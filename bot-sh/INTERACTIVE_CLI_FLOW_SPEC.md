# Interactive CLI Flow Spec (Source of Truth)

This file defines the exact user flow implemented in `bot-sh/interactive.py`.
The TUI must mirror this flow and behavior.

## Scope

- Applies to interactive mode (`python3 bot-sh/interactive.py`).
- Non-interactive CLI flags are out of scope for TUI flow order.

## Required Prompt Order

1. Match date
- Prompt: `Today` or `Tomorrow`.

2. Confirmed lineups branch
- Prompt: `Do you have confirmed lineups?`
- If `No`: continue without lineup inputs.
- If `Yes`: ask lineup name for:
  - Home Team
  - Away Team
- Validate lineup names via `get_lineup_positions`.

3. Stats selection
- Multi-select stats from the supported list.
- Internal values must map through `CLI_STAT_MAPPING`.

4. Minimum average
- Prompt numeric value.
- Invalid numeric input falls back to `1.0`.

5. Headless mode
- Prompt: run headless yes/no.

6. Output mode
- Prompt: terminal/json/csv/both.
- If json/csv: ask output path.
- If terminal: no path prompt.

7. Discover matches for selected date
- Must use the same selectors/logic as CLI for date/filter link discovery.

8. Optional team-name filter
- Prompt for substring filter.
- If no matches after filter:
  - Ask retry without filter.
  - If user declines retry: stop.

9. Sort mode
- Prompt: none/alpha/time.

10. Match count mode
- Prompt: all / pick 1 / pick N.
- If `all`: use all visible matches.
- If `pick 1`: require exactly one selected match.
- If `pick N`:
  - Ask N.
  - Require exactly N selected matches.
  - Re-prompt until exact count is selected.

11. Confirmation
- Show selected matches summary.
- Ask proceed yes/no.
- If `No`: cancel.

12. Run collection
- For each selected match:
  - Extract tabs.
  - Run collector.
  - Handle per-match output naming when multiple matches are selected.

## Flow Rules for TUI

- Right pane must be stage-based, not mixed:
  - Stage 1: Selection
  - Stage 2: Preview/Confirmation
  - Stage 3: Results
- Stage transitions:
  - After discovery/filter/sort: show Selection.
  - After valid match selection: show Preview.
  - After run starts/completes: show Results.
- Lineup branch must be first and explicit.
- If lineup mode is off, lineup fields must be hidden/disabled and values cleared.
- If lineup mode is on, both lineup inputs are required and validated.

## Acceptance Criteria

- TUI and CLI produce the same selected-match set for equivalent user choices.
- `today` and `tomorrow` discovery use equivalent selectors and retry behavior.
- Count mode constraints are enforced identically:
  - one => exactly 1
  - n => exactly N
  - all => all visible unless user manually selects a subset (TUI override behavior must be explicit in UI).
- User can always see what will run before execution.

## Maintenance Rule

If `interactive.py` flow changes, update this file in the same change.
