"""Textual app module for StatsHub TUI."""

from __future__ import annotations

import argparse
import asyncio
import re
from pathlib import Path

try:
    from rich.text import Text
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import (
        Button,
        Checkbox,
        DataTable,
        Footer,
        Header,
        Input,
        Label,
        OptionList,
        RichLog,
        Select,
        SelectionList,
        Static,
    )
except ImportError as exc:  # pragma: no cover - runtime dependency guard
    raise SystemExit(
        "Missing dependency 'textual'. Install it with: pip install textual"
    ) from exc

from bot_sh.models import CLI_STAT_MAPPING, LINEUP_POSITIONS, get_lineup_positions

from .constants import STAT_CHOICES, TUI_CSS
from .helpers import display_name_for_cli_key, to_float
from .services import collect_data, discover_matches


class StatsHubTUI(App):
    CSS = TUI_CSS
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, headless: bool = True) -> None:
        super().__init__()
        self.default_headless = headless
        self._selected_stats: list[str] = []
        self._selected_display_stats: list[str] = []
        self._selected_display_to_cli: dict[str, str] = {}
        self._current_stat: str | None = None
        self._last_data: dict = {}
        self._discovered_matches: list[dict] = []
        self._visible_matches: list[dict] = []
        self._flow_state = "config"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="body"):
            with Vertical(id="left-pane"):
                yield Static("Interactive Flow", id="options-title")

                yield Label("1) Match Date", classes="field-label")
                yield Select(
                    [("Today", "today"), ("Tomorrow", "tomorrow")],
                    value="today",
                    id="date-choice",
                )

                yield Label("2) Lineup Mode", classes="field-label")
                yield Checkbox("Confirmed lineups", id="has-lineups", value=False)
                yield Static(
                    "Path: No confirmed lineups. Collector will use non-lineup flow.",
                    id="lineup-mode-note",
                )
                yield Label("Home lineup", id="home-lineup-label", classes="field-sub-label")
                yield Input(placeholder="Home lineup (e.g., 4-2-3-1)", id="home-lineup", disabled=True)
                yield Label("Away lineup", id="away-lineup-label", classes="field-sub-label")
                yield Input(placeholder="Away lineup (e.g., 4-3-3)", id="away-lineup", disabled=True)

                yield Label("3) Stats", classes="field-label")
                yield SelectionList(
                    *[(label, key, True) for key, label in STAT_CHOICES],
                    id="stats-list",
                )

                yield Label("4) Minimum Average", classes="field-label")
                yield Input(value="1.0", id="min-average")

                yield Label("5) Runtime + Output", classes="field-label")
                yield Checkbox("Run headless", id="headless", value=self.default_headless)
                yield Select(
                    [
                        ("Terminal only", "terminal"),
                        ("JSON file", "json"),
                        ("CSV file", "csv"),
                        ("Both JSON and CSV", "both"),
                    ],
                    value="terminal",
                    id="output-choice",
                )
                yield Input(placeholder="Optional output path", id="output-path", disabled=True)

                yield Label("6) Discover + Filter + Sort", classes="field-label")
                yield Button("Discover Matches", id="discover-matches", variant="primary")
                yield Input(placeholder="Team filter (optional)", id="team-filter")
                yield Select(
                    [("None (site order)", "none"), ("Alphabetical", "alpha"), ("Kickoff time", "time")],
                    value="none",
                    id="sort-mode",
                )
                yield Button("Apply To Match List", id="apply-match-view", variant="default")

                yield Label("7) Match Selection", classes="field-label")
                yield Select(
                    [("All matches", "all"), ("Pick 1 match", "one"), ("Pick N matches", "n")],
                    value="all",
                    id="count-mode",
                )
                yield Input(value="5", id="count-n", placeholder="N for Pick N")

                with Horizontal(classes="left-actions"):
                    yield Button("Preview Selection", id="preview", variant="default")
                    yield Button("Run", id="run", variant="success")

            with Vertical(id="right-pane"):
                with Vertical(id="preview-card", classes="right-card"):
                    yield Static("Run Preview", id="summary-title")
                    yield Static("Discover matches to begin.", id="run-summary")
                    with Horizontal(id="preview-actions"):
                        yield Button("Back To Selection", id="back-selection", variant="default")
                        yield Button("Confirm And Run", id="confirm-run", variant="success")

                with Vertical(id="selection-card", classes="right-card"):
                    yield Static("Select Matches", id="selection-title")
                    yield SelectionList(id="match-list")

                with Vertical(id="results-card", classes="right-card"):
                    yield Static("Gathered Stats", id="results-title")
                    yield OptionList(id="stat-tabs")
                    table = DataTable(id="results-table")
                    table.cursor_type = "row"
                    yield table
                    yield RichLog(id="run-log", wrap=True, highlight=True, markup=False)

        yield Footer()

    def on_mount(self) -> None:
        self._setup_results_table()
        self._build_tabs_from_selection()
        self._sync_mode_inputs()
        self._sync_lineup_flow()
        self._set_flow_state("config")

    def _set_right_mode(self, mode: str) -> None:
        preview_card = self.query_one("#preview-card", Vertical)
        selection_card = self.query_one("#selection-card", Vertical)
        results_card = self.query_one("#results-card", Vertical)
        preview_card.display = mode == "preview"
        selection_card.display = mode == "selection"
        results_card.display = mode == "results"

    def _set_flow_state(self, state: str) -> None:
        self._flow_state = state
        back_button = self.query_one("#back-selection", Button)
        confirm_button = self.query_one("#confirm-run", Button)
        if state == "config":
            self._set_right_mode("preview")
            self.query_one("#apply-match-view", Button).disabled = True
            self.query_one("#count-mode", Select).disabled = True
            self.query_one("#count-n", Input).disabled = True
            self.query_one("#match-list", SelectionList).disabled = True
            self.query_one("#preview", Button).disabled = True
            self.query_one("#run", Button).disabled = True
            back_button.disabled = True
            confirm_button.disabled = True
            return

        if state == "selection":
            self._set_right_mode("selection")
            self.query_one("#apply-match-view", Button).disabled = False
            self.query_one("#count-mode", Select).disabled = False
            self.query_one("#match-list", SelectionList).disabled = False
            self._sync_mode_inputs()
            self.query_one("#preview", Button).disabled = True
            self.query_one("#run", Button).disabled = True
            back_button.disabled = True
            confirm_button.disabled = True
            return

        if state == "preview":
            self._set_right_mode("preview")
            self.query_one("#apply-match-view", Button).disabled = False
            self.query_one("#count-mode", Select).disabled = False
            self.query_one("#match-list", SelectionList).disabled = False
            self._sync_mode_inputs()
            self.query_one("#preview", Button).disabled = False
            self.query_one("#run", Button).disabled = False
            back_button.disabled = False
            confirm_button.disabled = False
            return

        if state == "results":
            self._set_right_mode("results")
            self.query_one("#apply-match-view", Button).disabled = False
            self.query_one("#count-mode", Select).disabled = False
            self.query_one("#match-list", SelectionList).disabled = False
            self._sync_mode_inputs()
            back_button.disabled = False
            confirm_button.disabled = True

    def _setup_results_table(self) -> None:
        table = self.query_one("#results-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Team", "Position", "Total", "Average", "Highest")

    def _log(self, message: str) -> None:
        self.query_one("#run-log", RichLog).write(message)

    def _set_summary(self, text: str) -> None:
        self.query_one("#run-summary", Static).update(text)

    def _parse_min_average(self) -> float:
        raw = self.query_one("#min-average", Input).value.strip()
        try:
            return float(raw)
        except ValueError:
            return 1.0

    def _parse_count_n(self) -> int:
        raw = self.query_one("#count-n", Input).value.strip()
        try:
            return max(1, int(raw))
        except ValueError:
            return 1

    def _selected_stat_keys(self) -> list[str]:
        stats_widget = self.query_one("#stats-list", SelectionList)
        return [value for value in stats_widget.selected if value in CLI_STAT_MAPPING]

    def _build_tabs_from_selection(self) -> None:
        stat_keys = self._selected_stat_keys()
        if not stat_keys:
            self._selected_stats = []
            self._selected_display_stats = []
            self._selected_display_to_cli = {}
            self._current_stat = None
            tabs = self.query_one("#stat-tabs", OptionList)
            tabs.clear_options()
            self._render_selected_stat()
            return

        self._selected_stats = stat_keys
        self._selected_display_stats = [display_name_for_cli_key(key) for key in stat_keys]
        self._selected_display_to_cli = {display_name_for_cli_key(key): key for key in stat_keys}

        tabs = self.query_one("#stat-tabs", OptionList)
        tabs.clear_options()
        tabs.add_options(self._selected_display_stats)
        self._current_stat = self._selected_display_stats[0]
        self._render_selected_stat()

    def _render_selected_stat(self) -> None:
        table = self.query_one("#results-table", DataTable)
        table.clear()
        if not self._current_stat:
            return

        min_average = self._parse_min_average()
        rows: list[tuple[str, str, str, object, str]] = []
        for team, stats_dict in self._last_data.items():
            positions = list(stats_dict.get(self._current_stat, []))
            positions.sort(key=lambda pos: to_float(pos.get("average")), reverse=True)
            for position in positions:
                avg_val = to_float(position.get("average"))
                avg_text = str(int(avg_val)) if float(avg_val).is_integer() else f"{avg_val:.2f}"
                avg_cell = Text(avg_text, style="green" if avg_val >= min_average else "red")
                total_val = to_float(position.get("total"))
                high_val = to_float(position.get("highest"))
                total_text = str(int(total_val)) if float(total_val).is_integer() else f"{total_val:.2f}"
                high_text = str(int(high_val)) if float(high_val).is_integer() else f"{high_val:.2f}"
                rows.append((team, str(position.get("position", "")), total_text, avg_cell, high_text))

        for row in rows:
            table.add_row(*row)

    def _sort_matches(self, matches: list[dict], sort_mode: str) -> list[dict]:
        if sort_mode == "alpha":
            return sorted(matches, key=lambda m: f"{m.get('home_name', '')} vs {m.get('away_name', '')}")
        if sort_mode == "time":
            def _time_key(match: dict) -> tuple[int, int, str]:
                kickoff = match.get("kickoff_time") or ""
                if not kickoff:
                    return (99, 99, f"{match.get('home_name', '')} vs {match.get('away_name', '')}")
                try:
                    hour, minute = kickoff.split(":")
                    return (int(hour), int(minute), f"{match.get('home_name', '')} vs {match.get('away_name', '')}")
                except Exception:
                    return (99, 99, f"{match.get('home_name', '')} vs {match.get('away_name', '')}")
            return sorted(matches, key=_time_key)
        return matches

    def _filter_matches(self, matches: list[dict], query: str) -> list[dict]:
        if not query.strip():
            return matches
        q = query.strip().lower()
        return [
            m for m in matches
            if q in f"{m.get('home_name', '')} {m.get('away_name', '')}".lower()
        ]

    def _match_label(self, match: dict) -> str:
        kickoff = f" [{match.get('kickoff_time')}]" if match.get("kickoff_time") else ""
        return f"{match.get('home_name')} vs {match.get('away_name')}{kickoff}"

    def _refresh_match_list(self) -> None:
        if self._flow_state == "config":
            return
        filter_query = self.query_one("#team-filter", Input).value
        sort_mode = str(self.query_one("#sort-mode", Select).value or "none")
        visible = self._filter_matches(self._discovered_matches, filter_query)
        visible = self._sort_matches(visible, sort_mode)
        self._visible_matches = visible

        widget = self.query_one("#match-list", SelectionList)
        widget.clear_options()
        if not visible:
            self._set_summary("No matches available with current filter.")
            self._set_flow_state("selection")
            return

        options = [(self._match_label(match), str(match.get("match_url") or ""), False) for match in visible]
        widget.add_options(options)
        self._set_flow_state("selection")
        self._log(f"Match list updated: {len(visible)} visible.")

    def _selected_matches_for_run(self) -> tuple[list[dict] | None, str | None]:
        mode = str(self.query_one("#count-mode", Select).value or "all")
        selected_urls = set(self.query_one("#match-list", SelectionList).selected)
        selected = [m for m in self._visible_matches if str(m.get("match_url") or "") in selected_urls]

        if mode == "all":
            if not self._visible_matches:
                return None, "No visible matches. Discover and apply filters first."
            if selected:
                return selected, None
            return list(self._visible_matches), None

        if mode == "one":
            if len(selected) != 1:
                return None, "Pick exactly 1 match for 'Pick 1 match'."
            return selected, None

        required = self._parse_count_n()
        if len(selected) != required:
            return None, f"Pick exactly {required} matches for 'Pick N matches'."
        return selected, None

    def _sync_mode_inputs(self) -> None:
        count_mode = str(self.query_one("#count-mode", Select).value or "all")
        if self._flow_state == "config":
            self.query_one("#count-n", Input).disabled = True
        else:
            self.query_one("#count-n", Input).disabled = count_mode != "n"

        output_choice = str(self.query_one("#output-choice", Select).value or "terminal")
        self.query_one("#output-path", Input).disabled = output_choice == "terminal"

    def _sync_lineup_flow(self) -> None:
        has_lineups = bool(self.query_one("#has-lineups", Checkbox).value)
        note = self.query_one("#lineup-mode-note", Static)
        home_label = self.query_one("#home-lineup-label", Label)
        home_lineup = self.query_one("#home-lineup", Input)
        away_label = self.query_one("#away-lineup-label", Label)
        away_lineup = self.query_one("#away-lineup", Input)

        home_label.display = has_lineups
        home_lineup.display = has_lineups
        away_label.display = has_lineups
        away_lineup.display = has_lineups
        home_lineup.disabled = not has_lineups
        away_lineup.disabled = not has_lineups

        if has_lineups:
            note.update("Path: Confirmed lineups. Enter home and away lineup names.")
            return

        home_lineup.value = ""
        away_lineup.value = ""
        note.update("Path: No confirmed lineups. Collector will use non-lineup flow.")

    def _output_settings(self) -> tuple[str | None, bool]:
        choice = str(self.query_one("#output-choice", Select).value or "terminal")
        raw_path = self.query_one("#output-path", Input).value.strip()
        if choice == "terminal":
            return None, False

        if choice == "both":
            base = raw_path or "out.json"
            if not base.lower().endswith((".json", ".csv")):
                base += ".json"
            return base, True

        ext = ".json" if choice == "json" else ".csv"
        if not raw_path:
            return f"out{ext}", False
        if not raw_path.lower().endswith(ext):
            return raw_path + ext, False
        return raw_path, False

    def _output_path_for_match(self, base_output: str | None, match: dict, total_matches: int) -> str | None:
        if not base_output:
            return None
        if total_matches <= 1:
            return base_output
        path = Path(base_output)
        safe_name = re.sub(r"[^a-z0-9]+", "_", self._match_label(match).lower()).strip("_")
        if not path.suffix:
            return f"{base_output}_{safe_name}"
        return str(path.with_name(f"{path.stem}_{safe_name}{path.suffix}"))

    def _build_preview_text(self, chosen_matches: list[dict]) -> str:
        date_choice = str(self.query_one("#date-choice", Select).value or "today")
        sort_mode = str(self.query_one("#sort-mode", Select).value or "none")
        count_mode = str(self.query_one("#count-mode", Select).value or "all")
        has_lineups = bool(self.query_one("#has-lineups", Checkbox).value)
        min_average = self._parse_min_average()
        stats = ", ".join(self._selected_stat_keys()) or "(none)"
        output_path, output_both = self._output_settings()
        output_label = "terminal" if not output_path else ("both" if output_both else output_path)

        lines = [
            f"Date: {date_choice}",
            f"Sort: {sort_mode}",
            f"Count mode: {count_mode}",
            f"Headless: {bool(self.query_one('#headless', Checkbox).value)}",
            f"Confirmed lineups: {has_lineups}",
            f"Min average: {min_average}",
            f"Stats: {stats}",
            f"Output: {output_label}",
            f"Matches selected: {len(chosen_matches)}",
        ]
        lines.extend([f"- {self._match_label(match)}" for match in chosen_matches])
        return "\n".join(lines)

    def _refresh_preview_if_possible(self) -> None:
        if self._flow_state not in {"preview", "results", "selection"}:
            return
        chosen_matches, error = self._selected_matches_for_run()
        if error or not chosen_matches:
            return
        self._set_summary(self._build_preview_text(chosen_matches))

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "has-lineups":
            self._sync_lineup_flow()
            self._refresh_preview_if_possible()
            return
        if event.checkbox.id == "headless":
            self.default_headless = bool(event.value)
            self._refresh_preview_if_possible()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id in {"count-mode", "output-choice"}:
            self._sync_mode_inputs()
        if event.select.id in {"date-choice", "output-choice", "sort-mode", "count-mode"}:
            self._refresh_preview_if_possible()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id in {"min-average", "output-path", "count-n", "home-lineup", "away-lineup"}:
            self._refresh_preview_if_possible()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "back-selection":
            if self._discovered_matches:
                self._set_flow_state("selection")
            return

        if button_id == "confirm-run":
            button_id = "run"

        if button_id == "discover-matches":
            date_choice = str(self.query_one("#date-choice", Select).value or "today")
            self.default_headless = bool(self.query_one("#headless", Checkbox).value)
            self._log(f"Discovering matches for {date_choice}...")
            try:
                matches = await asyncio.to_thread(discover_matches, date_choice, self.default_headless)
            except Exception as exc:
                self._log(f"ERROR discovering matches: {exc}")
                return
            self._discovered_matches = matches
            self._visible_matches = list(matches)
            if not matches:
                self._set_summary("No matches found.")
                self._log("No matches found.")
                self._set_flow_state("config")
                return
            self._set_flow_state("selection")
            self._refresh_match_list()
            self._set_summary(f"Discovered {len(matches)} matches. Apply filters, choose selection mode, then preview.")
            return

        if button_id == "apply-match-view":
            if self._flow_state == "config":
                self._set_summary("Discover matches first.")
                return
            self._refresh_match_list()
            return

        if button_id == "preview":
            if self._flow_state == "config":
                self._set_summary("Discover and select matches first.")
                return
            chosen_matches, error = self._selected_matches_for_run()
            if error:
                self._set_summary(error)
                self._log(f"ERROR: {error}")
                self._set_flow_state("selection")
                return
            if not chosen_matches:
                self._set_summary("No matches selected.")
                self._set_flow_state("selection")
                return
            self._set_summary(self._build_preview_text(chosen_matches))
            self._set_flow_state("preview")
            return

        if button_id != "run":
            return

        if self._flow_state != "preview":
            self._set_summary("Preview selection first, then run.")
            self._set_flow_state("selection")
            return
        chosen_matches, error = self._selected_matches_for_run()
        if error:
            self._log(f"ERROR: {error}")
            self._set_flow_state("selection")
            return
        if not chosen_matches:
            self._log("ERROR: No matches selected.")
            self._set_flow_state("selection")
            return

        stat_keys = self._selected_stat_keys()
        if not stat_keys:
            self._log("ERROR: Select at least one stat.")
            return

        has_lineups = bool(self.query_one("#has-lineups", Checkbox).value)
        home_positions = None
        away_positions = None
        if has_lineups:
            home_lineup = self.query_one("#home-lineup", Input).value.strip()
            away_lineup = self.query_one("#away-lineup", Input).value.strip()
            home_positions = get_lineup_positions(home_lineup)
            away_positions = get_lineup_positions(away_lineup)
            if not home_positions or not away_positions:
                lineup_list = ", ".join(sorted(LINEUP_POSITIONS.keys()))
                self._log("ERROR: Unknown lineup. Supported: " + lineup_list)
                return

        min_average = self._parse_min_average()
        base_output, output_both = self._output_settings()

        run_button = self.query_one("#run", Button)
        run_button.disabled = True
        self._log(f"Starting collection for {len(chosen_matches)} match(es)...")
        self._set_flow_state("results")

        try:
            for index, match in enumerate(chosen_matches, start=1):
                match_url = str(match.get("match_url") or "")
                if not match_url:
                    self._log("ERROR: One selected match has no URL; skipping.")
                    continue
                self._log(f"[{index}/{len(chosen_matches)}] {self._match_label(match)}")
                per_match_output = self._output_path_for_match(base_output, match, len(chosen_matches))
                result = await asyncio.to_thread(
                    collect_data,
                    match_url,
                    stat_keys,
                    min_average,
                    has_lineups,
                    home_positions,
                    away_positions,
                    self.default_headless,
                    per_match_output,
                    output_both,
                )
                self._last_data = result
                self._build_tabs_from_selection()
                self._set_right_mode("results")
                if per_match_output:
                    self._log(f"Saved: {per_match_output}")
            self._log("Collection completed.")
        except Exception as exc:
            self._log(f"ERROR: {exc}")
        finally:
            run_button.disabled = False

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "stat-tabs":
            return
        self._current_stat = str(event.option.prompt)
        self._render_selected_stat()

    def on_selection_list_selected_changed(self, event: SelectionList.SelectedChanged) -> None:
        if event.selection_list.id == "stats-list":
            self._build_tabs_from_selection()
            self._refresh_preview_if_possible()
            return
        if event.selection_list.id != "match-list":
            return
        if self._flow_state == "config":
            return
        selected_count = len(event.selection_list.selected)
        count_mode_widget = self.query_one("#count-mode", Select)
        target_mode = "all"
        if selected_count == 1:
            target_mode = "one"
        elif selected_count > 1:
            target_mode = "n"
            self.query_one("#count-n", Input).value = str(selected_count)

        current_mode = str(count_mode_widget.value or "all")
        if current_mode != target_mode:
            count_mode_widget.value = target_mode

        chosen_matches, error = self._selected_matches_for_run()
        if error:
            self._set_summary(error)
            self._set_flow_state("selection")
            return
        if not chosen_matches:
            self._set_summary("No matches selected.")
            self._set_flow_state("selection")
            return
        self._set_summary(self._build_preview_text(chosen_matches))
        self._set_flow_state("preview")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="StatsHub TUI")
    parser.add_argument("--headed", action="store_true", help="Run browser with UI")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = StatsHubTUI(headless=not args.headed)
    app.run()
