# External Integrations

**Analysis Date:** 2026-02-08

## APIs & External Services

**StatsHub Website:**
- URL: `https://www.statshub.com/`
- Purpose: Primary data source for football/soccer match statistics
- Integration Type: Web scraping via Playwright browser automation
- Endpoints Used:
  - `/` - Homepage with match listings
  - Individual match pages (URLs extracted dynamically)
  - "Opponent Stats" feature accessed via button click

**No External APIs Detected:**
- No REST API clients
- No GraphQL
- No third-party SDKs for data services

## Data Storage

**Databases:**
- None detected
- No SQL or NoSQL databases in use

**File Storage:**
- Local filesystem only
- Output formats:
  - JSON: Structured match statistics
  - CSV: Tabular statistics data
- Configuration files:
  - `.interactive_prefs.json` - User preferences (JSON)
  - `team_tabs.json` - Batch match definitions (JSON)

**Caching:**
- None detected
- No Redis, memcached, or file-based caching

## Authentication & Identity

**Auth Provider:**
- Not applicable
- No authentication required for StatsHub scraping (public data)
- No API keys or credentials detected

## Monitoring & Observability

**Error Tracking:**
- None detected
- No Sentry, Rollbar, or similar services

**Logs:**
- Console output only (`print()` statements)
- Debug artifacts saved locally when `--debug` flag used:
  - HTML snapshots: `debug_{position}.html`
  - Screenshots: `debug_{position}.png`

**Metrics:**
- None detected

## CI/CD & Deployment

**Hosting:**
- Not applicable - local CLI tool
- No deployment configuration detected

**CI Pipeline:**
- None detected
- No GitHub Actions, GitLab CI, or similar

**Package Distribution:**
- None detected
- Not published to PyPI

## Environment Configuration

**Required Configuration:**
- None - tool works out of the box

**Optional Configuration:**
- `.interactive_prefs.json` - Stores user preferences between sessions
- `team_tabs.json` - Defines batch processing match list

**Secrets Location:**
- Not applicable - no secrets required

## Webhooks & Callbacks

**Incoming:**
- None - no web server component

**Outgoing:**
- None - no webhook notifications

## Browser Automation Details

**Playwright Configuration:**
- Browser: Chromium
- Mode: Headless (configurable via `--headless` flag)
- Context: New context per session
- Navigation: Direct URL navigation and element-based interactions

**Key Interactions:**
- `page.goto("https://www.statshub.com/")` - Site navigation
- `page.get_by_text(label, exact=True).click()` - Date filter selection
- `page.get_by_role("link", name=match_name).click()` - Match selection
- `page.get_by_role("button", name="Opponent Stats NEW!").click()` - Stats panel
- `page.get_by_role("tab", name=team_name).click()` - Team tab switching
- `page.get_by_label("Stat").select_option(stat_value)` - Stat selection

**Data Extraction:**
- HTML content parsing via Playwright locators
- JavaScript execution via `page.evaluate()` for table data extraction
- Screenshots for debug artifacts

## Network Dependencies

**Required Connectivity:**
- `https://www.statshub.com/` - Must be accessible
- No proxy configuration detected

**Offline Capability:**
- None - requires live website access

---

*Integration audit: 2026-02-08*
