# Technology Stack

**Analysis Date:** 2026-02-08

## Languages

**Primary:**
- Python 3.12.3 - Entire application codebase

**Secondary:**
- CSS - TUI styling in `tui/constants.py`

## Runtime

**Environment:**
- Python 3.12.3 (CPython)
- Virtual environment: `venv/` directory present

**Package Manager:**
- pip 24.0
- No lockfile (requirements.txt or poetry.lock not detected)

## Frameworks

**Core:**
- Playwright 1.58.0 - Browser automation for web scraping
  - Used in: `bot_sh/cli.py`, `bot_sh/scraper.py`, `interactive.py`, `tui/services.py`
  - Sync API pattern: `sync_playwright()`

**CLI/TUI Frameworks:**
- Textual 7.5.0 - Terminal User Interface (TUI) framework
  - Used in: `tui/app.py`, `tui/constants.py`
- Questionary 2.1.1 - Interactive CLI prompts
  - Used in: `interactive.py`
- Rich 14.3.2 - Terminal formatting and output
  - Used as dependency for Textual and direct imports in `tui/app.py`

**Testing:**
- unittest - Standard library testing framework
  - Test files: `tests/test_outputs.py`, `tests/test_lineups.py`, `tests/test_cli_stats.py`

**Build/Dev:**
- None detected (no build tools, bundlers, or transpilers)

## Key Dependencies

**Critical (Core Functionality):**
- playwright 1.58.0 - Web scraping and browser automation
  - Chromium browser automation
  - Network idle waiting, element selection, screenshot capture

**CLI/TUI Experience:**
- textual 7.5.0 - Rich TUI application framework
- questionary 2.1.1 - User-friendly interactive prompts
- rich 14.3.2 - Rich text and beautiful formatting

**Utilities:**
- typing_extensions 4.15.0 - Backport typing features
- platformdirs 4.5.1 - Platform-specific directory paths (Textual dependency)

**Notable Absent Dependencies:**
- No web framework (Flask, FastAPI, Django)
- No database ORM (SQLAlchemy, etc.)
- No HTTP client library (requests, httpx) - uses Playwright for HTTP
- No data processing (pandas, numpy)

## Configuration

**Environment:**
- No .env files detected
- Configuration stored in JSON files:
  - `.interactive_prefs.json` - User preferences for interactive mode
  - `team_tabs.json` - Match configuration for batch processing

**Build:**
- No build configuration detected
- Pure Python execution

**Package Configuration:**
- No pyproject.toml, setup.py, or setup.cfg
- No requirements.txt (dependencies managed in venv directly)

## Platform Requirements

**Development:**
- Python 3.12+
- Virtual environment recommended
- Playwright browsers must be installed (`playwright install chromium`)

**Production:**
- Local execution only (no server/deployment detected)
- Headless browser support available via `--headless` flag
- Output formats: JSON, CSV

## Execution Entry Points

**CLI:**
- `python -m bot_sh.cli` - Direct CLI execution
- `python bot_sh/cli.py` - Alternative execution

**Interactive:**
- `python interactive.py` - Interactive questionary-based flow

**TUI:**
- `python tui.py` - Textual TUI application
- `python -m tui.app` - Module execution

**Batch Processing:**
- `python batch_collector.py` - Batch match processing
- `python batch_simple.py` - Simplified batch execution

---

*Stack analysis: 2026-02-08*
