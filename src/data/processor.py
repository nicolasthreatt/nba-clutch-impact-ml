import logging
import pandas as pd

from typing import Any, Dict, List, Optional

from src.api.api import API
from src.data.storage import SQLiteStorage
from src.classes.EventMsgType import EventMsgType
from src.classes.Game import Game
from src.classes.PlayByPlay import PlayByPlay
from src.classes.TeamGameInfo import TeamGameInfo
from src.classes.TeamType import TeamType

logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes NBA Play-By-Play data and extracts clutch events."""
    def __init__(self):
        self.api = API()
        self._storage: Optional[SQLiteStorage] = None
        self.clutch_period = 4
        self.clutch_seconds = 300
        self.clutch_margin = 5

    @property
    def storage(self) -> SQLiteStorage:
        if self._storage is None:
            self._storage = SQLiteStorage()
        return self._storage

    def get_or_create_clutch_events(
        self,
        season: str,
        refresh: bool = False,
        dry_run: bool = False,
    ) -> pd.DataFrame:
        """Load cached clutch events or fetch them, optionally skipping persistence."""
        if not refresh and self.storage.has_clutch_events(season):
            logger.info("Loading cached clutch events for season=%s from SQLite", season)
            return self.storage.load_clutch_events(season)

        logger.info("Fetching clutch events for season=%s from NBA API", season)
        df = self._fetch_clutch_events(season)
        if df.empty:
            logger.warning("No clutch events found for season=%s", season)
            return df

        if dry_run:
            logger.info("Dry run enabled; skipping SQLite save for season=%s", season)
            return df

        rows = self.storage.save_clutch_events(df, replace_season=refresh)
        logger.info("Saved %s clutch events for season=%s to SQLite", rows, season)
        return df

    def _fetch_clutch_events(self, season: str) -> pd.DataFrame:
        """Fetch and transform clutch play-by-play events for a given season."""
        data = self.api.load_season_games(season)
        if not data:
            return pd.DataFrame()

        clutch_plays: List[Dict[str, Any]] = []

        games = self._transform_game_data(data)
        pbp = self.api.load_play_by_play_games(game_ids=sorted(games.keys()), delay=1.5)

        for game_id, pbp_data in pbp.items():
            if pbp_data is None:
                continue

            teams = games[game_id]
            plays = self._transform_pbp_data(pbp_data, teams)

            if plays:
                clutch_plays.extend(plays)

        return pd.DataFrame(clutch_plays)

    def _is_clutch(self, play: PlayByPlay) -> bool:
        """Last 5 minutes of 4th quarter or OT, where score margin is at most 5 points."""
        return (
            play.score_margin is not None
            and play.period >= self.clutch_period
            and play.pc_time <= self.clutch_seconds
            and abs(play.score_margin) <= self.clutch_margin
        )

    def _get_possession_team(
        self,
        previous: Optional[PlayByPlay],
        play: PlayByPlay,
        is_home_team: TeamType
    ) -> Optional[TeamType]:
        """Determines which team has possession for the play."""

        action_type = play.event_msg_action_type or ""

        offensive_events = {
            EventMsgType.ASSIST,
            EventMsgType.FIELD_GOAL_MADE,
            EventMsgType.FIELD_GOAL_MISSED,
            EventMsgType.FREE_THROW,
            EventMsgType.TURNOVER,
        }

        defensive_events = {
            EventMsgType.BLOCK,
            EventMsgType.STEAL,
        }

        if play.event_msg_type in offensive_events:
            return is_home_team

        if play.event_msg_type in defensive_events:
            return is_home_team.flip()

        if play.event_msg_type == EventMsgType.FOUL:
            offensive_fouls = {
                "Away From Play",
                "Double Personal",
                "Loose Ball",
                "Transition Take",
            }
            if (
                action_type in offensive_fouls or
                "Flagrant" in action_type or
                "Offense" in action_type or
                "Offensive" in action_type or 
                "Technical" in action_type
            ):
                return is_home_team

            defensive_fouls = {
                "Clear Path",
                "Personal",
                "Personal Take",
                "Shooting",
            }
            if (
                action_type in defensive_fouls or
                "Defense" in action_type or
                "Defensive" in action_type
            ):
                return is_home_team.flip()

        if play.event_msg_type == EventMsgType.REBOUND:
            if previous is None or previous.team_id is None:
                logger.debug("Skipping rebound: previous missing for play=%s", vars(play))
                return None
            is_offensive = previous.team_id == play.team_id
            return is_home_team if is_offensive else is_home_team.flip()

        if play.event_msg_type == EventMsgType.VIOLATION:
            is_defensive = "Defensive" in action_type
            return is_home_team.flip() if is_defensive else is_home_team

        return None

    def _is_valid(self, play: PlayByPlay) -> bool:
        """Checks whether a play has missing data."""
        return (
            play.player_id is not None
            and play.team_id is not None
            and play.period is not None
            and play.pc_time is not None
            and play.score_margin is not None
            and play.event_msg_type not in (None, EventMsgType.INVALID,)
        )

    def _transform_game_data(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Dict[str, TeamGameInfo]]:
        """Transform leaguegamefinder data into a nested game dictionary."""

        games: Dict[str, Dict[str, TeamGameInfo]] = {}  # {game_id: {team_id: TeamGameInfo}}

        for result in data.get("resultSets", [{}])[0].get("rowSet", []):
            game = Game(result)

            game_id = game.game_id
            team_id = game.team_id

            if game_id not in games:
                games[game_id] = {}

            is_home_team = "vs." in game.matchup
            is_home_win = game.wl == "W" if is_home_team else game.wl == "L"

            games[game_id][team_id] = TeamGameInfo(TeamType(is_home_team), is_home_win)

        return games

    def _transform_pbp_data(
        self,
        data: Dict[str, Any],
        teams: Dict[str, TeamGameInfo]
    ) -> List[Dict[str, Any]]:
        """Transforms the play-by-play data into a list of clutch event dictionaries."""

        plays: List[Dict[str, Any]] = []
        previous: Optional[PlayByPlay] = None

        game = data.get("game", {})
        actions = game.get("actions", [])

        for action in actions:
            play = PlayByPlay.from_action(action, game.get("gameId"))
            scores = (play.away_score, play.home_score, play.total_score)

            if isinstance(previous, PlayByPlay) and None in scores:
                play._update_scores(
                    previous.away_score,
                    previous.home_score,
                    previous.total_score,
                )

            team_info = teams.get(play.team_id)
            if (
                self._is_valid(play) and
                self._is_clutch(play) and
                isinstance(team_info, TeamGameInfo)
            ):
                play.set_event_team(team_info.is_home_team)
                play.set_possession_team(
                    self._get_possession_team(previous, play, team_info.is_home_team)
                )
                play.set_home_win(team_info.is_home_win)

                plays.append(vars(play))

            previous = play

        return plays
