from enum import Enum


class EventMsgType(str, Enum):
    INVALID = "Invalid"

    ASSIST = "Assist"
    BLOCK = "Block"
    FIELD_GOAL_MADE = "Made Shot"
    FIELD_GOAL_MISSED = "Missed Shot"
    FOUL = "Foul"
    FREE_THROW = "Free Throw"
    FREE_THROW_MADE = "Made Free Throw"
    FREE_THROW_MISSED = "Missed Free Throw"
    REBOUND = "Rebound"
    STEAL = "Steal"
    TURNOVER = "Turnover"
    VIOLATION = "Violation"

    @classmethod
    def from_action_type(cls, action_type: str) -> "EventMsgType":
        if not action_type:
            return cls.INVALID
        return cls(action_type) if action_type in cls._value2member_map_ else cls.INVALID
