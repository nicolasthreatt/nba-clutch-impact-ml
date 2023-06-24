# data_processing.py
import pandas as pd
from api import load_games, load_play_by_play
from collections import OrderedDict
from EventMsgType import EventMsgType
from Game import Game
from PlayByPlay import PlayByPlay


def get_clutch_events(season: str) -> pd.DataFrame:
    """Gets play-by-play data for clutch-time situations.

    Clutch-time situations are defined as the last 5 minutes of the 4th quarter
    or overtime when the score differential is 5 points or less.

    Args:
        season (str): The season to get the data for.

    Returns:
        pd.DataFrame: A DataFrame containing the play-by-play data for clutch-time situations.
    """
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

        if df is not None and df.home_win.unique().size == 2:
            break

        df = process_play_by_play(pbp_data, teams, df)

    return df


def extract_game_data(game_data):
    """Extracts game data from the game data returned by the leaguegamefinder API.

    Args:
        game_data (dict): The game data returned by the leaguegamefinder API.
    
    Returns:
        dict: A dictionary containing the game data.
            game_id -> {team_id -> [is_home_team, is_home_win]}
    """

    games = {}
    for game in game_data["resultSets"][0]["rowSet"]:
        game_obj = Game(game)

        game_id = game_obj.game_id
        team_id = game_obj.team_id

        if game_id not in games:
            games[game_id] = {}

        # Determine if the home team and whether the home team won
        is_home_team = "vs." in game_obj.matchup
        if is_home_team: 
            is_home_win = int(game_obj.wl == "W")
        else:
            is_home_win = int(game_obj.wl == "L")

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
    home_possession = None

    for row in pbp_data["resultSets"][0]["rowSet"]:
        play = PlayByPlay(row)

        clutch = determine_clutch(play)

        if clutch and is_valid_play(play):
            primary_player, primary_team_id = determine_primary_player_and_team(play)
            is_home_team, is_home_win = teams[primary_team_id]

            home_possession = determine_home_possession(play, is_home_team)
            play.set_home_possession(home_possession)
            play.set_home_win(is_home_win)

            if is_assist(play) or is_steal(play):
                secondary_player, secondary_team_id = determine_secondary_player_and_team(play, 2)
                teams[secondary_team_id][0] = home_possession
                df = append_row_to_dataframe(df, play, secondary_player, teams[secondary_team_id])
            elif is_block(play):
                secondary_player, secondary_team_id = determine_secondary_player_and_team(play, 3)
                teams[secondary_team_id][0] = home_possession
                df = append_row_to_dataframe(df, play, secondary_player, teams[secondary_team_id])

    return df


def determine_clutch(play):
    """Determines if a play is considered clutch based on its time and score margin.

    A clutch play is defined as a play that occurs during the last 5 minutes of the 4th quarter or overtime,
    where the score margin is 5 points or less.

    Args:
        play (PlayByPlay): The play by play event object.

    Returns:
        bool: True if the play occurs during clutch time, False otherwise.
    """
    if play.pc_time and play.score_margin:
        return play.pc_time <= 300 and abs(play.score_margin) <= 5
    return False


def is_valid_play(play):
    """Checks if a play is a valid play based on its event message type and player/team information.

    Only looking for plays that are a field goal attempt, free throw attempt, turnover, or rebound.

    Args:
        play (PlayByPlay): The play by play event object.

    Returns:
        bool: True if the play is a valid play, False otherwise.
    """
    return (
        EventMsgType.has_event(play.event_msg_type) and
        play.player1_id and play.player1_team_id
    )


def determine_primary_player_and_team(play):
    """Determines the primary player and team for a play.

    Args:
        play (PlayByPlay): The play by play event object.

    Returns:
        tuple: A tuple containing the primary player and team ID.
    """
    primary_player = play.player1_name or play.player2_name
    primary_team_id = play.player1_team_id or play.player2_team_id
    return primary_player, primary_team_id


def determine_home_possession(play, is_home_team):
    """Determines the home possession based on the play and whether the primary team is the home team.

    Args:
        play (PlayByPlay): The play by play event object.
        is_home_team (bool): True if the primary team is the home team, False otherwise.

    Returns:
        bool or None: True if it's a home possession, False if it's an away possession, None if unknown.
    """
    if EventMsgType.non_rebound_event(play.event_msg_type):
        return is_home_team
    return None


def is_assist(play):
    """Checks if a play is an assist.

    Args:
        play (PlayByPlay): The play by play object.

    Returns:
        bool: True if the play is an assist, False otherwise.
    """
    return play.event_msg_type == 1 and "AST" in play.description


def is_steal(play):
    """Checks if a play is a steal.

    Args:
        play (PlayByPlay): The play by play object.

    Returns:
        bool: True if the play is a steal, False otherwise.
    """
    return play.event_msg_type == 5 and "STL" in play.description


def is_block(play):
    """Checks if a play is a block.

    Args:
        play (PlayByPlay): The play by play object.

    Returns:
        bool: True if the play is a block, False otherwise.
    """
    return play.event_msg_type == 2 and "BLK" in play.description


def determine_secondary_player_and_team(play, player_num):
    """Determines the secondary player and team for a play based on the player number.

    Args:
        play (PlayByPlay): The play by play object.
        player_num (int): The player number (2 for assist/steal, 3 for block).

    Returns:
        tuple: A tuple containing the secondary player and team ID.
    """
    if player_num == 2: # assist/steal
        secondary_player = play.player2_name
        secondary_team_id = play.player2_team_id
    elif player_num == 3: # block
        secondary_player = play.player3_name
        secondary_team_id = play.player3_team_id
    return secondary_player, secondary_team_id


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
    
    # Extend the new_row list with the player responsible for the event
    new_row.extend([player])

    # Append the new row to the DataFrame
    df.loc[len(df)] = new_row
    
    return df
