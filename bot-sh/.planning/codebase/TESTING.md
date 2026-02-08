# Testing Patterns

**Analysis Date:** 2026-02-08

## Test Framework

**Runner:**
- `unittest` (Python standard library)
- No pytest, nose, or other test runners detected
- No `pytest.ini`, `tox.ini`, or `pyproject.toml` test configuration

**Assertion Library:**
- Standard `unittest` assertions: `assertEqual()`, `assertIsNone()`, `assertIn()`, `assertRaises()`

**Run Commands:**
```bash
# Run all tests
python -m unittest discover tests/

# Run single test file
python tests/test_lineups.py
python tests/test_cli_stats.py
python tests/test_outputs.py

# Run with verbose output
python -m unittest discover tests/ -v
```

## Test File Organization

**Location:**
- Tests in dedicated `tests/` directory at project root
- Co-location pattern NOT used (tests separate from source)

**Naming:**
- Files: `test_*.py` pattern
  - `tests/test_lineups.py`
  - `tests/test_cli_stats.py`
  - `tests/test_outputs.py`

**Structure:**
```
bot-sh/
├── tests/
│   ├── __pycache__/         # Compiled test bytecode
│   ├── test_lineups.py      # Lineup validation tests
│   ├── test_cli_stats.py    # CLI argument parsing tests
│   └── test_outputs.py      # Output formatting tests
```

## Test Structure

**Suite Organization:**
```python
import unittest
import sys
from pathlib import Path

# Path manipulation for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot_sh.models import get_lineup_positions


class TestLineups(unittest.TestCase):
    def test_get_lineup_positions_includes_gk(self):
        positions = get_lineup_positions("4-3-3")
        self.assertIsNotNone(positions)
        self.assertEqual(positions[0], "GK")
        self.assertEqual(len(positions), 11)

    def test_get_lineup_positions_unknown(self):
        self.assertIsNone(get_lineup_positions("2-3-5"))


if __name__ == "__main__":
    unittest.main()
```

**Patterns:**
- One test class per module/feature
- Test method names are descriptive: `test_get_lineup_positions_includes_gk`
- Use `setUp()` / `tearDown()` not observed (tests are stateless)
- Standard `assert*` methods used (no custom assertions)

## Import Pattern in Tests

**Required boilerplate:**
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
```

This adds the project root to `sys.path` so `bot_sh` package can be imported.

## Mocking

**Framework:** None detected
- No `unittest.mock` usage observed
- No `pytest-mock` or `mock` library

**Testing Strategy:**
- Tests focus on pure functions and data transformation
- No Playwright browser automation tests (would require extensive mocking)
- No external API tests

**Example from `tests/test_outputs.py`:**
```python
def test_save_results_json(self):
    data = {
        "Team A": {
            "Tackles": [
                {
                    "position": "RB",
                    "total": "10",
                    "average": "1.2",
                    "highest": "3",
                }
            ]
        }
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "results.json")
        save_results(data, path)
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertIn("Team A", loaded)
        self.assertIn("Tackles", loaded["Team A"])
```

## Fixtures and Factories

**Test Data:**
- Inline test data within test methods
- No external fixture files
- Use `tempfile.TemporaryDirectory()` for file system operations

**Example:**
```python
def test_save_results_csv(self):
    data = {
        "Team A": {
            "Tackles": [
                {
                    "position": "RB",
                    "total": "10",
                    "average": "1.2",
                    "highest": "3",
                    "no_data": False,
                }
            ]
        }
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "results.csv")
        save_results(data, path)
        # assertions...
```

## Coverage

**Requirements:** No coverage enforcement detected
- No `.coveragerc` file
- No coverage threshold in CI
- No coverage badges in documentation

**View Coverage:**
```bash
# If you want to add coverage
pip install coverage
coverage run -m unittest discover tests/
coverage report
coverage html
```

## Test Types

**Unit Tests:**
- Focus on isolated functions
- Test data transformation logic
- Test validation functions

**Observed Test Coverage:**

1. **`tests/test_lineups.py`** - Lineup validation (36 lines)
   - Tests `get_lineup_positions()` from `bot_sh.models`
   - Validates GK inclusion, formation parsing, unknown formations

2. **`tests/test_cli_stats.py`** - CLI argument parsing (29 lines)
   - Tests `stats_from_args_strict()` and `stats_from_args_lenient()`
   - Tests valid/invalid stat names, SystemExit behavior

3. **`tests/test_outputs.py`** - Output formatting (71 lines)
   - Tests `derive_alt_output_path()` path transformations
   - Tests `save_results()` JSON and CSV output
   - Uses `tempfile.TemporaryDirectory()` for isolation

**Integration Tests:**
- NOT present
- No Playwright browser automation tests
- No end-to-end tests

**E2E Tests:**
- NOT present

## Common Patterns

**Testing Exceptions:**
```python
def test_stats_from_args_strict_invalid(self):
    with self.assertRaises(SystemExit):
        stats_from_args_strict("unknownstat", all_stats=False)
```

**Testing Edge Cases:**
```python
def test_derive_alt_output_path(self):
    self.assertEqual(derive_alt_output_path("out.json"), "out.csv")
    self.assertEqual(derive_alt_output_path("out.csv"), "out.json")
    self.assertEqual(derive_alt_output_path("out"), "out.csv")  # Edge case
```

**Testing Data Validation:**
```python
def test_get_lineup_positions_3421(self):
    positions = get_lineup_positions("3-4-2-1")
    self.assertIsNotNone(positions)
    self.assertIn("RF", positions)
    self.assertIn("LF", positions)
```

## Testing Gaps

**Not Tested:**
- `scraper.py` - Playwright browser automation (would require mocking `sync_playwright`)
- `cli.py` - Main orchestration functions (`run_single()`, `run_batch_*`)
- `tui/` - Textual TUI components (no UI testing framework)
- `interactive.py` - Interactive CLI (depends on `questionary`)
- File I/O error handling
- Network error scenarios
- Playwright page interactions

**Adding New Tests:**

For a new feature in `bot_sh/`:
```python
# tests/test_new_feature.py
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot_sh.new_module import new_function


class TestNewFeature(unittest.TestCase):
    def test_new_function_valid_input(self):
        result = new_function("valid_input")
        self.assertIsNotNone(result)
        self.assertEqual(result.expected_field, "expected_value")

    def test_new_function_invalid_input(self):
        with self.assertRaises(ValueError):
            new_function("invalid_input")


if __name__ == "__main__":
    unittest.main()
```

---

*Testing analysis: 2026-02-08*
