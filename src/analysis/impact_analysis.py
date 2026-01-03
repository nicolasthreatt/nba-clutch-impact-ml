import pandas as pd
import numpy as np

from typing import Literal


class ClutchWinProbabilityEvaluator:
    """Evaulates clutch impact based on changes in predicted win probability during play-by-play events."""

    def generate_clutch_impact_scores(
        self,
        df: pd.DataFrame,
        level: Literal["event", "player"] = "player"
    ) -> pd.DataFrame:
        """
        Compute clutch impact scores from play-by-play data.

        Args:
            df (pd.DataFrame): Play-by-play data including win probabilities.
            level (Literal["event", "player"]):
                - "event": individual event scores
                - "player": aggregated player scores

        Returns: pd.DataFrame
        """
        if level not in {"event", "player"}:
            raise ValueError(f"Invalid level: {level}")

        df = df.copy()

        df = df.sort_values(
            ["game_id", "period", "pc_time", "event_num"],
            ascending=[True, True, False, True]
        ).reset_index(drop=True)

        df_clutch = self._calculate_clutch_impact_scores(df)

        if level == "player":
            df_clutch = (
                df_clutch
                .groupby(["season", "player_name"])
                .agg(
                    games_played=("game_id", pd.Series.nunique),
                    clutch_impact_rtg=("clutch_impact_rtg", "sum"),
                )
                .reset_index()
                .sort_values(by="clutch_impact_rtg", ascending=False)
            )

        return df_clutch

    def _calculate_win_probability_changes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates prior and delta win probabilities for home and away teams."""
        for team_type in ("home", "away"):
            col = f"{team_type}_win_probability"
            df[f"prior_{col}"] = self._calculate_prior_win_probability(df, col)
            df[f"delta_{col}"] = df[col] - df[f"prior_{col}"].fillna(0)

        return df.fillna(0)

    def _calculate_prior_win_probability(self, df: pd.DataFrame, team_type: str) -> pd.Series:
        """Computes prior win probability for each play."""
        return df.groupby("game_id")[team_type].shift(1).fillna(0)

    def _calculate_clutch_impact_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute the clutch impact for each play-by-play event."""
        df = self._calculate_win_probability_changes(df)

        df["clutch_impact_rtg"] = np.where(
            df["home_possession"],
            df["delta_home_win_probability"],
            df["delta_away_win_probability"],
        )

        df["clutch_impact_rtg"] = round(df["clutch_impact_rtg"] * 100, 2)

        return df
