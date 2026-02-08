# Architecture

**Analysis Date:** 2026-02-08

## Pattern Overview

**Overall:** Layered Architecture with Multiple UI Front-Ends

**Key Characteristics:**
- Three separate entry points: CLI (`interactive.py`), TUI (`tui.py`), and Textual GUI (`tui/app.py`)
- Core scraping logic isolated in `bot_sh/` package
- Playwright-based browser automation for web scraping
- Data transformation and output formatting separated from scraping logic

## Layers

**CLI Layer (User Interface):**
- Purpose: Interactive command-line interface using questionary library
- Location: `interactive.py`
- Contains: Argument parsing, user prompts, preference persistence, match discovery
- Depends on: `bot_sh.models`, `bot_sh.cli`
- Used by: End users via command line

**TUI Layer (Textual GUI):**
- Purpose: Rich terminal-based GUI using Textual framework
- Location: `tui/` package (`tui/app.py`)
- Contains: Widget definitions, event handlers, screen composition, flow state management
- Depends on: `bot_sh.models`, `tui.services`, `tui.helpers`, `textual` library
- Used by: End users via `tui.py` launcher

**Service Layer:**
- Purpose: Bridge between UI and core scraping logic
- Location: `tui/services.py`
- Contains: `discover_matches()`, `extract_tabs()`, `collect_data()`
- Depends on: `bot_sh.cli`, `bot_sh.models`, `playwright.sync_api`
- Used by: `tui.app.StatsHubTUI`

**Core Scraper Layer:**
- Purpose: Web scraping automation using Playwright
- Location: `bot_sh/scraper.py`
- Contains: Navigation functions, stat collection, position switching, spinner UI
- Depends on: `bot_sh.models.POSITIONS`
- Used by: `bot_sh.cli`, `tui.services`

**Models Layer:**
- Purpose: Data definitions and mappings
- Location: `bot_sh/models.py`
- Contains: Position definitions, lineup mappings, stat name mappings, `MatchEntry` dataclass
- Depends on: None (pure data)
- Used by: All other layers

**CLI Orchestration Layer:**
- Purpose: High-level orchestration of scraping workflows
- Location: `bot_sh/cli.py`
- Contains: `run_single()`, `run_single_by_url()`, `run_batch_from_team_tabs()`, `_collect_match_stats()`
- Depends on: `bot_sh.scraper`, `bot_sh.models`, `bot_sh.outputs`, `playwright.sync_api`
- Used by: `interactive.py`, `tui.services`

**Output Layer:**
- Purpose: Data serialization to JSON/CSV
- Location: `bot_sh/outputs.py`
- Contains: `save_results()`, `derive_alt_output_path()`
- Depends on: `csv`, `json`, `os`
- Used by: `bot_sh.cli`, `tui.services`

## Data Flow

**Single Match Collection Flow:**

1. User launches via `tui.py` or `interactive.py`
2. UI collects parameters (date, stats, min average, lineup mode, output settings)
3. `discover_matches()` fetches available matches from statshub.com
4. User selects match(es) from discovered list
5. `extract_tabs()` identifies home/away team names from match page
6. `collect_data()` orchestrates scraping per match:
   - For each stat type:
     - Navigate to team tab
     - Select stat from dropdown
     - For each position in `POSITIONS`:
       - Toggle position switch
       - Extract Total/Average/Highest values
       - Toggle switch off
7. Data is swapped to opponent view (`_swap_to_opponent_team_view`)
8. Summary displayed and saved to output file(s)

**Batch Processing Flow:**

1. Load match configuration from JSON file
2. Iterate through matches with shared browser context
3. Collect stats for each match
4. Output per-match files or aggregate results

## Key Abstractions

**StatsHubTUI (Textual App):**
- Purpose: Main application class for Textual GUI
- Location: `tui/app.py` lines 40-642
- Pattern: Event-driven reactive UI with state machine (`_flow_state`)

**MatchEntry:**
- Purpose: Immutable match specification
- Location: `bot_sh/models.py` lines 140-146
- Pattern: `frozen=True` dataclass

**CLI_STAT_MAPPING:**
- Purpose: Normalize stat names between CLI args and internal representation
- Location: `bot_sh/models.py` lines 114-132
- Pattern: Bidirectional mapping dictionary

**_Spinner:**
- Purpose: Threaded progress indicator during position collection
- Location: `bot_sh/scraper.py` lines 496-524
- Pattern: Background thread with event-based stop mechanism

## Entry Points

**TUI Launcher:**
- Location: `tui.py`
- Triggers: Command line `python tui.py [--headed]`
- Responsibilities: Import and run `tui.app.main()`

**Interactive CLI:**
- Location: `interactive.py`
- Triggers: Command line `python interactive.py [--non-interactive ...]`
- Responsibilities: Full interactive flow with questionary prompts or scripted execution

**StatsHubTUI (Textual App):**
- Location: `tui/app.py::main()`
- Triggers: Called by `tui.py`
- Responsibilities: Compose UI, handle events, orchestrate service calls

## Error Handling

**Strategy:** Graceful degradation with debug artifacts

**Patterns:**
- Try/catch blocks around Playwright operations with fallback timeouts
- Debug mode saves HTML/PNG artifacts on extraction failures (`save_debug_artifacts()`)
- Silent failures in TUI services (`_save_results_silent()`) to avoid interrupting flow
- Validation of user inputs (lineup names) with helpful error messages

**Error Flow in Scraper:**
```python
# From scraper.py extract_position_stats()
try:
    page.wait_for_load_state("networkidle", timeout=wait_timeout_ms)
except Exception:
    if debug:
        # Log timeout details
        pass
# Continue with extraction attempt even after timeout
```

## Cross-Cutting Concerns

**Logging:** Print statements with emoji prefixes for visual feedback; RichLog widget in TUI
**Validation:** Lineup position validation at module load time (`_validate_lineups()`)
**Authentication:** None (public website scraping)
**Configuration:** JSON preference file (`.interactive_prefs.json`)

---

*Architecture analysis: 2026-02-08*
