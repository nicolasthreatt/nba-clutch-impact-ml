from enum import Enum

class EventMsgType(str, Enum):
    ASSIST = "Assist"
    BLOCK =  "Block"
    FIELD_GOAL_MADE = "Made Shot"
    FIELD_GOAL_MISSED = "Missed Shot"
    FOUL = "Foul"
    FREE_THROW = "Free Throw"
    REBOUND = "Rebound"
    STEAL = "Steal"
    TURNOVER = "Turnover"
    VIOLATION = "Violation"

    @classmethod
    def has_event(cls, event: str) -> bool:
        return event in cls._value2member_map_
