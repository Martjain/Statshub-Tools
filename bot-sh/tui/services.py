"""Playwright-backed services used by the Textual TUI."""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from bot_sh import cli
from bot_sh.models import CLI_STAT_MAPPING
from bot_sh.outputs import derive_alt_output_path
from playwright.sync_api import sync_playwright


def _save_results_silent(data: dict, output_path: str) -> None:
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix.lower() == ".csv":
        import csv

        with out_path.open("w", newline="", encoding="utf-8") as file_obj:
            writer = csv.writer(file_obj)
            writer.writerow(["team", "stat", "position", "total", "average", "highest", "no_data"])
            for team, stats_dict in data.items():
                for stat_name, positions in stats_dict.items():
                    for pos in positions:
                        writer.writerow(
                            [
                                team,
                                stat_name,
                                pos.get("position", ""),
                                pos.get("total", ""),
                                pos.get("average", ""),
                                pos.get("highest", ""),
                                bool(pos.get("no_data", False)),
                            ]
                        )
        return
    with out_path.open("w", encoding="utf-8") as file_obj:
        json.dump(data, file_obj, ensure_ascii=False, indent=2)


def discover_matches(date_filter: str, headless: bool) -> list[dict]:
    def _settle() -> None:
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            page.wait_for_load_state("domcontentloaded", timeout=8000)
            page.wait_for_timeout(1200)

    def _click_date(label: str) -> None:
        click_errors: list[str] = []
        candidates = [
            page.get_by_text(label, exact=True),
            page.get_by_role("button", name=label),
            page.get_by_role("tab", name=label),
        ]
        for locator in candidates:
            try:
                locator.first.click(timeout=3000)
                return
            except Exception as exc:
                click_errors.append(str(exc))
        raise RuntimeError(f"Could not click date filter '{label}'. Tried text/button/tab. Last error: {click_errors[-1] if click_errors else 'n/a'}")

    def _extract() -> list[dict]:
        found: list[dict] = []
        links = page.locator('a[href*="/fixture/"]').all()
        seen = set()
        for link in links:
            try:
                href = link.get_attribute("href")
                if not href or href in seen:
                    continue
                seen.add(href)
                match = re.search(r"/fixture/([^/]+)/(\d+)", href)
                if not match:
                    continue
                slug = match.group(1)
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
                found.append(
                    {
                        "match_url": href,
                        "home_name": home,
                        "away_name": away,
                        "kickoff_time": kickoff,
                    }
                )
            except Exception:
                continue
        return found

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto("https://www.statshub.com/")
            _settle()

            label = date_filter.capitalize()
            # Retry once because StatsHub occasionally ignores the first filter click.
            for attempt in range(2):
                _click_date(label)
                _settle()
                matches = _extract()
                if matches:
                    return matches
                if attempt == 0:
                    page.reload(wait_until="domcontentloaded")
                    _settle()
        finally:
            context.close()
            browser.close()

    return []


def extract_tabs(match_url: str, headless: bool) -> tuple[str, str]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        try:
            full_url = match_url if match_url.startswith("http") else "https://www.statshub.com" + match_url
            page.goto(full_url)
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                page.wait_for_timeout(1200)
            page.get_by_role("button", name="Opponent Stats NEW!").click()
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                page.wait_for_timeout(1200)
            tabs = [t.inner_text().strip() for t in page.locator('[role="tab"]').all()]
            tabs = [t for t in tabs if t]
            if len(tabs) < 2:
                raise RuntimeError("Could not detect team tabs for selected match.")
            return tabs[0], tabs[1]
        finally:
            context.close()
            browser.close()


def collect_data(
    match_url: str,
    stat_keys: list[str],
    min_average: float,
    has_lineups: bool,
    home_positions: list[str] | None,
    away_positions: list[str] | None,
    headless: bool,
    output_path: str | None = None,
    output_both: bool = False,
) -> dict:
    requested_output = output_path
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp_file:
        temp_output_path = tmp_file.name

    try:
        home_tab, away_tab = extract_tabs(match_url, headless=headless)
        internal_stats = [CLI_STAT_MAPPING[s] for s in stat_keys if s in CLI_STAT_MAPPING]
        cli.run_single_by_url(
            match_url=match_url,
            home_team_tab=home_tab,
            away_team_tab=away_tab,
            min_average=min_average,
            debug=False,
            stats=internal_stats,
            headless=headless,
            output=temp_output_path,
            output_both=False,
            home_lineup_positions=home_positions if has_lineups else None,
            away_lineup_positions=away_positions if has_lineups else None,
            verbose=False,
        )
        with open(temp_output_path, "r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)
        if requested_output:
            _save_results_silent(data, requested_output)
            if output_both:
                _save_results_silent(data, derive_alt_output_path(requested_output))
        return data
    finally:
        try:
            Path(temp_output_path).unlink(missing_ok=True)
        except Exception:
            pass
