# model.py
import pandas as pd
from sklearn.linear_model import LogisticRegression


FEATURES = [
    "event_num",
    "event_msg_type",
    "event_msg_action_type",
    "period",
    "pc_time",
    "score_margin",
    "home_poss",
]
TARGET = "home_win"


def create_model(dfTrain: pd.DataFrame) -> LogisticRegression:
    """Creates a logistic regression model.

    Args:
        dfTrain (pd.DataFrame): The training data.

    Returns:
        sklearn.linear_model.LogisticRegression: A logistic regression model.
    """

    X = dfTrain.loc[FEATURES].values
    y = dfTrain.loc[TARGET].values

    return LogisticRegression().fit(X, y)


def evaluate_model(df: pd.DataFrame, model: LogisticRegression) -> None:
    """Evaluates a logistic regression model.

    Args:
        df (pd.DataFrame): Data to evaluate the model on.
        model (sklearn.linear_model.LogisticRegression): The logistic regression model.
    """
    X = df.loc[FEATURES].values
    y = df.loc[TARGET].values

    print("\nAccuracy:", model.score(X, y))


def calculate_win_probs(dfTest: pd.DataFrame, lr: LogisticRegression) -> pd.DataFrame:
    """Calculcates the home and away teams win probability for each play-by-play clutch event.

    Args:
        dfTest: DataFrame representation of the test set.
        lr: Trained Logistical Regression model.
    
    Returns:
        Pandas dataframe with original input columns along with the home and away teams win probability
        for each play-by-play clutch event.
    """

    # Predict the winner of each game and each team's win probability for each play-by-play event
    dfPredict = (
        dfTest.assign(
            predicted_winner=model.predict(dfTest.loc[FEATURES].values),
            home_team_win_prob=model.predict_proba(dfTest.loc[FEATURES].values)[:, 1],
            away_team_win_prob=model.predict_proba(dfTest.loc[FEATURES].values)[:, 0],  # TODO: Is this right?
        )
    )[dfTest.columns.tolist() + ["predicted_winner", "home_team_win_prob", "away_team_win_prob"]]

    # Calcuate the away team's win probability
    # dfPredict['away_team_win_probability'] = 1 - dfPredict['home_team_win_probability']

    # Return the new dataframe with 0 fill in for any null data
    return dfPredict.fillna(0)
