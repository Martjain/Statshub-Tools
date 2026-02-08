# Coding Conventions

**Analysis Date:** 2026-02-08

## Naming Patterns

**Files:**
- Module files: `snake_case.py` (e.g., `bot_sh/models.py`, `tui/app.py`)
- Test files: `test_*.py` pattern (e.g., `tests/test_lineups.py`)
- Entry point scripts: Descriptive names like `interactive.py`, `codegen.py`, `batch_collector.py`

**Functions:**
- Use `snake_case` for all function names
- Private functions use leading underscore: `_validate_lineups()`, `_vprint()`, `_safe_click()`
- Descriptive verb-based names: `parse_args()`, `collect_stats_for_all_positions()`, `save_results()`

**Variables:**
- `snake_case` for variables (e.g., `all_collected_data`, `min_average`, `home_team_display`)
- Constants use `UPPER_SNAKE_CASE`: `POSITIONS`, `DEFAULT_STATS`, `STAT_DISPLAY_NAMES`, `ANSI_RESET`
- Private module-level constants: `_validate_lineups()` function validates `LINEUP_POSITIONS`

**Types:**
- Classes use `PascalCase`: `MatchEntry`, `_Spinner`, `StatsHubTUI`
- Type annotations use Python 3.10+ union syntax: `str | None`, `list[str]`, `dict[str, set[str]] | None`

## Code Style

**Formatting:**
- 4-space indentation (no tabs)
- 88-100 character line length (observed in practice)
- No explicit formatter config (`.prettierrc`, `pyproject.toml`) detected
- Trailing commas in multi-line collections

**Type Hints:**
- **Mandatory** for function signatures throughout the codebase
- Use `from __future__ import annotations` in TUI modules for forward references
- Prefer `str | None` over `Optional[str]` (Python 3.10+ style)
- Use `list[str]` over `List[str]` (Python 3.9+ style)
- Complex return types: `tuple[str | None, bool]` in `tui/app.py`

**Example:**
```python
def stats_from_args_strict(stats_value: str, all_stats: bool) -> list[str] | None:
def _parse_stats(stats_value: str) -> list[str]:
def _to_float_or_zero(value: Any) -> float:
```

## Import Organization

**Order:**
1. **Standard library** (alphabetical): `argparse`, `csv`, `json`, `os`, `re`, `sys`, `threading`, `time`
2. **Third-party** (alphabetical): `playwright.sync_api`, `questionary`, `textual.*`
3. **Local imports** (relative within package):
   ```python
   from .models import CLI_STAT_MAPPING, STAT_DISPLAY_NAMES
   from .outputs import derive_alt_output_path, save_results
   ```

**Path Aliases:**
- No explicit path aliases configured
- Tests use `sys.path.insert(0, str(Path(__file__).resolve().parents[1]))` pattern for imports

**Example from `bot_sh/cli.py`:**
```python
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
```

## Error Handling

**Patterns:**
- Use try/except with specific exception handling
- Graceful degradation with fallback values
- Debug mode flag (`debug: bool = False`) for verbose error output

**Example from `scraper.py`:**
```python
try:
    page.wait_for_load_state("networkidle", timeout=wait_timeout_ms)
except Exception:
    if debug:
        elapsed = time.monotonic() - start_wait
        print(f"   ⚠️ networkidle timeout after {elapsed:.2f}s for {position}")
```

**Validation Pattern:**
```python
def _validate_lineups() -> None:
    allowed_lineup_positions = set(POSITIONS) | {"CF", "RCAM", "LCAM"}
    for lineup, positions in LINEUP_POSITIONS.items():
        if len(positions) != 10:
            raise ValueError(f"Lineup '{lineup}' must have exactly 10 outfield positions...")
```

## Logging

**Framework:** `print()` statements with emoji prefixes

**Patterns:**
- Use emoji indicators for different message types:
  - `🚀` - Starting/launching
  - `📍` - Step indicator
  - `✅` - Success
  - `❌` - Error
  - `⚠️` - Warning
  - `📊` - Stats/data related
  - `🏟️` - Team/match related

**Verbose Mode:**
```python
def _vprint(verbose: bool, message: str) -> None:
    if verbose:
        print(message)
```

## Comments

**When to Comment:**
- Module-level docstrings explaining purpose
- Function docstrings for public APIs
- Inline comments for complex logic only
- Step annotations with numbered indicators in scraper flows

**Docstring Style:**
```python
"""Textual app module for StatsHub TUI."""

"""Playwright-backed services used by the Textual TUI."""

def navigate_to_match(
    page,
    date_filter: str = "today",
    match_name: str = "14:00 Deportivo Alavés",
    verbose: bool = True,
) -> None:
    """Navigate to StatsHub and select a specific match."""
```

**Pragma Comments:**
```python
except ImportError as exc:  # pragma: no cover - runtime dependency guard
```

## Function Design

**Size:**
- Functions range from 5-50 lines for focused operations
- Larger functions (100-200 lines) exist for orchestration (e.g., `run_single()`, `collect_stats_for_all_positions()`)
- Break complex flows into private helper functions

**Parameters:**
- Use keyword-only arguments for clarity in complex functions
- Default values for optional parameters: `headless: bool = True`, `verbose: bool = True`
- `**kwargs` pattern not used; explicit parameter lists preferred

**Return Values:**
- Return structured data (dicts, dataclasses) rather than raw values
- Use `None` for "no result" rather than empty collections
- Tuple returns for multiple values: `tuple[str | None, bool]`

## Module Design

**Exports:**
- `__all__` explicitly defined in package `__init__.py` files:
  ```python
  __all__ = ["StatsHubTUI", "main"]
  ```

**Barrel Files:**
- `bot_sh/__init__.py` is minimal (empty in this codebase)
- `tui/__init__.py` exports main classes

**Module Structure:**
```
bot_sh/
  __init__.py       # Package marker (empty)
  models.py         # Data models, constants, dataclasses
  cli.py            # CLI argument parsing and orchestration
  scraper.py        # Playwright web scraping logic
  outputs.py        # File output formatting (JSON/CSV)

tui/
  __init__.py       # Package exports
  app.py            # Textual TUI application
  services.py       # Playwright services for TUI
  helpers.py        # Utility functions
  constants.py      # TUI-specific constants and CSS
```

## Dataclasses

**Pattern:**
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class MatchEntry:
    match_url: str
    home_team_tab: str
    away_team_tab: str
    match_id: str | None = None
```

## Unicode/Emoji Usage

- Emojis allowed in print statements for CLI UX
- Emojis used in TUI static text labels
- Source files use UTF-8 encoding (explicit `encoding="utf-8"` in file operations)

---

*Convention analysis: 2026-02-08*
