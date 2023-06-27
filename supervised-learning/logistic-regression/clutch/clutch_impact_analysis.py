# clutch_impact_analysis.py
import pandas as pd
import numpy as np
from EventMsgType import EventMsgType


def generate_clutch_impact_ratings(df: pd.DataFrame, aggregation_columns=["season", "event_player"]) -> pd.DataFrame:
    """Compute clutch impact ratings for each player based on the input aggregation columns.
    
    Args:
        df (pd.DataFrame): DataFrame representation of the test set's predicted results.
        aggregation_columns (list): Column names to aggregate the clutch impact ratings.

    Returns:
        pd.DataFrame: Pandas DataFrame with the clutch impact ratings for each player.
    """

    df = calculate_teams_win_probability_changes(df)
    df = calculate_clutch_impact_ratings(df)

    return (
        df.groupby(aggregation_columns)['clutch_impact_rtg']
        .sum()
        .reset_index()
        .sort_values(by='clutch_impact_rtg', ascending=False)
    )


def calculate_teams_win_probability_changes(df_predict: pd.DataFrame) -> pd.DataFrame:
    """Calculates a team's change in win probability from the prior clutch event.

    Args:
        df_predict (pd.DataFrame): DataFrame representation of the test set's predicted results.
    
    Returns:
        pd.DataFrame: Pandas DataFrame with original input columns along with the home and away teams' 
            change in win probability for each play-by-play clutch event.
    """
    for team_win_probability in ["away_team_win_probability", "home_team_win_probability"]:
        df_predict[f'prior_{team_win_probability}'] = get_prior_win_probability(df_predict, team_win_probability)
        df_predict[f'delta_{team_win_probability}'] = calculate_delta_win_probability(df_predict, team_win_probability)

    return df_predict.fillna(0)


def get_prior_win_probability(df_predict: pd.DataFrame, team_win_probability: str) -> np.ndarray:
    """Computes the prior win probability for a given team.

    Some event types, such as assists, involves two players from the same team.
    In these cases, thee win probability for one of the events will occur two rows after the prior event.

    Args:
        df_predict (pd.DataFrame): DataFrame representation of the test set's predicted results.
        team_win_probability (str): Column name representing the team's win probability.

    Returns:
        pd.Series: Pandas Series containing the prior win probability for each play-by-play event.
    """
    df_predict["subseq"] = (
        df_predict
        .groupby(['season','game_id','period','pc_time'])
        .cumcount() + 1
    )

    return np.where(
        (df_predict['subseq'] == 1),
        (
            df_predict
            .sort_values(
                by=['season','game_id','period','pc_time'],
                ascending=[False,True,True,False]
            )
            .groupby(['game_id'])[team_win_probability]
            .shift(1)
        ),
        (
            df_predict
            .sort_values(
                by=['season','game_id','period','pc_time'],
                ascending=[False,True,True,False]
            )
            .groupby(['game_id'])[team_win_probability]
            .shift(2)
        )
    )


def calculate_delta_win_probability(df_predict, team_win_probability):
    """Calculates the change in win probability for a given team.

    Args:
        df_predict (pd.DataFrame): DataFrame representation of the test set's predicted results.
        team_win_probability (str): Column name representing the team's win probability.

    Returns:
        pd.Series: Pandas Series containing the change in win probability for each play-by-play event.
    """
    return np.where(
        df_predict[f'prior_{team_win_probability}'].notnull(),
            df_predict[team_win_probability] - df_predict[f'prior_{team_win_probability}'], 0.0
    )


def calculate_clutch_impact_ratings(df):
    """Compute the clutch impact for each play-by-play event.

    Args:
        df (pd.DataFrame): DataFrame representation of the test set's predicted results.

    Returns:
        pd.DataFrame: Pandas DataFrame with original input columns along with
                      the clutch impact for each play-by-play clutch event.
    """

    df['clutch_impact_rtg'] = np.where(
        (df['home_possession'] == 1), df['delta_home_team_win_probability'],
        np.where(
            (df['home_possession'] == 0), df['delta_away_team_win_probability'], 0
        )
    )

    df['clutch_impact_rtg'] = ( # TODO: SEE IF THIS IS NEEDED
        np.where(       
            (df['home_possession'] == 1) & (df["event_msg_type"] == EventMsgType.TURNOVER) & (df['description'].str.contains("STL")),
                df['delta_away_team_win_probability'],
        np.where(
            (df['home_possession'] == 0) & (df["event_msg_type"] == EventMsgType.TURNOVER) &  (df['description'].str.contains("STL")),
                df['delta_home_team_win_probability'], df['clutch_impact_rtg']
        ))
    )

    df['clutch_impact_rtg'] = np.where(
        (df["event_msg_type"] == EventMsgType.FIELD_GOAL_MADE) & df['description'].str.contains("AST"),
            round(df['clutch_impact_rtg'] / 2 * 100, 2),
            round(df['clutch_impact_rtg'] * 100, 2)
    )

    return df
