from dataclasses import dataclass
from src.classes.TeamType import TeamType


@dataclass
class TeamGameInfo:
    is_home_team: TeamType
    is_home_win: int
