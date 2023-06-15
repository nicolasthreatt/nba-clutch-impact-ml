# TODO: CLEAN UP CODE
# MOVE TO A DIRECTORY -> nba-clutch-analysis
# Add Docstrings and comments
# Verify data by writing to csv
from enum import IntEnum
import requests
import pandas as pd
from collections import OrderedDict
from sklearn.linear_model import LogisticRegression


# TODO: MOVE TO SEPERATE FILE
class Game:
    def __init__(self, row):
        self.season_id = row[0]
        self.team_id = row[1]
        self.team_abbreviation = row[2]
        self.team_name = row[3]
        self.game_id = row[4]
        self.game_date = row[5]
        self.matchup = row[6]
        self.wl = row[7]
        self.minutes = row[8]
        self.points = row[9]
        self.fgm = row[10]
        self.fga = row[11]
        self.fg_pct = row[12]
        self.fg3m = row[13]
        self.fg3a = row[14]
        self.fg3_pct = row[15]
        self.ftm = row[16]
        self.fta = row[17]
        self.ft_pct = row[18]
        self.oreb = row[19]
        self.dreb = row[20]
        self.reb = row[21]
        self.ast = row[22]
        self.stl = row[23]
        self.blk = row[24]
        self.tov = row[25]
        self.pf = row[26]
        self.plus_minus = row[27]


# TODO: MOVE TO SEPERATE FILE
class PlayByPlay:
    def __init__(self, row):
        self.game_id = row[0]
        self.event_num = row[1]
        self.event_msg_type = row[2]
        self.event_msg_action_type = row[3]
        self.period = row[4]
        self.wc_time_string = row[5]
        self.pc_time = self.convert_pc_time(row[6])
        self.home_description = row[7]
        self.neutral_description = row[8]
        self.visitor_description = row[9]
        self.description = self.home_description or self.visitor_description
        self.score = row[10]
        self.score_margin = int(row[11]) if row[11] not in (None, "TIE") else 0
        self.person1_type = row[12]
        self.player1_id = row[13]
        self.player1_name = row[14]
        self.player1_team_id = row[15]
        self.player1_team_city = row[16]
        self.player1_team_nickname = row[17]
        self.player1_team_abbreviation = row[18]
        self.person2_type = row[19]
        self.player2_id = row[20]
        self.player2_name = row[21]
        self.player2_team_id = row[22]
        self.player2_team_city = row[23]
        self.player2_team_nickname = row[24]
        self.player2_team_abbreviation = row[25]
        self.person3_type = row[26]
        self.player3_id = row[27]
        self.player3_name = row[28]
        self.player3_team_id = row[29]
        self.player3_team_city = row[30]
        self.player3_team_nickname = row[31]
        self.player3_team_abbreviation = row[32]
        self.video_available_flag = row[33]
    
    def convert_pc_time(self, pc_time_string):
        pc_time_minutes = int(pc_time_string.split(":")[0]) if pc_time_string else None
        pc_time_seconds = int(pc_time_string.split(":")[1]) if pc_time_string else None
        return pc_time_minutes * 60 + pc_time_seconds if pc_time_string else None


# TODO: MOVE TO SEPERATE FILE
class EventMsgType(IntEnum):
    FIELD_GOAL_MADE = 1
    FIELD_GOAL_MISSED = 2
    FREE_THROW = 3
    REBOUND = 4
    TURNOVER = 5
    FOUL = 6
    VIOLATION = 7
    # TIMEOUT = 9 # TODO: NEEDED?

    @classmethod
    def has_event(cls, event):
        return event in cls._value2member_map_


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
    return [attr for attr in vars(play) if not attr.startswith("__")] + ["event_player", "home_poss", "home_win"]


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
    clutch = False
    for row in pbp_data["resultSets"][0]["rowSet"]:
        play = PlayByPlay(row)

        if play.pc_time and play.score_margin:
            clutch = play.pc_time <= 300 and abs(play.score_margin) <= 5

        if clutch and EventMsgType.has_event(play.event_msg_type) and play.player1_id and play.player1_team_id:
            primary_player = play.player1_name or play.player1_team_id
            primary_team_id = play.player1_team_id
            df = append_row_to_dataframe(df, play, primary_player, teams[primary_team_id])
            if (play.event_msg_type == 1 and "AST" in play.description) or (
                play.event_msg_type == 5 and "STL" in play.description
            ):
                secondary_player = play.player2_name
                secondary_team_id = play.player2_team_id
                df = append_row_to_dataframe(df, play, secondary_player, teams[secondary_team_id])
            elif play.event_msg_type == 2 and "BLK" in play.description:
                secondary_player = play.player3_name
                secondary_team_id = play.player3_team_id
                df = append_row_to_dataframe(df, play, secondary_player, teams[secondary_team_id])

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

    # Retrieve instance variables using vars() and filter out those starting with "__"
    new_row = [vars(play)[attr] for attr in vars(play) if not attr.startswith("__")]
    
    # Extend the new_row list with the player and team values
    new_row.extend([player] + team)

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
