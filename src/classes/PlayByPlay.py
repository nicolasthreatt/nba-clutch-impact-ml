import math
from typing import Optional

from src.classes.EventMsgType import EventMsgType


class PlayByPlay:
    def __init__(self):
        self.home_possession = None
        self.home_win = None

    @classmethod
    def from_action(cls, action: dict, game_id: str):
        play = cls()

        # Game Information
        play.game_id = game_id
        play.season = game_id[3:5]

        # Team
        play.team_id = action.get("teamId")

        # Player
        play.player_id = action.get("personId")
        play.player_name = action.get("playerName")

        # Time
        play.period = int(action.get("period", 0))
        play.pc_time = play._convert_clock_to_seconds(action.get("clock"))

        # Event Infomation
        play.description = action.get("description")
        play.event_num = action.get("actionNumber")
        play.action_type = action.get("actionType")
        play.event_msg_type = EventMsgType.from_action_type(play.action_type)
        play.event_msg_action_type = action.get("subType")

        # Block Edge Case
        if play._is_block():
            play.action_type = "Block"
            play.event_msg_type = EventMsgType.BLOCK

        # Steal Edge Case
        if play._is_steal():
            play.action_type = "Steal"
            play.event_msg_type = EventMsgType.STEAL

        # Scores
        home_score = action.get("scoreHome")
        away_score = action.get("scoreAway")
        total_score = action.get("pointsTotal")
        play._set_scores(away_score, home_score, total_score)

        return play

    def set_home_possession(self, home_possession: int):
        self.home_possession = home_possession

    def set_home_win(self, home_win: int):
        self.home_win = home_win

    def _convert_clock_to_seconds(self, clock: Optional[str]) -> Optional[int]:
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

    def _is_assist(self) -> bool:
        return self.event_msg_type == EventMsgType.FIELD_GOAL_MADE and "AST" in self.description

    def _is_block(self) -> bool:
        return self.event_msg_type is None and "BLOCK" in self.description

    def _is_steal(self) -> bool:
        return self.event_msg_type is None and "STEAL" in self.description

    def _safe_int(self, value: str) -> Optional[int]:
        try:
            return int(value) if isinstance(value, str) and value != '' else None
        except (TypeError, ValueError):
            return None

    def _set_scores(self, away_score: str, home_score: str, total_score: str):
        self.away_score = self._safe_int(away_score)
        self.home_score = self._safe_int(home_score)
        self.total_score = self._safe_int(total_score)

        self.score_margin = None
        if self.home_score is not None and self.away_score is not None:
            self.score_margin = self.home_score - self.away_score

    def _update_scores(self, away: int, home: int, total: int):
        if self.away_score is None:
            self.away_score = away

        if self.home_score is None:
            self.home_score = home

        if self.total_score is None:
            self.total_score = total

        if self.home_score is not None and self.away_score is not None:
            self.score_margin = self.home_score - self.away_score
