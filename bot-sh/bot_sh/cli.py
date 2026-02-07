import argparse
import json
import os
from typing import Any

from . import scraper
from .models import (
    CLI_STAT_MAPPING,
    DEFAULT_AWAY_TEAM,
    DEFAULT_HOME_TEAM,
    DEFAULT_MATCH_NAME,
    DEFAULT_STATS,
    STAT_DISPLAY_NAMES,
)
from .outputs import derive_alt_output_path, save_results

ANSI_RESET = "\033[0m"
ANSI_GREEN = "\033[32m"
ANSI_RED = "\033[31m"


def parse_args(argv: list[str] | None = None):
    p = argparse.ArgumentParser(description="StatsHub position stats collector")
    p.add_argument(
        "--min-average",
        dest="min_average",
        type=float,
        default=1.0,
        help="Minimum average value to include in the summary (default: 1.0)",
    )
    p.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        help="Enable debug mode: save HTML/PNG artifacts when extraction fails",
    )
    p.add_argument(
        "--headless",
        dest="headless",
        action="store_true",
        help="Run browser in headless mode (no UI).",
    )
    p.add_argument(
        "--stats",
        dest="stats",
        type=str,
        default="tackles,fouls-won,fouls-committed,shots,shots-on-target",
        help="Comma-separated list of stats to collect. Options: tackles, fouls-won, fouls-committed, shots, shots-on-target (default: all)",
    )
    p.add_argument(
        "--all-stats",
        dest="all_stats",
        action="store_true",
        help="Collect all available stats (ignore --stats value).",
    )
    p.add_argument(
        "--date",
        dest="date",
        type=str,
        choices=["today", "tomorrow"],
        default="today",
        help="Which matches to collect: 'today' or 'tomorrow' (default: today)",
    )
    p.add_argument(
        "--output",
        dest="output",
        type=str,
        default=None,
        help="Path to write results (JSON or CSV). If omitted, no file is written.",
    )
    p.add_argument(
        "--output-both",
        dest="output_both",
        action="store_true",
        help="Also write the alternate format (write both JSON and CSV).",
    )
    p.add_argument(
        "--match",
        dest="match",
        type=str,
        default=DEFAULT_MATCH_NAME,
        help=f"Match time and team name to select (e.g., '14:00 Deportivo Alavés'). Default: '{DEFAULT_MATCH_NAME}'",
    )
    p.add_argument(
        "--home-team",
        dest="home_team",
        type=str,
        default=DEFAULT_HOME_TEAM,
        help=f"Home team tab name (e.g., '{DEFAULT_HOME_TEAM}'). Default: '{DEFAULT_HOME_TEAM}'",
    )
    p.add_argument(
        "--away-team",
        dest="away_team",
        type=str,
        default=DEFAULT_AWAY_TEAM,
        help=f"Away team tab name (e.g., '{DEFAULT_AWAY_TEAM}'). Default: '{DEFAULT_AWAY_TEAM}'",
    )
    return p.parse_args(argv)


def _parse_stats(stats_value: str) -> list[str]:
    return [s.strip().lower() for s in stats_value.split(",") if s.strip()]


def stats_from_args_strict(stats_value: str, all_stats: bool) -> list[str] | None:
    if all_stats:
        return None
    requested_stats = _parse_stats(stats_value)
    if "all" in requested_stats:
        return None

    stats_to_collect = []
    for stat_name in requested_stats:
        if stat_name in CLI_STAT_MAPPING:
            stats_to_collect.append(CLI_STAT_MAPPING[stat_name])
        else:
            print(
                "⚠️ Unknown stat: '{}'.".format(stat_name)
                + " Valid options: tackles, fouls-won, fouls-committed, shots, shots-on-target"
            )

    if not stats_to_collect:
        print("❌ No valid stats specified. Use --all-stats or provide valid --stats.")
        raise SystemExit(1)
    return stats_to_collect


def stats_from_args_lenient(stats_value: str) -> list[str] | None:
    requested_stats = _parse_stats(stats_value)
    stats_to_collect = []
    for stat_name in requested_stats:
        if stat_name in CLI_STAT_MAPPING:
            stats_to_collect.append(CLI_STAT_MAPPING[stat_name])
    return stats_to_collect if stats_to_collect else None


def _stat_display_name(stat_type: str) -> str:
    return STAT_DISPLAY_NAMES.get(stat_type, stat_type)


def _swap_to_opponent_team_view(
    all_collected_data: dict,
    home_team_display: str,
    away_team_display: str,
) -> dict:
    if home_team_display not in all_collected_data or away_team_display not in all_collected_data:
        return all_collected_data
    return {
        home_team_display: all_collected_data.get(away_team_display, {}),
        away_team_display: all_collected_data.get(home_team_display, {}),
    }


def run_single(
    min_average: float = 1.0,
    debug: bool = False,
    stats: list | None = None,
    headless: bool = False,
    output: str | None = None,
    output_both: bool = False,
    date_filter: str = "today",
    match_name: str = DEFAULT_MATCH_NAME,
    home_team_name: str = DEFAULT_HOME_TEAM,
    away_team_name: str = DEFAULT_AWAY_TEAM,
    verbose: bool = True,
) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        if verbose:
            print("🚀 Starting StatsHub Flow Replication...\n")

        if stats is None:
            stats = DEFAULT_STATS

        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        all_collected_data = {}

        try:
            scraper.navigate_to_match(
                page,
                date_filter=date_filter,
                match_name=match_name,
                verbose=verbose,
            )

            for stat_type in stats:
                stat_display = _stat_display_name(stat_type)

                if verbose:
                    print(f"\n{'='*60}")
                    print(f"📊 Collecting {stat_display} stats")
                    print(f"{'='*60}\n")

                scraper.select_team_and_stat(
                    page,
                    home_team_name,
                    stat_type,
                    stat_display,
                    verbose=verbose,
                )

                home_team_display = home_team_name.replace(" Deportivo", "").replace(
                    " Real Sociedad", ""
                )
                away_team_display = away_team_name.replace(" Deportivo", "").replace(
                    " Real Sociedad", ""
                )
                if verbose:
                    print(
                        f"📏  Collecting {stat_display} for {home_team_display}...\n"
                    )
                if home_team_display not in all_collected_data:
                    all_collected_data[home_team_display] = {}
                all_collected_data[home_team_display][stat_display] = (
                    scraper.collect_stats_for_all_positions(
                        page,
                        home_team_display,
                        stat_type,
                        debug=debug,
                        show_spinner=not debug,
                        verbose=verbose,
                    )
                )

                if verbose:
                    print(f"\n📍 Step 9: Switching to opponent team...")
                page.get_by_role("tab", name=away_team_name).click()
                page.wait_for_load_state("networkidle")
                try:
                    page.get_by_label("Stat").wait_for(timeout=5000)
                except Exception:
                    page.wait_for_timeout(1000)

                if verbose:
                    print(
                        f"📍 Step 10: Selecting stat {stat_display} for opponent team..."
                    )
                page.get_by_label("Stat").select_option(stat_type)

                if verbose:
                    print(
                        f"\n🏟️  Collecting {stat_display} for {away_team_display}...\n"
                    )
                if away_team_display not in all_collected_data:
                    all_collected_data[away_team_display] = {}
                all_collected_data[away_team_display][stat_display] = (
                    scraper.collect_stats_for_all_positions(
                        page,
                        away_team_display,
                        stat_type,
                        debug=debug,
                        show_spinner=not debug,
                        verbose=verbose,
                    )
                )

                if stat_type != stats[-1]:
                    if verbose:
                        print(
                            f"\n📍 Switching back to {home_team_display} for next stat..."
                        )
                    page.get_by_role("tab", name=home_team_name).click()
                    page.wait_for_load_state("networkidle")
                    try:
                        page.get_by_label("Stat").wait_for(timeout=5000)
                    except Exception:
                        page.wait_for_timeout(1000)

            all_collected_data = _swap_to_opponent_team_view(
                all_collected_data,
                home_team_display,
                away_team_display,
            )
            _print_summary(all_collected_data, min_average)

            if verbose:
                print("\n✅ Flow replication completed successfully!")

            if output or output_both:
                if not output and output_both:
                    save_results(all_collected_data, "out.json")
                    save_results(all_collected_data, "out.csv")
                else:
                    if output:
                        save_results(all_collected_data, output)
                    if output_both:
                        alt = derive_alt_output_path(output)
                        save_results(all_collected_data, alt)

        except Exception as e:
            print(f"\n❌ Error during flow execution: {str(e)}")
            raise

        finally:
            context.close()
            browser.close()


def run_single_by_url(
    match_url: str,
    home_team_tab: str,
    away_team_tab: str,
    min_average: float = 1.0,
    debug: bool = False,
    stats: list | None = None,
    headless: bool = False,
    output: str | None = None,
    output_both: bool = False,
    home_lineup_positions: list[str] | None = None,
    away_lineup_positions: list[str] | None = None,
    verbose: bool = True,
) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        if verbose:
            print("🚀 Starting StatsHub Flow Replication...\n")

        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        try:
            all_collected_data = _collect_match_stats(
                page,
                match_url=match_url,
                home_team_tab=home_team_tab,
                away_team_tab=away_team_tab,
                stats=stats,
                min_average=min_average,
                debug=debug,
                verbose=verbose,
            )

            if not all_collected_data:
                print("❌ No data collected.")
                return

            home_team_display = home_team_tab.title()
            away_team_display = away_team_tab.title()
            all_collected_data = _swap_to_opponent_team_view(
                all_collected_data,
                home_team_display,
                away_team_display,
            )
            summary_filters = None
            if home_lineup_positions or away_lineup_positions:
                summary_filters = {
                    home_team_display: set(away_lineup_positions or []),
                    away_team_display: set(home_lineup_positions or []),
                }
            _print_summary(
                all_collected_data,
                min_average,
                allowed_positions_by_team=summary_filters,
                colorize_threshold=bool(summary_filters),
            )
            if verbose:
                print("\n✅ Flow replication completed successfully!")

            if output or output_both:
                if not output and output_both:
                    save_results(all_collected_data, "out.json")
                    save_results(all_collected_data, "out.csv")
                else:
                    if output:
                        save_results(all_collected_data, output)
                    if output_both:
                        alt = derive_alt_output_path(output)
                        save_results(all_collected_data, alt)

        finally:
            context.close()
            browser.close()


def run_batch_from_team_tabs(
    team_tabs_path: str = "team_tabs.json",
    stats: list | None = None,
    min_average: float = 1.0,
    headless: bool = False,
    output_dir: str | None = None,
    debug: bool = False,
) -> None:
    from playwright.sync_api import sync_playwright

    if not os.path.exists(team_tabs_path):
        raise FileNotFoundError(
            f"Missing {team_tabs_path}. Generate it with bot-sh/extract_team_names.py."
        )

    with open(team_tabs_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    matches = data.get("matches", [])

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        try:
            all_results = {}
            success_count = 0

            for i, match in enumerate(matches, 1):
                home = match.get("home_team_tab")
                away = match.get("away_team_tab")
                match_url = match.get("match_url")

                print(f"\n[{i}/{len(matches)}] Processing: {home} vs {away}")
                print("-" * 80)

                match_key = f"{home} vs {away}"
                output_file = None
                if output_dir:
                    output_file = f"{output_dir}/{match_key.replace(' ', '_').lower()}.json"

                try:
                    result = _collect_match_stats(
                        page,
                        match_url=match_url,
                        home_team_tab=home,
                        away_team_tab=away,
                        stats=stats,
                        min_average=min_average,
                        debug=debug,
                    )

                    if result:
                        if output_file:
                            save_results(result, output_file)
                        all_results[match_key] = "✅ Success"
                        success_count += 1
                    else:
                        all_results[match_key] = "❌ No data collected"

                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    all_results[match_key] = f"❌ {str(e)[:50]}"

            print("\n" + "=" * 80)
            print("📋 BATCH SUMMARY")
            print("=" * 80)
            for match, status in all_results.items():
                print(f"  {match}: {status}")
            print(f"\n✅ Successfully processed: {success_count}/{len(matches)}")

        finally:
            context.close()
            browser.close()


def _collect_match_stats(
    page,
    match_url: str,
    home_team_tab: str,
    away_team_tab: str,
    stats: list | None,
    min_average: float,
    debug: bool,
    verbose: bool,
):
    if stats is None:
        stats = DEFAULT_STATS

    all_collected_data = {}

    scraper.navigate_to_match_by_url(page, match_url, verbose=verbose)
    home_team_display = home_team_tab.title()
    away_team_display = away_team_tab.title()

    for stat_type in stats:
        stat_display = _stat_display_name(stat_type)

        if verbose:
            print(f"  📊 Collecting {stat_display}...")

        scraper.select_team_and_stat(
            page, home_team_tab, stat_type, stat_display, verbose=verbose
        )

        if home_team_display not in all_collected_data:
            all_collected_data[home_team_display] = {}
        all_collected_data[home_team_display][stat_display] = (
            scraper.collect_stats_for_all_positions(
                page,
                home_team_display,
                stat_type,
                debug=debug,
                show_spinner=not debug,
                verbose=verbose,
            )
        )

        if verbose:
            print(f"  ✓ Collected for {home_team_display}")

        page.get_by_role("tab", name=away_team_tab).click()
        page.wait_for_load_state("networkidle")
        try:
            page.get_by_label("Stat").wait_for(timeout=5000)
        except Exception:
            page.wait_for_timeout(1000)

        page.get_by_label("Stat").select_option(stat_type)

        if away_team_display not in all_collected_data:
            all_collected_data[away_team_display] = {}
        all_collected_data[away_team_display][stat_display] = (
            scraper.collect_stats_for_all_positions(
                page,
                away_team_display,
                stat_type,
                debug=debug,
                show_spinner=not debug,
                verbose=verbose,
            )
        )

        if verbose:
            print(f"  ✓ Collected for {away_team_display}")

        if stat_type != stats[-1]:
            page.get_by_role("tab", name=home_team_tab).click()
            page.wait_for_load_state("networkidle")
            try:
                page.get_by_label("Stat").wait_for(timeout=5000)
            except Exception:
                page.wait_for_timeout(1000)

    return all_collected_data


def _to_float_or_zero(value: Any) -> float:
    try:
        if value is None or value == "":
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def _print_summary(
    all_collected_data: dict,
    min_average: float,
    allowed_positions_by_team: dict[str, set[str]] | None = None,
    colorize_threshold: bool = False,
) -> None:
    print("\n" + "=" * 80)
    if colorize_threshold:
        print(
            "📊 COLLECTED STATS SUMMARY (confirmed lineups only; min-average color threshold = {})".format(
                min_average
            )
        )
    else:
        print(
            "📊 COLLECTED STATS SUMMARY (filtered by min-average >= {})".format(
                min_average
            )
        )
    print("=" * 80)
    for team, stats_dict in all_collected_data.items():
        print(f"\n🏟️  {team}:")
        allowed_positions = None
        if allowed_positions_by_team:
            allowed_positions = allowed_positions_by_team.get(team)
        for stat_name, stat_positions in stats_dict.items():
            print(f"\n   📈 {stat_name}:")
            filtered = []
            for pos in stat_positions:
                position_name = pos.get("position", "")
                if allowed_positions is not None and position_name not in allowed_positions:
                    continue

                total_val = _to_float_or_zero(pos.get("total"))
                avg_val = _to_float_or_zero(pos.get("average"))
                high_val = _to_float_or_zero(pos.get("highest"))
                normalized = {
                    "position": position_name,
                    "total": total_val,
                    "average": avg_val,
                    "highest": high_val,
                }
                if colorize_threshold:
                    filtered.append(normalized)
                elif avg_val >= float(min_average):
                    filtered.append(normalized)

            filtered.sort(
                key=lambda p: p.get("average", 0.0),
                reverse=True,
            )

            if not filtered:
                if colorize_threshold and allowed_positions is not None:
                    print("   No positions from confirmed lineup.")
                else:
                    print(f"   No positions with average >= {min_average}.")
                continue

            print(
                f"   {'Position':<12} {'Total':<15} {'Average':<10} {'Highest':<10}"
            )
            print("   " + "-" * 50)
            for pos in filtered:
                total_display = (
                    str(int(pos["total"])) if pos["total"].is_integer() else f"{pos['total']:.2f}"
                )
                avg_display = (
                    str(int(pos["average"]))
                    if pos["average"].is_integer()
                    else f"{pos['average']:.2f}"
                )
                high_display = (
                    str(int(pos["highest"]))
                    if pos["highest"].is_integer()
                    else f"{pos['highest']:.2f}"
                )

                if colorize_threshold:
                    color = (
                        ANSI_GREEN
                        if pos["average"] >= float(min_average)
                        else ANSI_RED
                    )
                    avg_cell = f"{color}{avg_display:<10}{ANSI_RESET}"
                else:
                    avg_cell = f"{avg_display:<10}"
                print(
                    f"   {pos['position']:<12} {total_display:<15} {avg_cell} {high_display:<10}"
                )


def run_batch_from_config(
    config_file: str,
    stats: list | None = None,
    min_average: float = 1.0,
    headless: bool = False,
    debug: bool = False,
) -> None:
    with open(config_file, "r") as f:
        config = json.load(f)

    matches = config.get("matches", [])
    print(f"\n📊 Processing {len(matches)} matches from {config_file}\n")

    results = {}
    for i, match in enumerate(matches, 1):
        match_key = f"{match['home_team']} vs {match['away_team']}"
        print(f"\n[{i}/{len(matches)}] {match_key}")
        print("-" * 80)

        try:
            output_file = (
                "results/"
                + match["home_team"].replace(" ", "_").lower()
                + "_vs_"
                + match["away_team"].replace(" ", "_").lower()
                + ".json"
            )

            run_single(
                min_average=min_average,
                debug=debug,
                stats=stats,
                headless=headless,
                output=output_file,
                output_both=False,
                date_filter="today",
                match_name=match.get("match_name", match["home_team"]),
                home_team_name=match["home_team"],
                away_team_name=match["away_team"],
            )
            results[match_key] = "✅ Success"
        except Exception as e:
            print(f"❌ Error: {e}")
            results[match_key] = f"❌ {str(e)[:50]}"

    print("\n" + "=" * 80)
    print("📋 BATCH SUMMARY")
    print("=" * 80)
    for match, status in results.items():
        print(f"  {match}: {status}")

    success_count = sum(1 for s in results.values() if "✅" in s)
    print(f"\n✅ Successfully processed: {success_count}/{len(matches)}")
