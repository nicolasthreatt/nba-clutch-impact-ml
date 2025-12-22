import requests
import time

from typing import Dict, Optional, List
from requests.adapters import HTTPAdapter, Retry


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

    def __init__(self, timeout: int = 30, retries: int = 3):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.timeout = timeout

        retry_strategy = Retry(
            total=retries,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

    def load_games(self, season: str) -> Optional[Dict]:
        """Loads game data from the leaguegamefinder NBA API."""
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
        """Loads play-by-play data for a specific game ID."""
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

    def load_play_by_play_games(
        self,
        game_ids: List[str],
        delay: float = 0.5,
    ) -> Dict[str, Optional[Dict]]:
        """Loads play-by-play data for multiple games safely."""
        results = {}

        for game_id in game_ids:
            print(f"Getting play-by-play data for game ID: {game_id}")
            time.sleep(delay)

            data = self.load_play_by_play(game_id)
            if data is None:
                print(f"No play-by-play data for game ID: {game_id}")

            results[game_id] = data

        return results
