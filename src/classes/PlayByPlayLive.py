import math

from typing import Any, Dict, Optional

from src.classes.EventMsgType import EventMsgType
from src.classes.TeamType import TeamType


class PlayByPlayLive:
    def __init__(self, game_id: str, home_team_id: int, action: Dict[str, Any]):
        self.game_id = game_id
        self.season = game_id[3:5]
        self.action_number = action.get("actionNumber")
        self.pc_time = self._convert_clock_to_seconds(action.get("clock"))
        self.period = action.get("period")
        self.team_id = action.get("teamId")
        self.event_team = TeamType(self.team_id == home_team_id)
        self.possession_team = TeamType(self.team_id == home_team_id == action.get("possession"))
        self.event_msg_type = self._determine_event_msg_type(action.get("actionType"), action.get("shotResult"))
        self.event_msg_action_type = action.get("subType")
        self.person_id = action.get("personId")
        # self.assistPersonId = action.get("assistPersonId")  # TODO: IMPLEMENT EVENT_MSG_TYPE
        # self.stealPersonId = action.get("stealPersonId")    # TODO: IMPLEMENT EVENT_MSG_TYPE
        # self.blockPersonId = action.get("blockPersonId")    # TODO: IMPLEMENT EVENT_MSG_TYPE
        self.points_total = action.get("pointsTotal")
        self.score_home = int(action["scoreHome"]) if action.get("scoreHome") is not None else None
        self.score_away = int(action["scoreAway"]) if action.get("scoreAway") is not None else None
        self.score_margin = 0
        if self.score_home and self.score_away:
            self.score_margin = self.score_home - self.score_away
        self.player_name = action.get("playerName")

    def _convert_clock_to_seconds(self, clock: str) -> Optional[int]:
        if not clock:
            return None

        if clock.startswith("PT") and clock.endswith("S"):  # PTMMSS.SS
            try:
                minutes, seconds = clock[2:-1].split("M")  # Remove "PT" and Trailing "S"
                return int(minutes) * 60 + math.floor(float(seconds))
            except (ValueError, IndexError):
                return None

        if ":" in clock:  # MM:SS
            try:
                minutes, seconds = map(int, clock.split(":"))
                return minutes * 60 + seconds
            except ValueError:
                return None

        return None

    def _determine_event_msg_type(self, action_type: str, shot_result: str) -> Optional[str]:
        if not action_type:
            return None

        action_type = action_type.lower()
    
        if action_type in ("2pt", "3pt"):
            return EventMsgType.FIELD_GOAL_MADE if shot_result == "Made" else EventMsgType.FIELD_GOAL_MISSED

        elif action_type == "freethrow":
            return EventMsgType.FREE_THROW_MADE if shot_result == "Made" else EventMsgType.FREE_THROW_MISSED

        elif action_type == "rebound":
            return EventMsgType.REBOUND

        elif action_type in ("steal", "turnover"):
            return EventMsgType.TURNOVER

        return None
