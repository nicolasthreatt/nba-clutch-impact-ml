import requests
import pandas as pd
from collections import OrderedDict
from sklearn.linear_model import LogisticRegression


BASE_URL = "https://stats.nba.com/stats/"
HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Connection": "keep-alive",
    "Referer": "https://stats.nba.com/",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

FEATURES = [
    "EVENTNUM",
    "EVENTMSGTYPE",
    "EVENTMSGACTIONTYPE",
    "PERIOD",
    "PCTIMESTRING",
    "SCORE",
    "SCOREMARGIN",
]
TARGET = "HOME_WIN"


def load_games(season: str) -> dict:
    """Loads game data from the leaguegamefinder NBA API.

    Returns:
        dict: The game data returned by the API, or None if the request failed.

    Raises:
        requests.exceptions.RequestException: If the API request fails.
    """
    params = {
        "PlayerOrTeam": "T",
        "LeagueID": "00",
        "Season": season,
        "SeasonType": "Regular Season",
    }

    try:
        response = requests.get(
            BASE_URL + "leaguegamefinder",
            headers=HEADERS,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print("Request failed:", e)
        return None


def load_play_by_play(game_id):
    """Loads play-by-play data for a specific game ID.

    Args:
        game_id (str): The ID of the game.

    Returns:
        dict: The play-by-play data returned by the API, or None if the request failed.

    Raises:
        requests.exceptions.RequestException: If the API request fails.
    """
    pbp_params = {
        "GameID": game_id,
        "StartPeriod": 4,
        "EndPeriod": 10,
    }

    try:
        response = requests.get(
            BASE_URL + "playbyplayv2",
            headers=HEADERS,
            params=pbp_params,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print("Request failed:", e)
        return None


def get_clutch_events(season: str) -> pd.DataFrame:
    """Gets play-by-play data for clutch-time situations.

    Clutch-time situations are defined as the last 5 minutes of the 4th quarter
    or overtime when the score differential is 5 points or less.

    Args:
        season (str): The season to get the data for.

    Returns:
        pd.DataFrame: A DataFrame containing the play-by-play data for clutch-time situations.
    """
    # Get game IDs. If the request fails, return to exit the function
    data = load_games(season)
    if data is None:
        return

    # Get the game IDs from the API response
    # TODO: MOVE TO SEPARATE FUNCTION
    games = {}
    for game in data["resultSets"][0]["rowSet"]:
        team_id = game[1]
        game_id = game[4]
        matchup = game[6]
        w_l = game[7]
        if game_id not in games:
            games[game_id] = {}

        home_win = int(w_l == "W") if "vs." in matchup else 0

        games[game_id][team_id] = home_win

    # TODO: MOVE TO SEPARATE FUNCTION
    # print("Found", len(games), "games")
    # print("Found", len(win_loss), "wins/losses")

    # Get play-by-play data for each game ID
    # TODO: PERFORM CUSTOM SORT FOR GAME_IDS FROM DATA STRUCTURES
    for game_id, teams in OrderedDict(sorted(games.items())).items():
        print("Getting play-by-play data for game ID:", game_id)
        pbp_data = load_play_by_play(game_id)
        if pbp_data is None:
            print("No play-by-play data for game ID:", game_id)
            continue

        # Create an empty DataFrame with the extracted column names
        columns = pbp_data["resultSets"][0]["headers"] + ["HOME_WIN"]
        df = pd.DataFrame(columns=columns)

        # Iterate through each play in the play-by-play data and filter for clutch-time situations
        # Append each clutch-time play to the DataFrame
        for row in pbp_data["resultSets"][0]["rowSet"]:
            player1_team_id = row[15]
            player2_team_id = row[22]
            player3_team_id = row[29]

            # TODO: GET CORRECT TEAM ID for each event
            player_team_id = player1_team_id or player2_team_id or player3_team_id

            if row[6] and row[11] and player_team_id:  # game-clock/score margin
                gc_time_minutes = int(row[6].split(":")[0])
                score_margin = 0 if row[11] == "TIE" else int(row[11])
                if gc_time_minutes <= 5 and abs(score_margin) <= 5:  # Clutch-time
                    # TODO: GET CORRECT TEAM ID
                    df.loc[len(df.index)] = row + [teams[player_team_id]]
                    print(df.loc[len(df.index) - 1])

    return df


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


if __name__ == "__main__":
    print("\nGetting Training Data...")
    dfTrain = get_clutch_events("2021-22")

    print("\nGetting Test Data...")
    dfTest = get_clutch_events("2022-23")

    if dfTrain.empty or dfTest.empty:
        exit("No data returned. Exiting...")

    model = create_model(dfTrain)

    dfPredict = (
        dfTest.assign(
            predicted_winner=model.predict(dfTest.loc[FEATURES].values),
            home_win_prob=model.predict_proba(dfTest.loc[FEATURES].values)[:, 1],
        )
    )[dfTest.columns.tolist() + ["predicted_winner", "home_win_prob"]]

    print("\nPredictions:")
    print(dfPredict.head())
    print(evaluate_model(dfTest, model))
