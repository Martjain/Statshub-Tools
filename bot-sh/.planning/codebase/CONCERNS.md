# Codebase Concerns

**Analysis Date:** 2026-02-08

## Tech Debt

**Large Monolithic Modules:**
- Issue: Multiple modules exceed 500 lines with mixed responsibilities
- Files: 
  - `bot_sh/cli.py` (691 lines) - combines CLI parsing, orchestration, output formatting
  - `tui/app.py` (654 lines) - single large TUI class handling all UI events
  - `interactive.py` (552 lines) - mixes interactive prompts, discovery logic, and orchestration
  - `bot_sh/scraper.py` (525 lines) - combines navigation, extraction, and spinner UI
- Impact: Difficult to test, maintain, and extend. Changes in one area risk breaking others
- Fix approach: 
  - Split `cli.py` into `orchestrator.py`, `formatter.py`, and CLI parsing
  - Extract discovery logic into `discovery.py` service
  - Create separate TUI screens/widgets in `tui/screens/`

**Duplicate Match Discovery Logic:**
- Issue: Match discovery implemented in 3+ places with slight variations
- Files:
  - `interactive.py` lines 113-174 (`_discover_matches`)
  - `tui/services.py` lines 44-128 (`discover_matches`)
  - `extract_team_names.py` lines 9-84 (similar extraction logic)
- Impact: Bug fixes must be applied in multiple places; inconsistencies between implementations
- Fix approach: Create single `DiscoveryService` in `bot_sh/discovery.py` shared across all interfaces

**Silent Failures via Empty Pass Statements:**
- Issue: 18+ bare `except: pass` blocks suppress errors silently
- Files:
  - `bot_sh/scraper.py`: lines 74, 116, 208, 220, 225, 231, 240, 246, 254, 266, 307, 390
  - `tui/services.py`: line 201
  - `interactive.py`: line 53
  - `extract_team_names.py`: line 114
- Impact: Errors go undetected; debugging requires adding print statements; data quality issues
- Fix approach: 
  - Replace `pass` with proper logging
  - Use specific exception types
  - Add error counters/metrics

**Missing Dependency Injection:**
- Issue: Playwright browser instances created directly in functions throughout codebase
- Files: `bot_sh/cli.py`, `interactive.py`, `tui/services.py`, `extract_team_names.py`
- Impact: Cannot mock browser for testing; cannot reuse browser instances; no connection pooling
- Fix approach: Create `BrowserContext` dependency injected into functions

## Known Bugs

**Race Condition in Position Toggle:**
- Issue: `_set_switch_state` in `bot_sh/scraper.py` (lines 359-381) may fail silently if checkbox state doesn't update
- Symptoms: Position data may be collected for wrong positions
- Trigger: Slow network or rapid position changes
- Workaround: None currently; relies on retry logic in `_safe_click`

**Temp File Leak in TUI Services:**
- Issue: `tui/services.py` `collect_data()` creates temp file but cleanup only happens in `finally` block if no exception during data processing
- Files: `tui/services.py` lines 170-201
- Symptoms: Temp files may accumulate in `/tmp` on repeated failures
- Fix approach: Use `tempfile.TemporaryDirectory()` context manager

**Incorrect Position Count Validation:**
- Issue: `models.py` `_validate_lineups()` checks for exactly 10 positions but includes GK separately
- Files: `bot_sh/models.py` lines 73-87
- Impact: Validation logic doesn't match actual usage pattern
- Current mitigation: Only 15 formations defined; works for known cases

## Security Considerations

**No Input Sanitization on File Paths:**
- Risk: Path traversal attacks possible via `--output`, `--output-path`, `--config` arguments
- Files: `bot_sh/cli.py`, `interactive.py`, `tui/app.py`
- Files affected: All output writing functions
- Current mitigation: None
- Recommendations: 
  - Validate paths don't escape intended directories
  - Use `pathlib.Path.resolve()` and check against allowed roots
  - Sanitize match names used in filenames (line 416 in `tui/app.py`)

**Hardcoded External Dependencies:**
- Risk: External website structure changes break scraper
- Files: All scraper-related files reference `https://www.statshub.com/`
- Current mitigation: None
- Recommendations: 
  - Add health check endpoint monitoring
  - Implement circuit breaker pattern for external calls

**No Rate Limiting:**
- Risk: Could be blocked by target website for excessive requests
- Files: `bot_sh/scraper.py`, `extract_team_names.py`
- Current mitigation: Implicit delays via Playwright timeouts
- Recommendations:
  - Add explicit rate limiting between requests
  - Add jitter to retry delays
  - Respect robots.txt

## Performance Bottlenecks

**Synchronous Browser Operations:**
- Problem: All Playwright operations are synchronous; browser waits idle during processing
- Files: Entire codebase uses `sync_playwright`
- Cause: No async/await pattern implemented
- Improvement path: 
  - Migrate to `async_playwright` for concurrent match processing
  - Use asyncio.gather() for parallel stat collection across positions

**Repeated Browser Launches:**
- Problem: New browser launched for each match in batch mode
- Files: `bot_sh/cli.py` `run_batch_from_team_tabs()` lines 399-453
- Cause: Browser context created inside loop
- Improvement path:
  - Reuse single browser context across matches
  - Use persistent context with caching
  - Consider connection pooling

**No Discovery Caching:**
- Problem: Match list rediscovered on every run
- Files: `interactive.py`, `tui/services.py`
- Cause: No cache mechanism for discovered matches
- Improvement path:
  - Cache discovered matches with TTL (e.g., 5 minutes)
  - Store in JSON file or simple in-memory cache

**Redundant DOM Queries:**
- Problem: `extract_position_stats` in `bot_sh/scraper.py` queries DOM multiple times per position
- Files: `bot_sh/scraper.py` lines 91-195
- Cause: Separate locator calls for total, average, highest
- Improvement path:
  - Extract all stats in single JavaScript evaluation
  - Cache locator results

## Fragile Areas

**Web Scraping Selectors:**
- Files: `bot_sh/scraper.py` (entire file)
- Why fragile: Relies on specific DOM structure, aria roles, and text content from external site
- Safe modification: 
  - Add fallback selector strategies
  - Implement selector versioning/health checks
  - Add comprehensive error messages when selectors fail
- Test coverage: No automated tests for scraping logic

**Team Name Matching Logic:**
- Files: `extract_team_names.py` lines 117-141
- Why fragile: Uses fuzzy word matching between slug and tab text
- Safe modification:
  - Add validation that extracted tabs contain expected team names
  - Log warnings when fallback positional matching is used
- Test coverage: None

**TUI State Machine:**
- Files: `tui/app.py` lines 54, 161-210 (flow state management)
- Why fragile: State transitions scattered across event handlers; no centralized validation
- Safe modification:
  - Add explicit state transition validation
  - Log state changes for debugging
- Test coverage: None

**Hardcoded Default Values:**
- Files: `bot_sh/models.py` lines 135-137
- Why fragile: Default match/team names may not exist on target site
- Safe modification:
  - Validate defaults exist on startup
  - Make defaults configurable

## Scaling Limits

**Browser Instance Limit:**
- Current capacity: Single browser instance per process
- Limit: Cannot parallelize across matches without multiprocessing
- Scaling path: Implement queue-based worker pool with browser reuse

**Memory Leak Potential:**
- Resource: Playwright page objects in long-running TUI
- Limit: DOM snapshots accumulate in page context
- Scaling path: 
  - Periodically recreate page context
  - Add explicit cleanup of page resources

**Stat Collection Throughput:**
- Current capacity: ~25 positions × 2 teams × N stats sequentially
- Limit: Each position requires separate toggle/click/wait cycle
- Scaling path: 
  - Batch position toggles where UI allows
  - Use API endpoints if available instead of UI automation

## Dependencies at Risk

**Playwright:**
- Risk: Major version updates may break locator APIs
- Impact: Entire scraping functionality stops working
- Migration plan: 
  - Pin to major version in requirements
  - Abstract locator strategies behind adapter pattern
  - Add integration tests that verify critical paths

**Questionary (Interactive CLI):**
- Risk: TTY handling may break on different terminal emulators
- Impact: Interactive mode unusable on some systems
- Migration plan: 
  - Add `--non-interactive` fallback (already exists)
  - Test on multiple terminal types

**Textual (TUI):**
- Risk: Rapidly evolving framework; API changes common
- Impact: TUI may break on updates
- Migration plan:
  - Pin version in requirements
  - Keep TUI logic isolated from business logic

## Missing Critical Features

**Retry Logic:**
- Problem: No automatic retry for transient network failures
- Blocks: Reliable batch processing
- Priority: High

**Structured Logging:**
- Problem: Uses `print()` statements throughout; no log levels
- Blocks: Production monitoring, debugging at scale
- Priority: Medium

**Configuration Management:**
- Problem: No central config file; defaults scattered in code
- Blocks: Environment-specific deployments
- Priority: Medium

**Data Validation:**
- Problem: No schema validation for scraped data
- Blocks: Data quality assurance
- Priority: Medium

**Health Checks:**
- Problem: No way to verify target site availability before running
- Blocks: Proactive failure detection
- Priority: Low

## Test Coverage Gaps

**No Scraper Tests:**
- What's not tested: `bot_sh/scraper.py` (525 lines) - zero test coverage
- Files: `bot_sh/scraper.py`
- Risk: DOM changes break extraction silently
- Priority: Critical

**No TUI Tests:**
- What's not tested: `tui/app.py` (654 lines) - zero test coverage
- Files: `tui/app.py`
- Risk: UI changes break user workflows
- Priority: High

**No Interactive CLI Tests:**
- What's not tested: `interactive.py` (552 lines) - zero test coverage
- Files: `interactive.py`
- Risk: Interactive flows break on changes
- Priority: High

**No Integration Tests:**
- What's not tested: End-to-end flows from discovery to output
- Files: All orchestration in `bot_sh/cli.py`
- Risk: Component integration failures
- Priority: High

**Limited Unit Test Coverage:**
- Current tests (136 total lines):
  - `test_cli_stats.py`: Only tests argument parsing (29 lines)
  - `test_lineups.py`: Only tests lineup position lookup (36 lines)
  - `test_outputs.py`: Tests output formatting (71 lines)
- Missing coverage:
  - All scraping logic
  - All TUI logic
  - All discovery logic
  - Error handling paths
- Priority: Critical

## Code Quality Issues

**Magic Numbers:**
- Issue: Hardcoded timeouts and delays throughout
- Examples:
  - `timeout=5000` / `timeout=15000` / `timeout=8000` in various places
  - `wait_timeout_ms=2000` in scraper
  - `per_position_timeout_s=20.0` in scraper
- Fix approach: Create constants module with documented timeout values

**Missing Type Hints:**
- Issue: Many functions lack return type annotations
- Files: `interactive.py`, `extract_team_names.py`
- Impact: Reduced IDE support, harder refactoring

**Inconsistent Error Handling:**
- Issue: Mix of `print()` warnings, exception raising, and silent failures
- Files: All files
- Impact: Unpredictable error behavior
- Fix approach: Adopt consistent error handling strategy (return Result[T, E] or raise specific exceptions)

---

*Concerns audit: 2026-02-08*
