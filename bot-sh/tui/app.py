"""Textual app module for StatsHub TUI."""

from __future__ import annotations

import argparse
import asyncio

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
        self._selected_match: dict | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="body"):
            with Vertical(id="left-pane"):
                yield Static("Options", id="options-title")
                yield Label("Date", classes="field-label")
                yield Select(
                    [("Today", "today"), ("Tomorrow", "tomorrow")],
                    value="today",
                    id="date-choice",
                )
                yield Button("Discover Matches", id="discover-matches", variant="primary")

                yield Label("Discovered matches", classes="field-label")
                yield OptionList(id="match-list")

                yield Label("Min Average", classes="field-label")
                yield Input(value="1.0", id="min-average")

                yield Checkbox("Confirmed lineups", id="has-lineups", value=False)
                yield Label("Home lineup", classes="field-label")
                yield Input(placeholder="4-2-3-1", id="home-lineup", disabled=True)

                yield Label("Away lineup", classes="field-label")
                yield Input(placeholder="4-3-3", id="away-lineup", disabled=True)

                yield Label("Stats", classes="field-label")
                yield SelectionList(*[(label, key, True) for key, label in STAT_CHOICES], id="stats-list")

                with Horizontal(classes="left-actions"):
                    yield Button("Build Tabs", id="build-tabs", variant="default")
                    yield Button("Run", id="run", variant="success")

            with Vertical(id="right-pane"):
                yield Static("Results", id="results-title")
                yield OptionList(id="stat-tabs")
                table = DataTable(id="results-table")
                table.cursor_type = "row"
                yield table
                yield RichLog(id="run-log", wrap=True, highlight=True, markup=False)

        yield Footer()

    def on_mount(self) -> None:
        self._setup_results_table()
        self._build_tabs_from_selection()

    def _setup_results_table(self) -> None:
        table = self.query_one("#results-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Team", "Position", "Total", "Average", "Highest")

    def _log(self, message: str) -> None:
        self.query_one("#run-log", RichLog).write(message)

    def _parse_min_average(self) -> float:
        raw = self.query_one("#min-average", Input).value.strip()
        try:
            return float(raw)
        except ValueError:
            return 1.0

    def _selected_stat_keys(self) -> list[str]:
        stats_widget = self.query_one("#stats-list", SelectionList)
        selected = []
        for value in stats_widget.selected:
            if value in CLI_STAT_MAPPING:
                selected.append(value)
        return selected

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

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id != "has-lineups":
            return
        enabled = bool(event.value)
        home_lineup = self.query_one("#home-lineup", Input)
        away_lineup = self.query_one("#away-lineup", Input)
        home_lineup.disabled = not enabled
        away_lineup.disabled = not enabled
        if not enabled:
            home_lineup.value = ""
            away_lineup.value = ""

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "discover-matches":
            date_choice = str(self.query_one("#date-choice", Select).value or "today")
            self._log(f"Discovering matches for {date_choice}...")
            try:
                matches = await asyncio.to_thread(discover_matches, date_choice, self.default_headless)
            except Exception as exc:
                self._log(f"ERROR discovering matches: {exc}")
                return
            self._discovered_matches = matches
            self._selected_match = None
            match_list = self.query_one("#match-list", OptionList)
            match_list.clear_options()
            if not matches:
                self._log("No matches found.")
                return
            labels = []
            for match in matches:
                kickoff = f" [{match['kickoff_time']}]" if match.get("kickoff_time") else ""
                labels.append(f"{match.get('home_name')} vs {match.get('away_name')}{kickoff}")
            match_list.add_options(labels)
            self._log(f"Discovered {len(matches)} matches.")
            return

        if event.button.id == "build-tabs":
            self._build_tabs_from_selection()
            self._log("Tabs updated from selected stats.")
            return

        if event.button.id != "run":
            return

        if not self._selected_match:
            self._log("ERROR: Discover and select a match first.")
            return
        match_url = str(self._selected_match.get("match_url") or "")
        if not match_url:
            self._log("ERROR: Selected match has no URL.")
            return

        stat_keys = self._selected_stat_keys()
        if not stat_keys:
            self._log("ERROR: Select at least one stat.")
            return

        has_lineups = self.query_one("#has-lineups", Checkbox).value
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
        run_button = self.query_one("#run", Button)
        run_button.disabled = True
        self._log("Starting collection...")

        try:
            result = await asyncio.to_thread(
                collect_data,
                match_url,
                stat_keys,
                min_average,
                bool(has_lineups),
                home_positions,
                away_positions,
                self.default_headless,
            )
        except Exception as exc:
            self._log(f"ERROR: {exc}")
            run_button.disabled = False
            return

        self._last_data = result
        self._build_tabs_from_selection()
        self._log("Collection completed.")
        run_button.disabled = False

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "match-list":
            index = event.option_index
            if index < 0 or index >= len(self._discovered_matches):
                return
            self._selected_match = self._discovered_matches[index]
            self._log(
                "Selected match: "
                + f"{self._selected_match.get('home_name')} vs {self._selected_match.get('away_name')}"
            )
            return

        if event.option_list.id != "stat-tabs":
            return
        self._current_stat = str(event.option.prompt)
        self._render_selected_stat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="StatsHub TUI")
    parser.add_argument("--headed", action="store_true", help="Run browser with UI")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = StatsHubTUI(headless=not args.headed)
    app.run()
