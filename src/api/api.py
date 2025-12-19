import requests
from typing import Dict, Optional


class API:
    """Client interface for interacting with stats.nba.com endpoints."""

    BASE_URL = "https://stats.nba.com/stats/"

    HEADERS = {
        "Host": "stats.nba.com",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) "
            "Gecko/20100101 Firefox/72.0"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "x-nba-stats-origin": "stats",
        "x-nba-stats-token": "true",
        "Connection": "keep-alive",
        "Referer": "https://stats.nba.com/",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

    def __init__(self, timeout: int = 15):
        self.session = requests.Session()  # Create Persistent/Reusable HTTP Session
        self.session.headers.update(self.HEADERS)
        self.timeout = timeout

    def load_games(self, season: str) -> Optional[Dict]:
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
            response = self.session.get(
                self.BASE_URL + "leaguegamefinder",
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Request failed for season {season}: {e}")
            return None

    def load_play_by_play(self, game_id: str) -> Optional[Dict]:
        """Loads play-by-play data for a specific game ID.

           Raises:
               requests.exceptions.RequestException: If the API request fails.
        """
        params = {
            "GameID": game_id,
            "StartPeriod": 4,
            "EndPeriod": 10,
        }

        try:
            response = self.session.get(
                self.BASE_URL + "playbyplayv3",
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Request failed for game {game_id}: {e}")
            return None
