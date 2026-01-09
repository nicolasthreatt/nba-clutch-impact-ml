import logging
import requests
import time

from typing import Dict, Optional, List
from requests.adapters import HTTPAdapter, Retry

logger = logging.getLogger(__name__)


class API:
    """Client interface for interacting with stats.nba.com endpoints."""

    BASE_BATCH_URL = "https://stats.nba.com/stats/"
    BASE_LIVE_URL = "https://cdn.nba.com/static/json/liveData/"

    BATCH_HEADERS = {
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

    LIVE_HEADERS = {
        "User-Agent": ( 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) " 
            "Gecko/20100101 Firefox/72.0"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    def __init__(self, timeout: int = 30, retries: int = 3):
        self.timeout = timeout

        retry_strategy = Retry(
            total=retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={"GET"}

        )
        adapter = HTTPAdapter(max_retries=retry_strategy)

        # Batch Session
        self.batch_session = requests.Session()
        self.batch_session.headers.update(self.BATCH_HEADERS)
        self.batch_session.mount("https://", adapter)

        # Live / Real-time Session
        self.live_session = requests.Session()
        self.live_session.headers.update(self.LIVE_HEADERS)
        self.live_session.mount("https://", adapter)

    def load_live_game_boxscore(self, game_id: str) -> Optional[Dict]:
        """Loads live boxscore data."""
        live_url = f"{self.BASE_LIVE_URL}boxscore/boxscore_{game_id}.json"

        try:
            response = self.live_session.get(live_url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.exception(f"Live game request failed for game {game_id}: {e}")
            return None


    def load_season_games(self, season: str) -> Optional[Dict]:
        """Loads game data from the leaguegamefinder NBA API."""
        params = {
            "PlayerOrTeam": "T",
            "LeagueID": "00",
            "Season": season,
            "SeasonType": "Regular Season",
        }

        try:
            response = self.batch_session.get(
                self.BASE_BATCH_URL + "leaguegamefinder",
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.exception(f"Request failed for season {season}: {e}")
            return None

    def load_play_by_play_games(
        self,
        game_ids: List[str],
        delay: float = 0.5,
    ) -> Dict[str, Optional[Dict]]:
        """Loads play-by-play data for multiple games."""
        results = {}

        for game_id in game_ids:
            logger.info(f"Getting play-by-play data for game ID: {game_id}")
            time.sleep(delay)

            data = self.load_play_by_play_batch(game_id)
            if data is None:
                logger.warning(f"No play-by-play data for game ID: {game_id}")

            results[game_id] = data

        return results

    def load_play_by_play_batch(self, game_id: str) -> Optional[Dict]:
        """Batch play-by-play data. Use for backfills and reprocessing."""
        params = {
            "GameID": game_id,
            "StartPeriod": 4,
            "EndPeriod": 10,
        }

        try:
            response = self.batch_session.get(
                self.BASE_BATCH_URL + "playbyplayv3",
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.exception(f"Batch PBP request failed for game {game_id}: {e}")
            return None

    def load_play_by_play_live(self, game_id: str) -> Optional[Dict]:
        """Live play-by-play data (polling)."""
        live_url = f"{self.BASE_LIVE_URL}playbyplay/playbyplay_{game_id}.json"

        try:
            response = self.live_session.get(live_url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.exception(f"Live PBP request failed for game {game_id}: {e}")
            return None
