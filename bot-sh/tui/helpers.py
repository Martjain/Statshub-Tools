"""Helper utilities for TUI formatting and mapping."""

from __future__ import annotations

from bot_sh.models import CLI_STAT_MAPPING, STAT_DISPLAY_NAMES


def to_float(value: object) -> float:
    try:
        if value is None or value == "":
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def display_name_for_cli_key(cli_key: str) -> str:
    internal = CLI_STAT_MAPPING.get(cli_key, cli_key)
    return STAT_DISPLAY_NAMES.get(internal, cli_key)
