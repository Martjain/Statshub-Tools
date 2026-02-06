"""Simple batch processor - reads matches from a config file and processes each."""

import argparse
from bot_sh import cli


def process_batch(
    config_file: str,
    stats: list[str] | None = None,
    min_average: float = 1.0,
    headless: bool = False,
    debug: bool = False,
):
    """Process multiple matches from a config file."""
    cli.run_batch_from_config(
        config_file=config_file,
        stats=stats,
        min_average=min_average,
        headless=headless,
        debug=debug,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch processor for multiple matches")
    parser.add_argument(
        "--config",
        type=str,
        default="matches.json",
        help="Config file with matches (default: matches.json)",
    )
    parser.add_argument(
        "--stats",
        type=str,
        default="tackles,fouls-won",
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
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    args = parser.parse_args()

    stats_to_collect = cli.stats_from_args_lenient(args.stats)

    process_batch(
        config_file=args.config,
        stats=stats_to_collect,
        min_average=args.min_average,
        headless=args.headless,
        debug=args.debug,
    )
