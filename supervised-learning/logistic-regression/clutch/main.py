from data_processing import calculate_win_probs, get_clutch_events
from model import create_model, evaluate_model
from data_processing import 


if __name__ == "__main__":
    print("\nGetting Training Data...")
    dfTrain = get_clutch_events("2021-22")

    print("\nGetting Test Data...")
    dfTest = get_clutch_events("2022-23")

    if not dfTrain or not dfTest or dfTrain.empty or dfTest.empty:
        exit("\nNo data returned. Exiting...")

    model = create_model(dfTrain)
    evaluate_model(dfTrain, model)

    dfPredict = calculate_win_probs(dfTest, model)

    print("\nPredictions:")
    print(dfPredict.head())
