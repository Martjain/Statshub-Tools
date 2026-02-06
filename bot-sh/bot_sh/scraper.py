import re
import threading
import time

from .models import POSITIONS


def _vprint(verbose: bool, message: str) -> None:
    if verbose:
        print(message)


def navigate_to_match(
    page,
    date_filter: str = "today",
    match_name: str = "14:00 Deportivo Alavés",
    verbose: bool = True,
) -> None:
    """Navigate to StatsHub and select a specific match."""
    _vprint(verbose, "📍 Step 1: Navigating to StatsHub...")
    page.goto("https://www.statshub.com/")

    label = date_filter.capitalize()
    _vprint(verbose, f"📍 Step 2: Clicking '{label}' filter...")
    page.get_by_text(label, exact=True).click()

    _vprint(verbose, f"📍 Step 3: Selecting match - {match_name}...")
    page.get_by_role("link", name=match_name).click()

    _vprint(verbose, "📍 Step 4: Opening 'Opponent Stats'...")
    page.get_by_role("button", name="Opponent Stats NEW!").click()


def navigate_to_match_by_url(page, match_url: str, verbose: bool = True) -> None:
    """Navigate directly to a match using its URL."""
    if not match_url.startswith("http"):
        match_url = "https://www.statshub.com" + match_url

    _vprint(verbose, f"📍 Step 1: Navigating directly to match: {match_url}")
    page.goto(match_url)
    page.wait_for_load_state("networkidle")

    _vprint(verbose, "📍 Step 2: Opening 'Opponent Stats'...")
    page.get_by_role("button", name="Opponent Stats NEW!").click()


def select_team_and_stat(
    page,
    team_name: str,
    stat_value: str,
    stat_display: str | None = None,
    verbose: bool = True,
) -> None:
    if stat_display is None:
        stat_display = stat_value
    _vprint(verbose, f"📍 Step 5: Selecting team tab '{team_name}'...")
    page.get_by_role("tab", name=team_name).click()

    _vprint(verbose, f"📍 Step 6: Selecting stat '{stat_display}'...")
    try:
        page.get_by_label("Stat").select_option(stat_value)
    except Exception:
        try:
            page.get_by_label("Stat").select_option(label=stat_display)
        except Exception as e2:
            print(
                f"   ⚠️ Failed to select stat {stat_display} (tried value '{stat_value}')"
            )
            try:
                stat_select = page.get_by_label("Stat")
                options = stat_select.locator("option").all()
                print(f"   Available options: {[opt.inner_text() for opt in options]}")
            except Exception:
                pass
            raise e2


def save_debug_artifacts(page, position: str, stats: dict) -> None:
    safe_pos = position.replace("/", "_")
    try:
        html_path = f"debug_{safe_pos}.html"
        png_path = f"debug_{safe_pos}.png"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page.content())
        page.screenshot(path=png_path)
        print(f"   🐞 Saved debug artifacts for {position}: {html_path}, {png_path}")
    except Exception as e:
        print(f"   ⚠️ Failed to save debug artifacts for {position}: {e}")


def extract_position_stats(
    page, position: str, debug: bool = False, wait_timeout_ms: int = 2000
) -> dict:
    start_wait = time.monotonic()
    try:
        page.wait_for_load_state("networkidle", timeout=wait_timeout_ms)
    except Exception:
        if debug:
            elapsed = time.monotonic() - start_wait
            print(f"   ⚠️ networkidle timeout after {elapsed:.2f}s for {position}")

    try:
        try:
            if (
                page.locator("text=No data found for the selected criteria").count() > 0
                or page.locator("text=No data found").count() > 0
            ):
                return {
                    "position": position,
                    "total": "0",
                    "average": "0.0",
                    "highest": "0",
                    "no_data": True,
                }
        except Exception:
            pass

        try:
            page.wait_for_selector("text=Total", timeout=wait_timeout_ms)
        except Exception:
            if debug:
                print(
                    f"   ⚠️ 'Total' selector timeout after {wait_timeout_ms}ms for {position}"
                )
                save_debug_artifacts(
                    page,
                    position,
                    {
                        "position": position,
                        "total": None,
                        "average": None,
                        "highest": None,
                    },
                )
            return {
                "position": position,
                "total": "0",
                "average": "0.0",
                "highest": "0",
                "no_data": True,
            }

        try:
            total_text = page.locator("text=Total").first.evaluate(
                "el => el.parentElement.textContent"
            )
        except Exception:
            total_text = ""

        total_value = (
            re.search(r"\d+", total_text).group()
            if re.search(r"\d+", total_text)
            else None
        )

        average_loc = page.locator("text=Average").first
        try:
            average_text = average_loc.evaluate("el => el.parentElement.textContent")
        except Exception:
            average_text = ""
        average_value = (
            re.search(r"[\d.]+", average_text).group()
            if re.search(r"[\d.]+", average_text)
            else None
        )

        highest_loc = page.locator("text=Highest").first
        try:
            highest_text = highest_loc.evaluate("el => el.parentElement.textContent")
        except Exception:
            highest_text = ""
        highest_value = (
            re.search(r"\d+", highest_text).group()
            if re.search(r"\d+", highest_text)
            else None
        )

        result = {
            "position": position,
            "total": total_value,
            "average": average_value,
            "highest": highest_value,
        }

        if debug and (
            result["total"] is None
            or result["average"] is None
            or result["highest"] is None
        ):
            save_debug_artifacts(page, position, result)

        return result
    except Exception as e:
        print(f"   ⚠️ Could not extract stats for {position}: {str(e)}")
        return {"position": position, "total": None, "average": None, "highest": None}


def _safe_click(
    page, locator, label: str, timeout_ms: int = 2000, fast_mode: bool = False
) -> bool:
    if fast_mode:
        try:
            handle = locator.element_handle()
            if handle:
                page.evaluate("el => el.click()", handle)
                return True
        except Exception:
            pass
        try:
            locator.click(force=True, timeout=timeout_ms)
            return True
        except Exception as e:
            print(f"   ⚠️ Failed clicking {label}: {e}")
            return False

    try:
        locator.click(timeout=timeout_ms)
        return True
    except Exception:
        pass

    try:
        locator.scroll_into_view_if_needed()
    except Exception:
        pass

    try:
        locator.click(timeout=timeout_ms)
        return True
    except Exception:
        pass

    try:
        handle = locator.element_handle()
        if handle:
            page.evaluate(
                "el => el.scrollIntoView({block: 'center', inline: 'center'})", handle
            )
    except Exception:
        pass

    try:
        locator.click(force=True, timeout=timeout_ms)
        return True
    except Exception as e:
        pass

    try:
        handle = locator.element_handle()
        if handle:
            page.evaluate("el => el.click()", handle)
            return True
    except Exception:
        pass

    try:
        handle = locator.element_handle()
        if handle:
            box = handle.bounding_box()
            if box:
                page.mouse.click(
                    box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                )
                return True
    except Exception:
        pass

    try:
        page.keyboard.press("PageDown")
        locator.click(timeout=timeout_ms)
        return True
    except Exception as e:
        print(f"   ⚠️ Failed clicking {label}: {e}")
        return False


def _position_locator(page, position: str):
    return page.locator(f'[role="switch"][id="position-{position}"]')


def _read_totals_blob(page) -> str:
    try:
        return page.locator("text=Total").first.evaluate(
            "el => el.parentElement.textContent || ''"
        )
    except Exception:
        return ""


def _wait_for_stats_update(page, prev_blob: str, timeout_ms: int = 2000) -> None:
    try:
        page.wait_for_function(
            """
            (prev) => {
              const noData = document.body.innerText.includes('No data found');
              const totalEl = Array.from(document.querySelectorAll('*')).find(
                el => el.textContent && el.textContent.includes('Total')
              );
              const blob = totalEl && totalEl.parentElement ? totalEl.parentElement.textContent : '';
              return noData || (blob && blob !== prev);
            }
            """,
            prev_blob,
            timeout=timeout_ms,
        )
    except Exception:
        pass


def _is_checked(locator) -> bool:
    try:
        aria = locator.get_attribute("aria-checked")
        if aria is not None:
            return aria == "true"
        data_state = locator.get_attribute("data-state")
        if data_state is not None:
            return data_state == "checked"
        return False
    except Exception:
        return False


def _ensure_state(locator, checked: bool, timeout_ms: int = 2000) -> bool:
    desired = "true" if checked else "false"
    try:
        locator.wait_for(state="attached", timeout=timeout_ms)
    except Exception:
        return False
    try:
        locator.wait_for_attribute("aria-checked", desired, timeout=timeout_ms)
        return True
    except Exception:
        try:
            data_desired = "checked" if checked else "unchecked"
            locator.wait_for_attribute("data-state", data_desired, timeout=timeout_ms)
            return True
        except Exception:
            return False


def _clear_all_positions(page) -> None:
    for position in POSITIONS:
        locator = _position_locator(page, position)
        if locator.count() == 0:
            locator = page.get_by_role("switch", name=position, exact=True)
        if locator.count() == 0:
            locator = page.get_by_role("switch", name=position)
        if _is_checked(locator):
            _safe_click(
                page,
                locator,
                f"switch for {position} (clear)",
                timeout_ms=1500,
                fast_mode=False,
            )
            _ensure_state(locator, checked=False, timeout_ms=1500)


def _set_switch_state(page, position: str, checked: bool, attempts: int = 3) -> bool:
    for _ in range(attempts):
        locator = _position_locator(page, position)
        if locator.count() == 0:
            locator = page.get_by_role("switch", name=position, exact=True)
        if locator.count() == 0:
            locator = page.get_by_role("switch", name=position)

        current = _is_checked(locator)
        if current == checked:
            return True

        # Try a fast JS click first, then normal click.
        _safe_click(
            page,
            locator,
            f"switch for {position} (set {checked})",
            timeout_ms=1500,
            fast_mode=False,
        )
        if _ensure_state(locator, checked=checked, timeout_ms=1500):
            return True
    return False


def _scroll_positions_to_bottom(page) -> None:
    try:
        page.locator('[role="dialog"]').first.evaluate(
            "el => el.scrollTo(0, el.scrollHeight)"
        )
    except Exception:
        pass


def collect_stats_for_all_positions(
    page,
    team_name: str,
    stat_type: str,
    debug: bool = False,
    per_position_timeout_s: float = 20.0,
    show_spinner: bool = True,
    verbose: bool = True,
) -> list:
    collected_data = []

    _vprint(verbose, "📍 Step 7: Opening position selector...")
    page.get_by_role("button", name="Select positions").click()

    _vprint(
        verbose, f"📍 Step 8: Collecting stats for all positions ({team_name})..."
    )

    spinner = None
    errors = []
    if show_spinner and not debug:
        spinner = _Spinner(
            f"Collecting positions for {team_name} ({stat_type})",
            total=len(POSITIONS),
        )
        spinner.start()
    for position in POSITIONS:
        try:
            start_time = time.monotonic()
            if position in ["ST", "RST", "LST"]:
                _scroll_positions_to_bottom(page)

            locator = _position_locator(page, position)
            if locator.count() == 0:
                locator = page.get_by_role("switch", name=position, exact=True)
            if locator.count() == 0:
                locator = page.get_by_role("switch", name=position)

            is_striker = position in ["ST", "RST", "LST"]
            click_timeout = 500 if is_striker else 2000
            if not _safe_click(
                page,
                locator,
                f"switch for {position}",
                timeout_ms=click_timeout,
                fast_mode=is_striker,
            ):
                raise Exception("Click failed")

            if spinner:
                spinner.step(position)
            elif debug:
                print(f"   - Collecting data for {position}...")
            stats = extract_position_stats(
                page, position, debug=debug, wait_timeout_ms=2000
            )
            collected_data.append(stats)
            if debug:
                print(
                    f"     Total: {stats['total']}, Avg: {stats['average']}, High: {stats['highest']}"
                )

            try:
                off_locator = _position_locator(page, position)
                if off_locator.count() == 0:
                    off_locator = page.get_by_role("switch", name=position, exact=True)
                if off_locator.count() == 0:
                    off_locator = page.get_by_role("switch", name=position)
                _safe_click(
                    page,
                    off_locator,
                    f"turning off switch for {position}",
                    timeout_ms=2000,
                    fast_mode=False,
                )
                if _is_checked(off_locator):
                    _safe_click(
                        page,
                        off_locator,
                        f"turning off switch for {position} (retry)",
                        timeout_ms=2000,
                        fast_mode=False,
                    )
            except Exception:
                print(f"   ⚠️ Failed turning off switch for {position}")

            elapsed = time.monotonic() - start_time
            if debug and elapsed > per_position_timeout_s:
                print(f"   ⚠️ Position {position} took {elapsed:.2f}s")
        except Exception as e:
            if spinner:
                errors.append(position)
            else:
                print(f"   ⚠️ Error processing {position}: {str(e)}")

    if spinner:
        spinner.stop()
        if errors:
            print(f"⚠️  Positions with issues: {', '.join(errors)}")

    return collected_data


class _Spinner:
    def __init__(self, text: str, total: int) -> None:
        self._text = text
        self._total = total
        self._current = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def start(self) -> None:
        self._thread.start()

    def step(self, label: str) -> None:
        self._current += 1
        self._text = f"Collecting positions {self._current}/{self._total} ({label})"

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1)
        print("\r✅ Positions collected".ljust(80))

    def _run(self) -> None:
        i = 0
        while not self._stop.is_set():
            ch = self._chars[i % len(self._chars)]
            msg = f"\r{ch} {self._text}"
            print(msg.ljust(80), end="", flush=True)
            time.sleep(0.1)
            i += 1
