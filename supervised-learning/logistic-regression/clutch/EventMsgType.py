
from enum import IntEnum

class EventMsgType(IntEnum):
    FIELD_GOAL_MADE = 1
    FIELD_GOAL_MISSED = 2
    FREE_THROW = 3
    REBOUND = 4
    TURNOVER = 5
    # FOUL = 6 # Think about how to get home vs away possession
    # VIOLATION = 7 # Think about how to get home vs away possession
    # TIMEOUT = 9 # TODO: NEEDED?

    @classmethod
    def has_event(cls, event):
        return event in cls._value2member_map_

    @classmethod
    def non_rebound_event(cls, event):
        if event != cls.REBOUND:
            return True
        return False