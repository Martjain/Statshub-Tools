# StatsHub Automation Tool

A Python-based Playwright automation tool for collecting per-position opponent football statistics from StatsHub. Gathers Total, Average, and Highest values for multiple stats across all player positions.

## Features

- **Automated Data Collection**: Navigate StatsHub UI and extract stats programmatically
- **Opponent Stats Focus**: Collects opponent-team position stats for each selected team tab
- **Multi-Stat Support**: Collect multiple statistics (Tackles, Fouls, Shots, etc.) in a single run
- **Position-Level Granularity**: Toggle each position individually and extract position-specific stats
- **Flexible Filtering**: Filter results by minimum average value
- **Batch Processing**: Process multiple matches from a config file
- **Output Persistence**: Save results as JSON or CSV (or both)
- **Headless Mode**: Run without a visible browser
- **Date Selection**: Specify "today" or "tomorrow" for match selection
- **Debug Artifacts**: Optional HTML/PNG capture for troubleshooting

## Installation

1. **Clone or navigate to the project directory:**

   ```bash
   cd /home/martinesfer/Downloads/Workspace/automate_statshub/bot-sh
   ```

2. **Set up a Python virtual environment (optional but recommended):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install playwright questionary
   playwright install
   ```

Note: The `bot-sh/venv` directory is not tracked in git. If it goes missing, recreate it with the steps above.

## Project Structure

```
bot-sh/
├── codegen.py              # CLI wrapper (parses arguments and invokes bot_sh.cli)
├── interactive.py          # Rich interactive CLI
├── batch_collector.py      # Batch runner (team_tabs.json)
├── batch_simple.py         # Config-based batch runner (matches.json)
├── bot_sh/
│   ├── __init__.py         # Package init
│   ├── cli.py              # CLI parsing and orchestration
│   ├── scraper.py          # Playwright navigation and extraction
│   ├── outputs.py          # JSON/CSV writers and helpers
│   ├── models.py           # Constants and mappings
└── venv/                   # Virtual environment
```

## Usage

### Basic Example

Run with default settings (headless mode, all default stats, today's date):

```bash
python3 bot-sh/codegen.py --headless
```

### Interactive Mode (Rich UI)

```bash
python3 bot-sh/interactive.py
```

Note: Interactive prompts require a TTY. For CI or non-interactive environments:

```bash
python3 bot-sh/interactive.py --non-interactive --dry-run --count 5 --filter barcelona --sort alpha
```

Interactive options include filtering matches by team name, sorting (including kickoff time), and a confirmation summary before execution.

The interactive CLI also saves your last selections to `bot-sh/.interactive_prefs.json` and uses them as defaults next time.

During collection, the terminal shows a spinner instead of per-position logs, then prints a final summary. The summary is sorted by average (descending) for each stat.
The final team summaries are shown in opponent view: each team row reflects stats conceded to opponents (home and away tab data are mapped vice versa).

**Interactive CLI flow (prompts):**
- Match date: `Today` or `Tomorrow`
- Confirmed lineups: yes/no (if yes, enter lineup name for home and away; `GK` is auto-included)
- Stats to collect: multi-select
- Minimum average: numeric threshold
- Run headless: yes/no
- Output format: terminal/json/csv/both (+ optional path)
- Optional filter by team name
- Sort matches: site order, alphabetical, kickoff time
- How many matches: all, pick 1, or pick N (checkbox selection)
- When picking N, the CLI prints the match list and requires selecting exactly N matches
- Final confirmation with selected matches

**Confirmed lineup input format:**
- Enter the lineup as a single formation string (example: `4-2-3-1`).
- Do not enter positions manually in the prompt; only the lineup name is required.
- Supported lineup names:
  `3-4-3`, `3-4-1-2`, `3-4-2-1`, `3-5-2`, `3-1-4-2`, `3-5-1-1`,
  `4-3-3`, `4-1-4-1`, `4-2-2-2`, `4-4-2`, `4-2-3-1`, `4-3-2-1`,
  `4-1-3-2`, `5-3-2`, `5-4-1`.
- `GK` is automatically included for every lineup.

### Collect Specific Stats

Collect only "Tackles" and "Fouls Committed":

```bash
python3 bot-sh/codegen.py --headless --stats tackles,fouls-committed
```

**Available stats** (option values):

- `tackles` → "Tackles"
- `fouls-committed` → "Fouls Committed"
- `fouls-won` → "Fouls Won"
- `shots` → "Shots"
- `shots-on-target` → "Shots on Target"
- `goals` → "Goals"
- `assists` → "Assists"
- `scored-or-assisted` → "Scored or Assisted"
- `total-passes` → "Total Passes"
- `yellow-cards` → "Yellow Cards"
- `dispossessed` → "Dispossessed"

### Filter Results by Average

Only include positions where average ≥ 2.0:

```bash
python3 bot-sh/codegen.py --headless --min-average 2.0 --stats tackles
```

### Save Output

**Save as JSON:**

```bash
python3 bot-sh/codegen.py --headless --output results.json
```

**Save as CSV:**

```bash
python3 bot-sh/codegen.py --headless --output results.csv
```

**Save both JSON and CSV:**

```bash
python3 bot-sh/codegen.py --headless --output-both
```

(Creates `out.json` and `out.csv` by default, or derives alternate format from `--output` path)

### Select Match Date

**For tomorrow's matches:**

```bash
python3 bot-sh/codegen.py --headless --date tomorrow --all-stats
```

**For today's matches (default):**

```bash
python3 bot-sh/codegen.py --headless --date today --all-stats
```

### Use Different Matches

By default, the tool collects stats for **Deportivo Alavés vs Real Sociedad** at **14:00**. To use a different match:

```bash
python3 bot-sh/codegen.py --headless \
  --match "16:00 Barcelona" \
  --home-team "FC Barcelona Barcelona" \
  --away-team "Real Madrid Real Madrid" \
  --stats tackles --output match.json
```

**Parameters:**

- `--match`: The match link text (e.g., "14:00 Deportivo Alavés", "16:00 Barcelona")
- `--home-team`: First team tab name (e.g., "Deportivo Alavés Deportivo")
- `--away-team`: Second team tab name (e.g., "Real Sociedad Real Sociedad")

Note: output is opponent stats. Summary rows are mapped to opponent view (team A summary uses team B tab data, and vice versa).

### Collect All Stats

Run collection for all supported statistics:

```bash
python3 bot-sh/codegen.py --headless --all-stats --output all_stats.json
```

### Enable Debug Mode

Save HTML and PNG artifacts for inspection:

```bash
python3 bot-sh/codegen.py --headless --debug --stats tackles
```

Creates files like `debug_RB.html` and `debug_RB.png` for each position.

### Complete Example

```bash
python3 bot-sh/codegen.py \
  --headless \
  --date today \
  --all-stats \
  --min-average 1.5 \
  --output match_stats.json \
  --output-both
```

## Batch Processing Multiple Matches (Automated Discovery)

The interactive CLI discovers available matches directly from StatsHub for `today` or `tomorrow`, and extracts team tab labels automatically. No manual `team_tabs.json` is required for interactive runs.

```bash
python3 bot-sh/interactive.py
```

If you still prefer the static `team_tabs.json` flow for scheduled runs, you can generate it with:

```bash
python3 bot-sh/extract_team_names.py --date today
```

Then run:

```bash
python3 bot-sh/batch_collector.py --headless --stats tackles --output-dir batch_results/
```

## CLI Arguments

| Argument        | Type   | Default                       | Description                                                    |
| --------------- | ------ | ----------------------------- | -------------------------------------------------------------- |
| `--headless`    | Flag   | `False`                       | Run browser without UI                                         |
| `--debug`       | Flag   | `False`                       | Save debug HTML/PNG artifacts                                  |
| `--all-stats`   | Flag   | `False`                       | Collect all supported stats                                    |
| `--stats`       | String | `tackles,fouls-won,fouls-committed,shots,shots-on-target` | Comma-separated list of stats (e.g., `tackles,fouls-won`)      |
| `--min-average` | Float  | `1.0`                         | Filter positions by minimum average value                      |
| `--date`        | Choice | `today`                       | Match date (`today` or `tomorrow`)                             |
| `--match`       | String | `14:00 Deportivo Alavés`      | Match identifier (time and team name, e.g., `16:00 Barcelona`) |
| `--home-team`   | String | `Deportivo Alavés Deportivo`  | First team tab name                                            |
| `--away-team`   | String | `Real Sociedad Real Sociedad` | Second team tab name                                           |
| `--output`      | String | None                          | Output file path (`.json` or `.csv`)                           |
| `--output-both` | Flag   | `False`                       | Save both JSON and CSV formats                                 |

## Output Formats

### JSON Structure

```json
{
  "Deportivo Alavés": {
    "Tackles": [
      {
        "position": "RB",
        "total": "46",
        "average": "2.9",
        "highest": "5"
      },
      ...
    ],
    "Fouls Won": [...]
  },
  "Real Sociedad": {...}
}
```

### CSV Structure

```csv
team,stat,position,total,average,highest,no_data
Deportivo Alavés,Tackles,RB,46,2.9,5,False
Deportivo Alavés,Tackles,CB,18,1.3,3,False
Real Sociedad,Tackles,RB,26,2.0,4,False
...
```

## How It Works

1. **Navigation**: Opens StatsHub, clicks the date filter (Today/Tomorrow), and selects the target match
2. **Opponent Stats**: Clicks the "Opponent Stats" button to access team statistics
3. **Team & Stat Selection**: Selects team tab and stat dropdown for the first team (Deportivo Alavés)
4. **Position Iteration**: Opens position selector and toggles each position on/off sequentially
5. **Data Extraction**: For each position, waits for cards to load and extracts Total, Average, and Highest values
6. **Team Switching**: Repeats collection for opponent team (Real Sociedad)
7. **Multi-Stat Loop**: Repeats the above for each requested stat
8. **Output**: Prints summary and saves results if `--output` is specified

## Robustness Features

- **Retry Logic**: Falls back to `click(force=True)` if standard click fails
- **Viewport Handling**: Uses `scroll_into_view_if_needed()` before clicking elements
- **Wait States**: Waits for `networkidle` after navigation and position toggles
- **Fallback Selectors**: Tries option value first, then option label if selection fails
- **Timeout Handling**: Short timeouts (5s) for cards that may not load; graceful degradation

## Troubleshooting

### Match Not Found

- Verify the match date exists on StatsHub
- Try with `--date today` if `--date tomorrow` fails
- The tool looks for "14:00 Deportivo Alavés" match; adjust manually if needed

### "No data found" in Output

- Some positions may not have stats for the selected match/stat
- These are marked with `"no_data": true` in JSON output
- Filtered out from console summary if `--min-average` is set

### Selector Not Found

- Enable `--debug` to capture HTML/PNG for inspection
- Check if StatsHub UI has changed (selectors may need updates)
- Review captured HTML files to locate alternate selectors

## Performance Notes

- Single stat collection: ~2–3 minutes (depends on position count and network)
- All-stats collection: ~10–15 minutes for both teams
- Headless mode is significantly faster than UI mode
- Network stability affects performance; retries are automatic

## Known Limitations

- Match selection requires exact match identifier text from StatsHub (time and team name)
- Team tab names vary by match; inspect the UI to find exact tab labels
- Position selectors and stat options are tied to current StatsHub structure
- "Tomorrow" availability depends on StatsHub content
- Currently processes only two teams per match (customize in code if needed)

## Future Enhancements

- Configuration validation for inputs
- Add richer retry/backoff and structured logging
- Support for scheduling and CI/CD integration

## License

This project is provided as-is for personal use.
