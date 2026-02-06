"""Isolated debug runner for a single match/team/stat."""

from __future__ import annotations

import argparse
import time

from playwright.sync_api import sync_playwright

from bot_sh.models import POSITIONS
from bot_sh.scraper import _safe_click


def _safe_wait_networkidle(page, timeout_ms: int = 10000) -> bool:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
        return True
    except Exception as e:
        print(f"   ⚠️ networkidle timeout: {e}")
        return False


def _extract_stats_quick(page):
    """Quick extraction without long waits."""
    try:
        if (
            page.locator("text=No data found for the selected criteria").count() > 0
            or page.locator("text=No data found").count() > 0
        ):
            print("   ⚠️ UI says: No data found")
            return {"total": "0", "average": "0.0", "highest": "0", "no_data": True}
    except Exception:
        pass

    total_count = 0
    try:
        total_count = page.locator("text=Total").count()
    except Exception:
        total_count = 0
    if total_count == 0:
        print("   ⚠️ No 'Total' elements found yet")

    start = time.monotonic()
    try:
        page.wait_for_selector("text=Total", timeout=2000)
    except Exception:
        elapsed = time.monotonic() - start
        print(f"   ⚠️ Total selector timeout after {elapsed:.2f}s (no data)")
        return {"total": "0", "average": "0.0", "highest": "0", "no_data": True}

    def _value(label: str, pattern: str):
        try:
            text = page.locator(f"text={label}").first.evaluate(
                "el => el.parentElement.textContent"
            )
        except Exception:
            text = ""
        import re

        m = re.search(pattern, text)
        return m.group() if m else None

    return {
        "total": _value("Total", r"\d+"),
        "average": _value("Average", r"[\d.]+"),
        "highest": _value("Highest", r"\d+"),
    }


def run_debug(
    match_url: str,
    team_tab: str,
    stat_value: str,
    headless: bool,
    per_position_timeout_s: float,
) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        try:
            if not match_url.startswith("http"):
                match_url = "https://www.statshub.com" + match_url

            print(f"Navigating: {match_url}")
            page.goto(match_url)
            if not _safe_wait_networkidle(page, 15000):
                print("   ⚠️ STUCK AT NAVIGATION")
                return

            print("Opening Opponent Stats…")
            try:
                page.get_by_role("button", name="Opponent Stats NEW!").click(timeout=10000)
            except Exception as e:
                print(f"   ⚠️ STUCK AT OPPONENT STATS CLICK: {e}")
                return
            if not _safe_wait_networkidle(page, 15000):
                print("   ⚠️ STUCK AFTER OPPONENT STATS")
                return

            print(f"Selecting team tab: {team_tab}")
            try:
                page.get_by_role("tab", name=team_tab).click(timeout=10000)
            except Exception as e:
                print(f"   ⚠️ STUCK AT TEAM TAB CLICK: {e}")
                return
            if not _safe_wait_networkidle(page, 10000):
                print("   ⚠️ STUCK AFTER TEAM TAB")
                return

            print(f"Selecting stat: {stat_value}")
            try:
                page.get_by_label("Stat").select_option(stat_value, timeout=10000)
            except Exception as e:
                print(f"   ⚠️ STUCK AT STAT SELECT: {e}")
                return
            if not _safe_wait_networkidle(page, 10000):
                print("   ⚠️ STUCK AFTER STAT SELECT")
                return

            print("Opening position selector…")
            try:
                page.get_by_role("button", name="Select positions").click(timeout=10000)
            except Exception as e:
                print(f"   ⚠️ STUCK AT POSITION SELECTOR: {e}")
                return

            for position in POSITIONS:
                start = time.monotonic()
                print(f"\nPosition: {position}")
                locator = page.locator(f'[role="switch"][id="position-{position}"]')
                if locator.count() == 0:
                    locator = page.get_by_role("switch", name=position, exact=True)
                if locator.count() == 0:
                    locator = page.get_by_role("switch", name=position)

                click_start = time.monotonic()
                is_striker = position in ["ST", "RST", "LST"]
                clicked = _safe_click(
                    page,
                    locator,
                    f"switch for {position}",
                    timeout_ms=500 if is_striker else 2000,
                    fast_mode=is_striker,
                )
                click_elapsed = time.monotonic() - click_start
                print(f"   click_time={click_elapsed:.2f}s")
                if not clicked:
                    print(f"   ✗ click failed for {position}")
                    continue

                wait_start = time.monotonic()
                _safe_wait_networkidle(page, 8000)
                wait_elapsed = time.monotonic() - wait_start
                print(f"   networkidle_time={wait_elapsed:.2f}s")
                stats = _extract_stats_quick(page)
                elapsed = time.monotonic() - start
                print(
                    f"   total={stats['total']} avg={stats['average']} high={stats['highest']} ({elapsed:.2f}s)"
                )

                # toggle off
                off_locator = page.locator(f'[role="switch"][id="position-{position}"]')
                if off_locator.count() == 0:
                    off_locator = page.get_by_role("switch", name=position, exact=True)
                if off_locator.count() == 0:
                    off_locator = page.get_by_role("switch", name=position)
                _safe_click(page, off_locator, f"turning off switch for {position}")

                elapsed = time.monotonic() - start
                if elapsed > per_position_timeout_s:
                    print(
                        f"   ⚠️ STUCK AT POSITION {position} (>{per_position_timeout_s}s). Aborting."
                    )
                    return

        finally:
            context.close()
            browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Isolated match debug runner")
    parser.add_argument(
        "--match-url",
        default="/fixture/asteras-tripolis-vs-olympiacos-fc-ml8dmj/15381664",
    )
    parser.add_argument("--team-tab", default="ASTERAS AKTOR")
    parser.add_argument("--stat", default="shots")
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument(
        "--per-position-timeout",
        type=float,
        default=20.0,
        help="Seconds allowed per position before aborting.",
    )
    args = parser.parse_args()
    run_debug(
        args.match_url,
        args.team_tab,
        args.stat,
        args.headless,
        args.per_position_timeout,
    )


if __name__ == "__main__":
    main()
