# model.py
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


FEATURES = [
    "event_num_scaled",
    "event_msg_type_scaled",
    "event_msg_action_type_scaled",
    "period_scaled",
    "pc_time_scaled",
    "score_margi_scaledn",
    "home_possession_scaled",
]
TARGET = "home_win"


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocesses the data.

    Logistic Regression requires data be scaled to have a mean of 0 and a standard deviation of 1.
    Fit on the training data and use the same scaler to transform the training and test data.

    Args:
        df (pd.DataFrame): The data to preprocess.

    Returns:
        pd.DataFrame: The preprocessed data.
    """
    scaler = StandardScaler()
    for feature in FEATURES:
        df[feature] = df[feature.replace("_scaled", '')]
    df[FEATURES] = scaler.fit_transform(df[FEATURES])

    return df


def create_model(dfTrain: pd.DataFrame) -> LogisticRegression:
    """Creates a logistic regression model.

    Args:
        dfTrain (pd.DataFrame): The training data.

    Returns:
        sklearn.linear_model.LogisticRegression: A logistic regression model.
    """
    dfTrain = preprocess_data(dfTrain)
    
    X = dfTrain[FEATURES].values
    y = dfTrain[TARGET].values
    return LogisticRegression().fit(X, y)


def evaluate_model(df: pd.DataFrame, model: LogisticRegression) -> None:
    """Evaluates a logistic regression model.

    Accuracy is the percentage of correctly predicted label
        = correct predictions / total predictions

    Args:
        df (pd.DataFrame): Data to evaluate the model on.
        model (sklearn.linear_model.LogisticRegression): The logistic regression model.
    """
    X = df[FEATURES]
    y = df[TARGET]

    print("\nAccuracy:", model.score(X, y))


def predict_win_probs(dfTest: pd.DataFrame, lr: LogisticRegression) -> pd.DataFrame:
    """Calculcates the home and away teams win probability for each play-by-play clutch event.

    Args:
        dfTest: DataFrame representation of the test set.
        lr: Trained Logistical Regression model.
    
    Returns:
        Pandas dataframe with original input columns along with the home and away teams win probability
        for each play-by-play clutch event.
    """
    dfTest = preprocess_data(dfTest)
    X = dfTest[FEATURES].values

    # Predict the winner of each game and each team's win probability for each play-by-play event
    dfPredict = (
        dfTest.assign(
            predicted_winner=lr.predict(X),
            home_team_win_probability=lr.predict_proba(X)[:, 1],
            away_team_win_probability=lr.predict_proba(X)[:, 0],
        )
    )[dfTest.columns.tolist() + ["predicted_winner", "home_team_win_probability", "away_team_win_probability"]]

    # Return the new dataframe with 0 fill in for any null data
    return dfPredict.fillna(0)
