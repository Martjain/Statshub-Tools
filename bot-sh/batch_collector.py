"""Batch match collector - processes all matches listed in team_tabs.json."""

import argparse
from bot_sh import cli


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch collector for all matches on a date"
    )
    parser.add_argument(
        "--date",
        type=str,
        choices=["today", "tomorrow"],
        default="today",
        help="Match date (default: today)",
    )
    parser.add_argument(
        "--stats",
        type=str,
        default="tackles,fouls-won,fouls-committed,shots,shots-on-target",
        help="Comma-separated stats",
    )
    parser.add_argument(
        "--min-average",
        type=float,
        default=1.0,
        help="Minimum average filter",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run headless",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save individual match results",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    args = parser.parse_args()

    stats_to_collect = cli.stats_from_args_lenient(args.stats)

    cli.run_batch_from_team_tabs(
        team_tabs_path="team_tabs.json",
        stats=stats_to_collect,
        min_average=args.min_average,
        headless=args.headless,
        output_dir=args.output_dir,
        debug=args.debug,
    )
