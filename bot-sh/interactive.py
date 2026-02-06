"""Interactive CLI for StatsHub automation."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import questionary

from bot_sh import cli
from bot_sh.models import CLI_STAT_MAPPING
from playwright.sync_api import sync_playwright


PREFS_PATH = Path(__file__).with_name(".interactive_prefs.json")
PREFERRED_STAT_KEYS = [
    "tackles",
    "fouls-won",
    "fouls-committed",
    "shots",
    "shots-on-target",
]
PREFERRED_STAT_TO_INTERNAL = {
    key: CLI_STAT_MAPPING[key] for key in PREFERRED_STAT_KEYS if key in CLI_STAT_MAPPING
}


def _load_prefs(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_prefs(path: Path, prefs: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _choose_stats(defaults: list[str] | None) -> list[str] | None:
    options = [
        ("Tackles", "tackles"),
        ("Fouls Won", "fouls-won"),
        ("Fouls Committed", "fouls-committed"),
        ("Shots", "shots"),
        ("Shots on Target", "shots-on-target"),
    ]
    if not defaults:
        defaults = None
    selected = questionary.checkbox(
        "Select stats to collect (space to toggle):",
        choices=[questionary.Choice(title=title, value=value) for title, value in options],
        default=defaults,
    ).ask()
    if not selected:
        return None
    stats = []
    for value in selected:
        if value in CLI_STAT_MAPPING:
            stats.append(CLI_STAT_MAPPING[value])
    return stats or None


def _choose_output_single(default_choice: str, default_path: str) -> tuple[str | None, bool]:
    choice = questionary.select(
        "Output format:",
        choices=[
            questionary.Choice("Terminal only", "terminal"),
            questionary.Choice("JSON file", "json"),
            questionary.Choice("CSV file", "csv"),
            questionary.Choice("Both JSON and CSV", "both"),
        ],
        default=default_choice,
    ).ask()
    if choice == "terminal":
        return None, False
    if choice == "both":
        return None, True
    path = questionary.text(
        f"Output file path ({choice}):", default=default_path or f"out.{choice}"
    ).ask()
    return path, False


def _discover_matches(date_filter: str, headless: bool) -> list[dict]:
    matches: list[dict] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto("https://www.statshub.com/")
            page.wait_for_load_state("networkidle")
            label = date_filter.capitalize()
            page.get_by_text(label, exact=True).click()
            page.wait_for_load_state("networkidle")

            links = page.locator('a[href*="/fixture/"]').all()
            seen = set()
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if not href or href in seen:
                        continue
                    seen.add(href)
                    match_pattern = r"/fixture/([^/]+)/(\d+)"
                    m = re.search(match_pattern, href)
                    if not m:
                        continue
                    slug = m.group(1)
                    parts = slug.split("-vs-")
                    if len(parts) != 2:
                        continue
                    home_slug, away_slug = parts
                    home = " ".join(w.capitalize() for w in home_slug.split("-"))
                    away = " ".join(w.capitalize() for w in away_slug.split("-"))
                    try:
                        text = link.inner_text() or ""
                    except Exception:
                        text = ""
                    time_match = re.search(r"\b(\d{1,2}:\d{2})\b", text)
                    kickoff = time_match.group(1) if time_match else ""
                    matches.append(
                        {
                            "match_url": href,
                            "home_name": home,
                            "away_name": away,
                            "match_id": m.group(2),
                            "kickoff_time": kickoff,
                        }
                    )
                except Exception:
                    continue
        finally:
            context.close()
            browser.close()
    return matches


def _extract_tabs(match_url: str, headless: bool) -> tuple[str, str]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        try:
            if not match_url.startswith("http"):
                match_url = "https://www.statshub.com" + match_url
            page.goto(match_url)
            page.wait_for_load_state("networkidle")
            page.get_by_role("button", name="Opponent Stats NEW!").click()
            page.wait_for_load_state("networkidle")

            tabs = page.locator('[role="tab"]').all()
            tab_names = []
            for tab in tabs:
                try:
                    text = tab.inner_text().strip()
                    if text:
                        tab_names.append(text)
                except Exception:
                    continue
            if len(tab_names) < 2:
                raise RuntimeError("Could not detect team tabs.")
            return tab_names[0], tab_names[1]
        finally:
            context.close()
            browser.close()


def _sort_matches(matches: list[dict], sort_mode: str) -> list[dict]:
    if sort_mode == "alpha":
        return sorted(
            matches,
            key=lambda m: f"{m.get('home_name','')} vs {m.get('away_name','')}",
        )
    if sort_mode == "time":
        def _time_key(m: dict):
            t = m.get("kickoff_time") or ""
            if not t:
                return (99, 99, f"{m.get('home_name','')} vs {m.get('away_name','')}")
            try:
                hour, minute = t.split(":")
                return (int(hour), int(minute), f"{m.get('home_name','')} vs {m.get('away_name','')}")
            except Exception:
                return (99, 99, f"{m.get('home_name','')} vs {m.get('away_name','')}")
        return sorted(matches, key=_time_key)
    return matches


def _filter_matches(matches: list[dict], query: str) -> list[dict]:
    if not query:
        return matches
    q = query.strip().lower()
    filtered = []
    for m in matches:
        label = f"{m.get('home_name','')} {m.get('away_name','')}".lower()
        if q in label:
            filtered.append(m)
    return filtered


def _parse_args():
    parser = argparse.ArgumentParser(description="Interactive StatsHub CLI")
    parser.add_argument(
        "--non-interactive", action="store_true", help="Run without prompts."
    )
    parser.add_argument("--dry-run", action="store_true", help="Print selections and exit.")
    parser.add_argument("--date", choices=["today", "tomorrow"], default="today")
    parser.add_argument(
        "--stats",
        default="tackles,fouls-won,fouls-committed,shots,shots-on-target",
    )
    parser.add_argument("--min-average", type=float, default=1.0)
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument(
        "--output",
        choices=["terminal", "json", "csv", "both"],
        default="terminal",
    )
    parser.add_argument("--output-path", default="")
    parser.add_argument("--count", default="all", help="Batch count: all or N")
    parser.add_argument(
        "--sort",
        choices=["none", "alpha", "time"],
        default="none",
        help="Sort matches: none, alpha, or time",
    )
    parser.add_argument("--filter", default="", help="Filter matches by substring")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--prefs", default=str(PREFS_PATH), help="Preferences file path")
    return parser.parse_args()


def _parse_stats_arg(stats_arg: str) -> list[str] | None:
    requested = [s.strip().lower() for s in stats_arg.split(",") if s.strip()]
    stats = []
    for value in requested:
        if value in CLI_STAT_MAPPING:
            stats.append(CLI_STAT_MAPPING[value])
    return stats or None


def _internal_to_preferred_keys(stats: list[str] | None) -> list[str]:
    if not stats:
        return []
    keys = []
    for key, internal in PREFERRED_STAT_TO_INTERNAL.items():
        if internal in stats:
            keys.append(key)
    return keys


def main() -> None:
    args = _parse_args()
    if not sys.stdin.isatty() and not args.non_interactive:
        print("Interactive mode requires a TTY. Re-run with --non-interactive.")
        return

    questionary.print("StatsHub Interactive", style="bold")
    prefs_path = Path(args.prefs)
    prefs = _load_prefs(prefs_path)

    if args.non_interactive:
        date_choice = args.date
        stats = _parse_stats_arg(args.stats)
        min_average = args.min_average
        headless = args.headless
    else:
        date_choice = questionary.select(
            "Match date:",
            choices=[
                questionary.Choice("Today", "today"),
                questionary.Choice("Tomorrow", "tomorrow"),
            ],
            default=prefs.get("date", "today"),
        ).ask()

        stats = _choose_stats(prefs.get("stats"))
        min_average_raw = questionary.text(
            "Minimum average:", default=str(prefs.get("min_average", 1.0))
        ).ask()
        try:
            min_average = float(min_average_raw)
        except ValueError:
            min_average = 1.0

        headless = questionary.confirm(
            "Run headless?", default=bool(prefs.get("headless", True))
        ).ask()

    if args.non_interactive:
        output_choice = args.output
        output_both = output_choice == "both"
        if output_choice == "terminal":
            output = None
        else:
            default_name = f"out.{output_choice}"
            output = args.output_path or default_name
    else:
        output_default = prefs.get("output", "terminal")
        output_path_default = prefs.get("output_path", "")
        output, output_both = _choose_output_single(output_default, output_path_default)

    matches = _discover_matches(date_choice, headless=headless)
    if not matches:
        print("No matches found.")
        return

    if args.non_interactive:
        matches = _filter_matches(matches, args.filter)
        matches = _sort_matches(matches, args.sort)
        if not matches:
            print("No matches found after filtering.")
            return
        if args.count == "all":
            chosen_matches = matches
        else:
            try:
                n = max(1, int(args.count))
            except ValueError:
                n = 1
            chosen_matches = matches[:n]
    else:
        filter_query = questionary.text(
            "Filter matches by team name (optional):", default=prefs.get("filter", "")
        ).ask()
        matches = _filter_matches(matches, filter_query)
        if not matches:
            retry = questionary.confirm(
                "No matches found after filtering. Retry without filter?",
                default=True,
            ).ask()
            if retry:
                filter_query = ""
                matches = _filter_matches(matches, filter_query)
            else:
                print("No matches found after filtering.")
                return
        sort_choice = questionary.select(
            "Sort matches:",
            choices=[
                questionary.Choice("None (site order)", "none"),
                questionary.Choice("Alphabetical", "alpha"),
                questionary.Choice("Kickoff time", "time"),
            ],
            default=prefs.get("sort", "none"),
        ).ask()
        matches = _sort_matches(matches, sort_choice)

        selection = questionary.select(
            "How many matches to run?",
            choices=[
                questionary.Choice("All matches", "all"),
                questionary.Choice("Pick 1 match", "one"),
                questionary.Choice("Pick N matches", "n"),
            ],
            default=prefs.get("count_mode", "all"),
        ).ask()
        if selection == "all":
            chosen_matches = matches
        elif selection == "one":
            choices = []
            for m in matches:
                label = f"{m.get('home_name')} vs {m.get('away_name')}"
                choices.append(questionary.Choice(label, m))
            chosen_matches = [
                questionary.select(
                    "Select match:",
                    choices=choices,
                ).ask()
            ]
        else:
            n_raw = questionary.text(
                "How many matches?", default=str(prefs.get("count", 5))
            ).ask()
            try:
                n = max(1, int(n_raw))
            except ValueError:
                n = 5
            chosen_matches = matches[:n]

    if args.dry_run:
        print(
            {
                "mode": "user",
                "date": date_choice,
                "stats": stats,
                "min_average": min_average,
                "output": output,
                "output_both": output_both,
                "headless": headless,
                "matches": len(chosen_matches),
            }
        )
        return

    if not args.yes:
        preview = "\n".join(
            [f"- {m.get('home_name')} vs {m.get('away_name')}" for m in chosen_matches]
        )
        proceed = questionary.confirm(
            "Proceed with these matches?\n" + preview,
            default=True,
        ).ask()
        if not proceed:
            print("Cancelled.")
            return

    if not args.non_interactive:
        output_choice = (
            "both"
            if output_both
            else ("terminal" if output is None else (Path(output).suffix.lstrip(".") or "terminal"))
        )
        prefs_update = {
            "date": date_choice,
            "stats": _internal_to_preferred_keys(stats),
            "min_average": min_average,
            "headless": headless,
            "output": output_choice,
            "output_path": output or "",
            "filter": filter_query if "filter_query" in locals() else "",
            "sort": sort_choice if "sort_choice" in locals() else "none",
            "count_mode": selection if "selection" in locals() else "all",
            "count": n if "n" in locals() else 1,
        }
        _save_prefs(prefs_path, prefs_update)

    for i, match in enumerate(chosen_matches, 1):
        print(
            f"[{i}/{len(chosen_matches)}] {match.get('home_name')} vs {match.get('away_name')}"
        )
        match_url = match.get("match_url")
        home_team, away_team = _extract_tabs(match_url, headless=headless)
        out_path = output
        out_both = output_both
        if len(chosen_matches) > 1 and output:
            safe_name = f"{home_team} vs {away_team}".replace(" ", "_").lower()
            out_path = f"{Path(output).stem}_{safe_name}{Path(output).suffix}"
            out_both = False

        cli.run_single_by_url(
            match_url=match_url,
            home_team_tab=home_team,
            away_team_tab=away_team,
            min_average=min_average,
            debug=False,
            stats=stats,
            headless=headless,
            output=out_path,
            output_both=out_both,
            verbose=False,
        )
    return


if __name__ == "__main__":
    main()
