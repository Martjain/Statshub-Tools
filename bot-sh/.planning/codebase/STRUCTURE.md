# Codebase Structure

**Analysis Date:** 2026-02-08

## Directory Layout

```
bot-sh/
├── bot_sh/                    # Core scraping package
│   ├── __init__.py            # Empty package init
│   ├── cli.py                 # CLI orchestration (691 lines)
│   ├── models.py              # Data definitions and mappings (146 lines)
│   ├── outputs.py             # JSON/CSV serialization (56 lines)
│   └── scraper.py             # Playwright automation (525 lines)
├── tui/                       # Textual TUI package
│   ├── __init__.py            # Package exports (6 lines)
│   ├── app.py                 # Main Textual app (654 lines)
│   ├── constants.py           # CSS and stat choices (141 lines)
│   ├── helpers.py             # Formatting utilities (20 lines)
│   └── services.py            # Playwright service bridge (202 lines)
├── tests/                     # Unit tests
│   ├── test_cli_stats.py      # CLI argument parsing tests (29 lines)
│   ├── test_lineups.py        # Lineup position tests (36 lines)
│   └── test_outputs.py        # Output serialization tests (71 lines)
├── venv/                      # Python virtual environment
├── .planning/                 # Planning documentation
│   └── codebase/              # Architecture and structure docs
├── interactive.py             # Questionary-based CLI (552 lines)
├── tui.py                     # TUI launcher (8 lines)
├── batch_collector.py         # Batch processing script
├── batch_simple.py            # Simplified batch script
├── codegen.py                 # Code generation utilities
├── extract_team_names.py      # Team name extraction tool
└── INTERACTIVE_CLI_FLOW_SPEC.md  # Flow specification
```

## Directory Purposes

**`bot_sh/`:**
- Purpose: Core scraping and data processing package
- Contains: All business logic for StatsHub automation
- Key files: `cli.py` (orchestration), `scraper.py` (automation), `models.py` (data)

**`tui/`:**
- Purpose: Textual TUI implementation
- Contains: GUI components, styling, service wrappers
- Key files: `app.py` (main UI), `services.py` (bridge to core)

**`tests/`:**
- Purpose: Unit tests
- Contains: Test modules for core functionality
- Key files: `test_lineups.py`, `test_outputs.py`, `test_cli_stats.py`

## Key File Locations

**Entry Points:**
- `tui.py`: Launcher for Textual TUI (imports from `tui.app`)
- `interactive.py`: Full-featured CLI with interactive prompts
- `bot_sh/cli.py`: Core CLI functions callable by other modules

**Configuration:**
- `.interactive_prefs.json`: User preference storage (JSON)
- `INTERACTIVE_CLI_FLOW_SPEC.md`: Documentation of CLI flow

**Core Logic:**
- `bot_sh/scraper.py`: Playwright page interaction and data extraction
- `bot_sh/cli.py`: High-level workflow orchestration
- `bot_sh/models.py`: Data structures and stat mappings

**Testing:**
- `tests/test_lineups.py`: Validates lineup position mappings
- `tests/test_outputs.py`: Validates JSON/CSV output
- `tests/test_cli_stats.py`: Validates stat argument parsing

## Naming Conventions

**Files:**
- Module names use snake_case: `scraper.py`, `cli.py`, `models.py`
- Test files prefixed with `test_`: `test_lineups.py`
- Package directories use lowercase: `bot_sh/`, `tui/`

**Functions:**
- Private functions prefixed with underscore: `_vprint()`, `_safe_click()`
- Action functions use verb prefix: `navigate_to_match()`, `collect_stats_for_all_positions()`
- Boolean checks use `is_`/`has_` prefix: `_is_checked()`, `has_confirmed_lineups`

**Variables:**
- Constants use UPPER_CASE: `STAT_CHOICES`, `DEFAULT_STATS`, `POSITIONS`
- Internal mappings use descriptive keys: `CLI_STAT_MAPPING`, `STAT_DISPLAY_NAMES`

**Classes:**
- TUI classes use descriptive names: `StatsHubTUI`
- Helper classes prefixed with underscore: `_Spinner`
- Dataclasses use CamelCase: `MatchEntry`

## Where to Add New Code

**New Stat Type:**
- Add to `bot_sh/models.py`:
  - Update `STAT_DISPLAY_NAMES` mapping
  - Add CLI key mapping to `CLI_STAT_MAPPING`
- Add to `tui/constants.py`:
  - Add to `STAT_CHOICES` list

**New UI Component:**
- Textual widgets: `tui/app.py` in `compose()` method
- Event handlers: `tui/app.py` with `on_*` prefix methods
- Styling: `tui/constants.py` in `TUI_CSS`

**New Scraper Functionality:**
- Page navigation: `bot_sh/scraper.py`
- Add helper methods for new UI interactions
- Update `extract_position_stats()` if data format changes

**New Output Format:**
- Formatter: `bot_sh/outputs.py` in `save_results()`
- Alternative path derivation: `derive_alt_output_path()`

**New Test:**
- Add to appropriate `tests/test_*.py` file
- Use existing test classes as templates

## Special Directories

**`__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes (by Python interpreter)
- Committed: No (should be in .gitignore)

**`venv/`:**
- Purpose: Python virtual environment
- Generated: Yes (by `python -m venv`)
- Committed: No (should be in .gitignore)

**`.planning/`:**
- Purpose: Architecture documentation and planning artifacts
- Generated: No (maintained manually)
- Committed: Yes (part of project documentation)

---

*Structure analysis: 2026-02-08*
