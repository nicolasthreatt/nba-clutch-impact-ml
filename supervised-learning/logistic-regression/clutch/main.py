from data_processing import get_clutch_events
from model import create_model, evaluate_model, predict_win_probs
from plots import plot_accurary


if __name__ == "__main__":
    print("\nGetting Training Data...")
    dfTrain = get_clutch_events("2021-22")

    print("\nGetting Test Data...")
    dfTest = get_clutch_events("2022-23")

    if dfTrain is None or dfTest is None or dfTrain.empty or dfTest.empty:
        exit("\nNo data returned. Exiting...")

    print("\nTraining Data:")
    print(dfTrain.tail())

    print("\nTest Data:")
    print(dfTest.tail())

    model = create_model(dfTrain)
    evaluate_model(dfTrain, model)

    dfPredict = predict_win_probs(dfTest, model)

    plot_accurary(dfPredict)

    print("\nPredictions:")
    print(dfPredict.head())
