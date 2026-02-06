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
