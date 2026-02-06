"""CLI wrapper for the modular collector."""

from bot_sh import cli


if __name__ == "__main__":
    args = cli.parse_args()
    stats_to_collect = cli.stats_from_args_strict(args.stats, args.all_stats)

    cli.run_single(
        min_average=args.min_average,
        debug=args.debug,
        stats=stats_to_collect,
        headless=args.headless,
        output=args.output,
        output_both=args.output_both,
        date_filter=args.date,
        match_name=args.match,
        home_team_name=args.home_team,
        away_team_name=args.away_team,
    )
