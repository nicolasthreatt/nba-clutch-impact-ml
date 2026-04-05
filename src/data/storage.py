import sqlite3

from pathlib import Path
from typing import Any, Optional

import pandas as pd


class SQLiteStorage:
    """SQLite-backed storage for clutch event datasets."""

    DB_PATH = Path("data/nba_clutch.sqlite")
    CLUTCH_EVENTS_TABLE = "clutch_events"
    CLUTCH_EVENT_COLUMNS = [
        ("game_id", "TEXT NOT NULL"),
        ("event_num", "INTEGER NOT NULL"),
        ("season", "TEXT NOT NULL"),
        ("team_id", "INTEGER"),
        ("player_id", "INTEGER"),
        ("player_name", "TEXT"),
        ("period", "INTEGER"),
        ("pc_time", "INTEGER"),
        ("event_msg_type", "TEXT"),
        ("event_msg_action_type", "TEXT"),
        ("away_score", "INTEGER"),
        ("home_score", "INTEGER"),
        ("total_score", "INTEGER"),
        ("score_margin", "INTEGER"),
        ("event_team", "INTEGER"),
        ("possession_team", "INTEGER"),
        ("home_win", "INTEGER"),
    ]

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else self.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    def _connect(self) -> sqlite3.Connection:
        """Create a SQLite connection with row access by column name."""
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_tables(self) -> None:
        """Create SQLite tables and indexes."""
        column_defs = ",\n".join(
            f"{column_name} {column_type}"
            for column_name, column_type in self.CLUTCH_EVENT_COLUMNS
        )

        with self._connect() as connection:
            connection.executescript(
                f"""
                CREATE TABLE IF NOT EXISTS {self.CLUTCH_EVENTS_TABLE} (
                    {column_defs},
                    PRIMARY KEY (game_id, event_num)
                );

                CREATE INDEX IF NOT EXISTS idx_clutch_events_season
                ON {self.CLUTCH_EVENTS_TABLE}(season);

                CREATE INDEX IF NOT EXISTS idx_clutch_events_player_id
                ON {self.CLUTCH_EVENTS_TABLE}(player_id);
                """
            )

    def _season_key(self, season: Optional[str]) -> Optional[str]:
        """Return the 2-digit season key."""
        if season is None:
            return None
        return season[2:4] if len(season) >= 4 and "-" in season else season

    def _prepare_clutch_events(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare clutch event data for SQLite storage."""
        clutch_events = df.copy()
        column_names = [column_name for column_name, _ in self.CLUTCH_EVENT_COLUMNS]

        for column in (
            "event_msg_type",
            "event_msg_action_type",
            "player_name",
            "game_id",
            "season"
        ):
            if column in clutch_events.columns:
                clutch_events[column] = clutch_events[column].apply(
                    lambda x: str(x) if x is not None and pd.notna(x) else None
                )

        for column in ("event_team", "possession_team", "home_win"):
            if column in clutch_events.columns:
                clutch_events[column] = clutch_events[column].apply(
                    lambda x: int(x) if x is not None and pd.notna(x) else None
                )

        return clutch_events[column_names]

    def has_clutch_events(self, season: str) -> bool:
        """Return whether clutch events exist for the season."""
        season_key = self._season_key(season)

        with self._connect() as connection:
            row = connection.execute(
                f"SELECT 1 FROM {self.CLUTCH_EVENTS_TABLE} WHERE season = ? LIMIT 1",
                (season_key,),
            ).fetchone()

        return row is not None

    def save_clutch_events(self, df: pd.DataFrame, replace_season: bool = False) -> int:
        """Save clutch events to SQLite."""
        if df.empty:
            return 0

        clutch_events = self._prepare_clutch_events(df)
        column_names = [column_name for column_name, _ in self.CLUTCH_EVENT_COLUMNS]
        seasons = clutch_events["season"].dropna().unique().tolist()

        with self._connect() as connection:
            if replace_season and seasons:
                for season in seasons:
                    connection.execute(
                        f"DELETE FROM {self.CLUTCH_EVENTS_TABLE} WHERE season = ?",
                        (season,),
                    )

            clutch_events.to_sql("_temp", connection, if_exists="replace", index=False)
            columns = ", ".join(column_names)
            connection.execute(
                f"""
                INSERT OR REPLACE INTO {self.CLUTCH_EVENTS_TABLE} ({columns})
                SELECT {columns}
                FROM _temp
                """
            )
            connection.execute("DROP TABLE IF EXISTS _temp")

        return len(clutch_events)

    def load_clutch_events(self, season: Optional[str] = None) -> pd.DataFrame:
        """Load clutch events from SQLite."""
        query = f"SELECT * FROM {self.CLUTCH_EVENTS_TABLE}"
        params: tuple[Any, ...] = ()

        if season is not None:
            query += " WHERE season = ?"
            params = (self._season_key(season),)

        query += " ORDER BY game_id, period, pc_time DESC, event_num"

        with self._connect() as connection:
            return pd.read_sql_query(query, connection, params=params)
