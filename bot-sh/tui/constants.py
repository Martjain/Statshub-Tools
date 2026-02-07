"""Constants used by the Textual TUI."""

from __future__ import annotations

STAT_CHOICES: list[tuple[str, str]] = [
    ("tackles", "Tackles"),
    ("fouls-won", "Fouls Won"),
    ("fouls-committed", "Fouls Committed"),
    ("shots", "Shots"),
    ("shots-on-target", "Shots on Target"),
    ("goals", "Goals"),
    ("assists", "Assists"),
    ("scored-or-assisted", "Scored or Assisted"),
    ("total-passes", "Total Passes"),
    ("yellow-cards", "Yellow Cards"),
    ("dispossessed", "Dispossessed"),
]

TUI_CSS = """
Screen {
    layout: vertical;
}

#body {
    height: 1fr;
}

#left-pane {
    width: 38;
    min-width: 32;
    border: round #666666;
    padding: 1;
}

#right-pane {
    width: 1fr;
    border: round #666666;
    padding: 1;
}

#options-title, #results-title {
    text-style: bold;
    margin-bottom: 1;
}

#stats-list {
    height: 12;
    border: round #555555;
    margin-bottom: 1;
}

#match-list {
    height: 8;
    border: round #555555;
    margin-bottom: 1;
}

#date-choice {
    width: 18;
}

#stat-tabs {
    height: 5;
    border: round #555555;
    margin-bottom: 1;
}

#results-table {
    height: 1fr;
    border: round #555555;
    margin-bottom: 1;
}

#run-log {
    height: 10;
    border: round #555555;
}

.field-label {
    margin-top: 1;
}

.left-actions {
    margin-top: 1;
}
"""
