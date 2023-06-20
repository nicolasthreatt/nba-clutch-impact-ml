# crunch_time_analysis.py
import pandas as pd
import numpy as np

def calculate_teams_win_probability_changes(df_predict: pd.DataFrame) -> pd.DataFrame:
    """Calculates a team's change in win probability from the prior clutch event.

    Args:
        df_predict (pd.DataFrame): DataFrame representation of the test set's predicted results.
    
    Returns:
        pd.DataFrame: Pandas DataFrame with original input columns along with the home and away teams' 
            change in win probability for each play-by-play clutch event.
    """

    df_predict["pbpEventNum"] = (
        df_predict
        .groupby(['season','Game_ID','Period','PCTime','Mins','OrderNumber'])
        .cumcount() + 1
    )

    for team_win_probability in ["away_team_win_probability", "home_team_win_probability"]:
        df_predict[f'prior_{team_win_probability}'] = get_prior_win_probability(df_predict, team_win_probability)
        df_predict[f'delta_{team_win_probability}'] = calculate_delta_win_probability(df_predict, team_win_probability)

    return df_predict.fillna(0)


def get_prior_win_probability(df_predict: pd.DataFrame, team_win_probability: str) -> np.ndarray:
    """Computes the prior win probability for a given team.

    Args:
        df_predict (pd.DataFrame): DataFrame representation of the test set's predicted results.
        team_win_probability (str): Column name representing the team's win probability.

    Returns:
        pd.Series: Pandas Series containing the prior win probability for each play-by-play event.
    """

    return np.where(
        (df_predict['pbpEventNum'] == 1),
        (
            df_predict
            .sort_values(
                by=['season','Game_ID','Period','PCTime','Mins','OrderNumber'],
                ascending=[False,True,True,False,False,True]
            )
            .groupby(['Game_ID'])[team_win_probability]
            .shift(1)
        ),
        (
            df_predict
            .sort_values(
                by=['season','Game_ID','Period','PCTime','Mins','OrderNumber'],
                ascending=[False,True,True,False,False,True]
            )
            .groupby(['Game_ID'])[team_win_probability]
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
        (
            df_predict[f'prior_{team_win_probability}'].isnull() &
            ~df_predict['EventTypeText'].str.contains("Missed")
        ),
        df_predict[team_win_probability],
        df_predict[team_win_probability] - df_predict[f'prior_{team_win_probability}']
    )


def generate_crunch_time_scores(df, aggregation_columns):
    """Compute crunch time scores.
    
    Args:
        df (pd.DataFrame): DataFrame representation of the test set's predicted results.
        aggregation_columns (list): Column names to aggregate the crunch time scores.

    Returns:
        pd.DataFrame: Pandas DataFrame with original input columns along with the crunch time score for each play-by-play clutch event.
    """

    df = calculate_teams_win_probability_changes(df)

    df['Crunch_Time_Score'] = get_crunch_time_score(df)

    return (
        df.groupby(aggregation_columns)['Crunch_Time_Score']
        .sum()
        .reset_index()
        .sort_values(by='Crunch_Time_Score', ascending=False)
    )

def get_crunch_time_score(df):
    """Compute the crunch time score for each play-by-play event.

    Args:
        df (pd.DataFrame): DataFrame representation of the test set's predicted results.

    Returns:
        np.ndarray: Numpy array containing the crunch time score for each play-by-play event.
    """

    df['Crunch_Time_Score'] = np.where(
        (df['Location'] == 'h'), df['delta_home_team_win_probability'],
        np.where(
            (df['Location'] == 'v'), df['delta_away_team_win_probability'], 0
        )
    )

    df['Crunch_Time_Score'] = np.where(
        (df['Location'] == 'h') & (df['EventTypeText'].str.contains("Steal")), df['delta_away_team_win_probability'],
        np.where(
            (df['Location'] == 'v') & (df['EventTypeText'].str.contains("Steal")), df['delta_home_team_win_probability'], df['Crunch_Time_Score']
        )
    )

    df['Crunch_Time_Score'] = np.where(
        df['EventTypeText'].str.contains("Assist"), df['Crunch_Time_Score'] / 2, df['Crunch_Time_Score']
    )

    return df['Crunch_Time_Score']
