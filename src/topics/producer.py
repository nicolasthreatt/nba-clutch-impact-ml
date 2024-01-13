# Description: Producer class for the play-by-play streming topic
import json
import requests
import time
import threading
from kafka import KafkaProducer
from src.classes.PlayByPlay import PlayByPlayLive

HEADERS = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'x-nba-stats-token': 'true',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'x-nba-stats-origin': 'stats',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Referer': 'https://stats.nba.com/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
}

class Producer(threading.Thread):
    def __init__(self, game_id: str):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        self.game_id = "0042200401"

    def stop(self):
        self.stop_event.set()

    def run(self):
        producer = KafkaProducer(bootstrap_servers='localhost:9092')

        # while not self.stop_event.is_set():
        while True:
            play_by_play = self.play_by_play_data(self.game_id)

            for play in play_by_play:
                play = PlayByPlayLive(play)
                producer.send(self.game_id + "-pbp-live", value=json.dumps(play.__dict__).encode('utf-8'))
                break

            time.sleep(5)  # Adjust the interval as needed

        producer.close()

    def play_by_play_data(self, gameId: str) -> dict:
        # Move lines (37-45 here) to a function or maybe into api.py
        play_by_play_url = "https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{}.json".format(gameId)
        response = requests.get(url=play_by_play_url, headers=HEADERS)

        if response.status_code == 200:
            json_data = response.json()
            play_by_play = json_data['game']['actions']
            return play_by_play
