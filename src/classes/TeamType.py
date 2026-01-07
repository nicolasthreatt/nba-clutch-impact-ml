from enum import IntEnum


class TeamType(IntEnum):
    HOME = 1
    AWAY = 0

    def flip(self) -> "TeamType":
        return TeamType.AWAY if self == TeamType.HOME else TeamType.HOME
