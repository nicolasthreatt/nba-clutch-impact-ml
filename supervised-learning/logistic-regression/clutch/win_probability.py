# TODO: CLEAN UP CODE
# MOVE TO A DIRECTORY -> nba-clutch-analysis
# Add Docstrings and comments
# Verify data by writing to csv
import requests
import pandas as pd
from collections import OrderedDict
from sklearn.linear_model import LogisticRegression
from EventMsgType import EventMsgType
from Game import Game
from PlayByPlay import PlayByPlay

# MAYBE ADD TO .env file?
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
    "event_num",
    "event_msg_type",
    "event_msg_action_type",
    "period",
    "pc_time",
    # "SCORE",
    "score_margin",
    # "home_poss",  # TODO: IMPLEMENT AS BINARY FLAG
]
TARGET = "home_win"


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
    # Load all games for the specified season
    data = load_games(season)
    if data is None:
        return

    games = extract_game_data(data)

    df = None
    for game_id, teams in sort_games(games):
        print("Getting play-by-play data for game ID:", game_id)
        pbp_data = load_play_by_play(game_id)
        if pbp_data is None:
            print("No play-by-play data for game ID:", game_id)
            continue

        df = process_play_by_play(pbp_data, teams, df)

    return df


def extract_game_data(game_data):
    """Extracts game data from the game data returned by the leaguegamefinder API.

    Args:
        game_data (dict): The game data returned by the leaguegamefinder API.
    
    Returns:
        dict: A dictionary containing the game data.
    """

    games = {}
    for game in game_data["resultSets"][0]["rowSet"]:
        game_obj = Game(game)
        game_id = game_obj.game_id

        if game_id not in games:
            games[game_id] = {}

        team_id = game_obj.team_id
        is_home_team = "vs." in game_obj.matchup
        is_home_win = int(game_obj.wl == "W") if is_home_team else False

        games[game_id][team_id] = [is_home_team, is_home_win]

    return games


def create_column_names(play):
    """Creates a list of column names based on the attributes of the PlayByPlay class.

    Args:
        play (PlayByPlay): The PlayByPlay object containing the row data.

    Returns:
        list: A list of column names.
    """
    return [attr for attr in vars(play) if not attr.startswith("__")] + ["event_player"]


def sort_games(games):
    """Sorts the games by game ID.

    TODO: CUSTOM SORT SHOWING OFF DATA SRUCTURES AND ALGORITHMS

    Args:
        games (dict): The games to sort.
    
    Returns:
        list: A list of tuples containing the game ID and the teams.
    """
    return OrderedDict(sorted(games.items())).items()


def process_play_by_play(pbp_data, teams, df):
    """Processes the play-by-play data returned by the playbyplayv2 API.

    Args:
        pbp_data (dict): The play-by-play data returned by the playbyplayv2 API.
        teams (dict): The teams playing in the game.
        df (pd.DataFrame): The DataFrame to append the data to.

    Returns:
        pd.DataFrame: A DataFrame containing the play-by-play data.
    """
    clutch = False
    home_poss = None
    for row in pbp_data["resultSets"][0]["rowSet"]:
        play = PlayByPlay(row)

        if play.pc_time and play.score_margin:
            clutch = play.pc_time <= 300 and abs(play.score_margin) <= 5

        if clutch and EventMsgType.has_event(play.event_msg_type) and play.player1_id and play.player1_team_id:
            primary_player = play.player1_name or play.player1_team_id
            primary_team_id = play.player1_team_id
            df = append_row_to_dataframe(df, play, primary_player, teams[play.player1_team_id])
            if (play.event_msg_type == 1 and "AST" in play.description) or (
                play.event_msg_type == 5 and "STL" in play.description
            ):
                secondary_player = play.player2_name
                # secondary_team_id = play.player2_team_id
                df = append_row_to_dataframe(df, play, secondary_player, teams[play.player1_team_id])
            elif play.event_msg_type == 2 and "BLK" in play.description:
                secondary_player = play.player3_name
                # secondary_team_id = play.player3_team_id
                df = append_row_to_dataframe(df, play, secondary_player, teams[play.player1_team_id])
            print(df.tail(5))

    return df


def append_row_to_dataframe(df: pd.DataFrame, play: list, player: str, team: list) -> pd.DataFrame:
    """Appends a new row to a DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to append the row to.
        play (PlayByPlay): The PlayByPlay object containing the row data.
        player (str): The player to append to the row.
        team (list): The team to append to the row.

    Returns:
        pd.DataFrame: The DataFrame with the new row appended.
    """
    if df is None:
        df = pd.DataFrame(columns=create_column_names(play))

    # play.is_home_possession(team)
    play.is_home_win(team)

    # Retrieve instance variables using vars() and filter out those starting with "__"
    new_row = [vars(play)[attr] for attr in vars(play) if not attr.startswith("__")]
    
    # Extend the new_row list with the player responsible for the event
    new_row.extend([player])

    # Append the new row to the DataFrame
    df.loc[len(df)] = new_row
    
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
