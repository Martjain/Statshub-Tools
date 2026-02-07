"""Playwright-backed services used by the Textual TUI."""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from bot_sh import cli
from bot_sh.models import CLI_STAT_MAPPING
from playwright.sync_api import sync_playwright


def discover_matches(date_filter: str, headless: bool) -> list[dict]:
    matches: list[dict] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto("https://www.statshub.com/")
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                page.wait_for_load_state("domcontentloaded", timeout=8000)
                page.wait_for_timeout(1200)

            label = date_filter.capitalize()
            page.get_by_text(label, exact=True).click()
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                page.wait_for_load_state("domcontentloaded", timeout=8000)
                page.wait_for_timeout(1200)

            links = page.locator('a[href*="/fixture/"]').all()
            seen = set()
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if not href or href in seen:
                        continue
                    seen.add(href)
                    match = re.search(r"/fixture/([^/]+)/(\d+)", href)
                    if not match:
                        continue
                    slug = match.group(1)
                    parts = slug.split("-vs-")
                    if len(parts) != 2:
                        continue
                    home_slug, away_slug = parts
                    home = " ".join(w.capitalize() for w in home_slug.split("-"))
                    away = " ".join(w.capitalize() for w in away_slug.split("-"))
                    try:
                        text = link.inner_text() or ""
                    except Exception:
                        text = ""
                    time_match = re.search(r"\b(\d{1,2}:\d{2})\b", text)
                    kickoff = time_match.group(1) if time_match else ""
                    matches.append(
                        {
                            "match_url": href,
                            "home_name": home,
                            "away_name": away,
                            "kickoff_time": kickoff,
                        }
                    )
                except Exception:
                    continue
        finally:
            context.close()
            browser.close()

    return sorted(matches, key=lambda m: f"{m.get('home_name', '')} vs {m.get('away_name', '')}")


def extract_tabs(match_url: str, headless: bool) -> tuple[str, str]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        try:
            full_url = match_url if match_url.startswith("http") else "https://www.statshub.com" + match_url
            page.goto(full_url)
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                page.wait_for_timeout(1200)
            page.get_by_role("button", name="Opponent Stats NEW!").click()
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                page.wait_for_timeout(1200)
            tabs = [t.inner_text().strip() for t in page.locator('[role="tab"]').all()]
            tabs = [t for t in tabs if t]
            if len(tabs) < 2:
                raise RuntimeError("Could not detect team tabs for selected match.")
            return tabs[0], tabs[1]
        finally:
            context.close()
            browser.close()


def collect_data(
    match_url: str,
    stat_keys: list[str],
    min_average: float,
    has_lineups: bool,
    home_positions: list[str] | None,
    away_positions: list[str] | None,
    headless: bool,
) -> dict:
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp_file:
        output_path = tmp_file.name

    try:
        home_tab, away_tab = extract_tabs(match_url, headless=headless)
        internal_stats = [CLI_STAT_MAPPING[s] for s in stat_keys if s in CLI_STAT_MAPPING]
        cli.run_single_by_url(
            match_url=match_url,
            home_team_tab=home_tab,
            away_team_tab=away_tab,
            min_average=min_average,
            debug=False,
            stats=internal_stats,
            headless=headless,
            output=output_path,
            output_both=False,
            home_lineup_positions=home_positions if has_lineups else None,
            away_lineup_positions=away_positions if has_lineups else None,
            verbose=False,
        )
        with open(output_path, "r", encoding="utf-8") as file_obj:
            return json.load(file_obj)
    finally:
        try:
            Path(output_path).unlink(missing_ok=True)
        except Exception:
            pass
