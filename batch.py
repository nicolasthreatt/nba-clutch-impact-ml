# batch.py
from src.analysis.impact_analysis import generate_clutch_impact_ratings
from src.data.data_processing import get_clutch_events
from src.model.model import create_model, evaluate_model, predict_win_probs


if __name__ == "__main__":
    print("\nGetting Training Data...")
    dfTrain = get_clutch_events("2021-22")

    print("\nGetting Test Data...")
    dfTest = get_clutch_events("2022-23")

    if dfTrain is None or dfTest is None or dfTrain.empty or dfTest.empty:
        exit("\nNo data returned. Exiting...")

    print("\nTraining Model...")
    model = create_model(dfTrain)
    evaluate_model(dfTrain, model)

    print("\nPredicting Win Probabilities...")
    dfPredict = predict_win_probs(dfTest, model)
    print(dfPredict.head())

    print("\nGenerating Clutch Impact Ratings...")
    dfClutchScores = generate_clutch_impact_ratings(dfPredict)

    if dfClutchScores is None or dfClutchScores.empty:
        exit("\nNo data returned. Exiting...")

    print(dfClutchScores.head())
