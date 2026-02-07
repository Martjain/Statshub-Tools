from dataclasses import dataclass


POSITIONS = [
    "GK",
    "RB",
    "RWB",
    "RCB",
    "CB",
    "LCB",
    "LB",
    "LWB",
    "CDM",
    "RCDM",
    "LCDM",
    "RCM",
    "CM",
    "LCM",
    "RM",
    "LM",
    "CAM",
    "RW",
    "LW",
    "RF",
    "LF",
    "ST",
    "RST",
    "LST",
]

LINEUP_POSITIONS = {
    "3-4-3": ["LCB", "CB", "RCB", "RWB", "RCM", "LCM", "LWB", "RW", "ST", "LW"],
    "3-4-1-2": [
        "RCB",
        "CB",
        "LCB",
        "RWB",
        "RCDM",
        "LCDM",
        "LWB",
        "CAM",
        "RST",
        "LST",
    ],
    "3-4-2-1": ["RCB", "CB", "LCB", "RWB", "RCM", "LCM", "LWB", "RF", "LF", "ST"],
    "3-5-2": ["RCB", "CB", "LCB", "RWB", "RCM", "CM", "LCM", "LWB", "RST", "LST"],
    "3-1-4-2": ["RCB", "CB", "LCB", "CDM", "RWB", "RCM", "LCM", "LWB", "RST", "LST"],
    "3-5-1-1": ["RCB", "CB", "LCB", "RWB", "RCDM", "CM", "LCDM", "LWB", "CF", "ST"],
    "4-3-3": ["RB", "CB", "CB", "LB", "RCM", "CM", "LCM", "RW", "ST", "LW"],
    "4-1-4-1": ["RB", "RCB", "LCB", "LB", "CDM", "RM", "RCM", "LCM", "LM", "ST"],
    "4-2-2-2": ["RB", "RCB", "LCB", "LB", "RCDM", "LCDM", "RCAM", "LCAM", "RST", "LST"],
    "4-4-2": ["RB", "RCB", "LCB", "LB", "RM", "RCM", "LCM", "LM", "RST", "LST"],
    "4-2-3-1": ["RB", "RCB", "LCB", "LB", "RCDM", "LCDM", "RW", "CAM", "LW", "ST"],
    "4-3-2-1": ["RB", "RCB", "LCB", "LB", "RCM", "CM", "LCM", "CAM", "RST", "LST"],
    "4-1-3-2": ["RB", "RCB", "LCB", "LB", "CDM", "RM", "CM", "LM", "RST", "LST"],
    "5-3-2": ["RWB", "RCB", "CB", "LCB", "LWB", "RCM", "CM", "LCM", "RST", "LST"],
    "5-4-1": ["RWB", "RCB", "CB", "LCB", "LWB", "RM", "RCM", "LCM", "LM", "ST"],
}


def normalize_lineup_name(lineup_name: str) -> str:
    return "-".join(lineup_name.strip().lower().split())


def get_lineup_positions(lineup_name: str) -> list[str] | None:
    normalized = normalize_lineup_name(lineup_name)
    positions = LINEUP_POSITIONS.get(normalized)
    if not positions:
        return None
    return ["GK", *positions]


def _validate_lineups() -> None:
    allowed_lineup_positions = set(POSITIONS) | {"CF", "RCAM", "LCAM"}
    for lineup, positions in LINEUP_POSITIONS.items():
        if len(positions) != 10:
            raise ValueError(
                f"Lineup '{lineup}' must have exactly 10 outfield positions, got {len(positions)}."
            )
        for pos in positions:
            if pos not in allowed_lineup_positions:
                raise ValueError(
                    f"Lineup '{lineup}' includes unsupported position '{pos}'."
                )


_validate_lineups()


DEFAULT_STATS = [
    "wasFouled",
    "fouls",
    "totalTackle",
    "shots",
    "onTargetScoringAttempt",
]


STAT_DISPLAY_NAMES = {
    "totalTackle": "Tackles",
    "fouls": "Fouls Committed",
    "wasFouled": "Fouls Won",
    "shots": "Shots",
    "onTargetScoringAttempt": "Shots on Target",
    "goals": "Goals",
    "goalAssist": "Assists",
    "scoredOrAssisted": "Scored or Assisted",
    "totalPass": "Total Passes",
    "yellowCard": "Yellow Cards",
    "dispossessed": "Dispossessed",
}


CLI_STAT_MAPPING = {
    "tackles": "totalTackle",
    "fouls-won": "wasFouled",
    "fouls-committed": "fouls",
    "shots": "shots",
    "shots-on-target": "onTargetScoringAttempt",
    "goals": "goals",
    "assists": "goalAssist",
    "scored-or-assisted": "scoredOrAssisted",
    "total-passes": "totalPass",
    "yellow-cards": "yellowCard",
    "dispossessed": "dispossessed",
    "fouls_won": "wasFouled",
    "fouls_committed": "fouls",
    "shots_on_target": "onTargetScoringAttempt",
    "scored_or_assisted": "scoredOrAssisted",
    "total_passes": "totalPass",
    "yellow_cards": "yellowCard",
}


DEFAULT_MATCH_NAME = "14:00 Deportivo Alavés"
DEFAULT_HOME_TEAM = "Deportivo Alavés Deportivo"
DEFAULT_AWAY_TEAM = "Real Sociedad Real Sociedad"


@dataclass(frozen=True)
class MatchEntry:
    match_url: str
    home_team_tab: str
    away_team_tab: str
    match_id: str | None = None
