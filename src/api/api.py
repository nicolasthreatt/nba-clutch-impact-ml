import requests

BASE_URL = "https://stats.nba.com/stats/"

HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Connection": "keep-alive",
    "Referer": "https://stats.nba.com/",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

SESSION = requests.Session()  # Create Persistent/Reusable HTTP Session
SESSION.headers.update(HEADERS)


def load_games(season: str) -> dict:
    """Loads game data from the leaguegamefinder NBA API.

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
        response = SESSION.get(
            BASE_URL + "leaguegamefinder",
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Request failed for season {season}: {e}")
        return None


def load_play_by_play(game_id: str) -> dict:
    """Loads play-by-play data for a specific game ID.

    Raises:
        requests.exceptions.RequestException: If the API request fails.
    """
    pbp_params = {
        "GameID": game_id,
        "StartPeriod": 4,
        "EndPeriod": 10,
    }

    try:
        response = SESSION.get(
            BASE_URL + "playbyplayv3",
            params=pbp_params,
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Request failed for game {game_id}: {e}")
        return None
