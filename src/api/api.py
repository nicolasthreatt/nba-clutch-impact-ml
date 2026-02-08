import logging
import random
import requests
import time

from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter, Retry
from typing import Any, Dict, Optional, List

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
        self.timeout = (5, timeout)

        retry_strategy = Retry(
            total=retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={"GET"},
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)

        self.session = requests.Session()
        self.session.mount("https://", adapter)

    def load_live_game_boxscore(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Loads live boxscore data."""
        live_url = f"{self.BASE_LIVE_URL}boxscore/boxscore_{game_id}.json"

        try:
            response = self.session.get(
                live_url,
                headers=self.LIVE_HEADERS,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.exception("Live game request failed for game %s: %s", game_id, e)
            return None


    def load_season_games(self, season: str) -> Optional[Dict[str, Any]]:
        """Loads game data from the leaguegamefinder NBA API."""
        params = {
            "PlayerOrTeam": "T",
            "LeagueID": "00",
            "Season": season,
            "SeasonType": "Regular Season",
        }

        try:
            response = self.session.get(
                self.BASE_BATCH_URL + "leaguegamefinder",
                params=params,
                headers=self.BATCH_HEADERS,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.exception("Request failed for season %s: %s", season, e)
            return None

    def load_play_by_play_games(
        self,
        game_ids: List[str],
        delay: float = 0.5,
        max_workers: int = 3,
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """Loads play-by-play data for multiple games."""
        results = {}

        def store_result(game_id: str, data: Optional[Dict[str, Any]]):
            """Store a fetch result."""
            if data is None:
                logger.warning("No play-by-play data for game ID: %s", game_id)
                time.sleep(max(0.1, delay / 2))
            results[game_id] = data

        def fetch(game_id: str) -> Optional[Dict[str, Any]]:
            time.sleep(delay + random.uniform(0, 0.2))
            return self.load_play_by_play_batch(game_id)

        if max_workers <= 1:
            for game_id in game_ids:
                logger.info("Getting play-by-play data for game ID: %s", game_id)
                data = fetch(game_id)
                store_result(game_id, data)
            return results

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_games = {executor.submit(fetch, game_id): game_id for game_id in game_ids}
            for future_game in as_completed(future_games):
                game_id = future_games[future_game]
                try:
                    data = future_game.result()
                except Exception:
                    logger.exception("PBP fetch failed for game ID: %s", game_id)
                    data = None
                store_result(game_id, data)

        return results

    def load_play_by_play_batch(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Batch play-by-play data. Use for backfills and reprocessing."""
        params = {
            "GameID": game_id,
            "StartPeriod": 4,
            "EndPeriod": 10,
        }

        try:
            response = self.session.get(
                self.BASE_BATCH_URL + "playbyplayv3",
                params=params,
                headers=self.BATCH_HEADERS,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.exception("Batch PBP request failed for game %s: %s", game_id, e)
            return None

    def load_play_by_play_live(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Live play-by-play data (polling)."""
        live_url = f"{self.BASE_LIVE_URL}playbyplay/playbyplay_{game_id}.json"

        try:
            response = self.session.get(
                live_url,
                headers=self.LIVE_HEADERS,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.exception("Live PBP request failed for game %s: %s", game_id, e)
            return None
