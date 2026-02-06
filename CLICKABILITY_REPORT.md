# Match Clickability Report - February 4, 2026 (Today)

## Summary

- **Total Matches Found:** 23
- **Accessible via direct URL navigation:** 23 (100%)

## Notes

All matches on the `Today` list are accessible when navigating directly to each match's `/fixture/...` URL and opening the "Opponent Stats" section. A helper script extracted the UPPERCASE team tab labels and saved them to `team_tabs.json` for reliable batch processing.

File created: `team_tabs.json` — contains `match_url`, `match_id`, `home_team_tab`, and `away_team_tab` for all matches.

## How to Use with Batch Processor

1. Use the provided `team_tabs.json` (or generate it via `bot-sh/extract_team_names.py`) which includes `match_url` and exact UPPERCASE tab labels.

Example `team_tabs.json` entry:

```json
{
  "match_url": "/fixture/toulouse-vs-amiens-sc-ml83ym/15366329",
  "match_id": "15366329",
  "home_team_tab": "TOULOUSE",
  "away_team_tab": "AMIENS SC"
}
```

2. Run the batch collector (reads `team_tabs.json` automatically):

```bash
python3 bot-sh/batch_collector.py --headless --stats tackles --output-dir batch_results/
```

This uses direct URL navigation and the exact UPPERCASE tab labels to avoid selector ambiguity.

## Recommendation

- Prefer `match_url` + UPPERCASE `home_team_tab` / `away_team_tab` for batch runs.
- If you need to regenerate `team_tabs.json`, run:

```bash
python3 bot-sh/extract_team_names.py
```

The extraction script visits each match URL and records the visible tab labels (UPPERCASE), producing `team_tabs.json`.
