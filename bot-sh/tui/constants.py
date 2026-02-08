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
    background: #0a1018;
    color: #d8e4ef;
}

#body {
    height: 1fr;
    padding: 1 2;
}

#left-pane {
    width: 44;
    min-width: 38;
    border: heavy #2f4f6f;
    background: #0f1d2d;
    padding: 1 2;
    margin-right: 1;
    overflow-y: auto;
}

#right-pane {
    width: 1fr;
    border: heavy #2f4f6f;
    background: #0d1724;
    padding: 1 2;
}

#options-title, #summary-title, #selection-title, #results-title {
    text-style: bold;
    color: #7dc3ff;
    margin-bottom: 1;
}

#stats-list {
    height: 10;
    border: round #34506b;
    margin-bottom: 1;
    background: #0b1623;
}

#match-list {
    height: 1fr;
    border: round #34506b;
    margin-bottom: 1;
    background: #0b1623;
}

#run-summary {
    border: round #34506b;
    background: #0b1623;
    color: #d6e8ff;
    height: 1fr;
    padding: 1;
    margin-bottom: 1;
}

#stat-tabs {
    height: 5;
    border: round #34506b;
    margin-bottom: 1;
    background: #0b1623;
}

#results-table {
    height: 1fr;
    border: round #34506b;
    background: #0b1623;
}

#run-log {
    height: 10;
    border: round #34506b;
    background: #0b1623;
    margin-top: 1;
}

#preview-card, #selection-card, #results-card {
    height: 1fr;
    border: round #34506b;
    background: #0e1c2b;
    padding: 1;
}

#preview-actions {
    height: auto;
}

#preview-actions Button {
    margin-right: 1;
}

.field-label {
    margin-top: 1;
    text-style: bold;
    color: #95c3ea;
}

.field-sub-label {
    margin-top: 1;
    color: #8ab4d8;
}

.left-actions {
    margin-top: 1;
    height: auto;
}

Select, Input {
    width: 1fr;
    margin-bottom: 1;
}

Button {
    margin-bottom: 1;
}

Checkbox {
    margin-bottom: 1;
}
"""
