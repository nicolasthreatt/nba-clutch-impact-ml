import pandas as pd
from data_processing import get_clutch_events
from model import create_model, evaluate_model


if __name__ == "__main__":
    print("\nGetting Training Data...")
    dfTrain = get_clutch_events("2021-22")

    print(dfTrain.tail())
    exit()

    print("\nGetting Test Data...")
    dfTest = get_clutch_events("2022-23")

    if not dfTrain or not dfTest:
        exit("\nNo data returned. Exiting...")

    if dfTrain.empty or dfTest.empty:
        exit("\nNo data returned. Exiting...")

    model = create_model(dfTrain)

    dfPredict = (
        dfTest.assign(
            predicted_winner=model.predict(dfTest.loc[FEATURES].values),
            home_team_win_prob=model.predict_proba(dfTest.loc[FEATURES].values)[:, 1],
            away_team_win_prob=model.predict_proba(dfTest.loc[FEATURES].values)[:, 0],  # Is this right?
        )
    )[dfTest.columns.tolist() + ["predicted_winner", "home_team_win_prob", "away_team_win_prob"]]

    print("\nPredictions:")
    print(dfPredict.head())
    print(evaluate_model(dfTest, model))
