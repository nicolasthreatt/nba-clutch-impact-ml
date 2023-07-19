# Description: Producer class for the play-by-play streming topic
import json
import requests
import time
import threading
from kafka import KafkaProducer
from src.classes.PlayByPlay import PlayByPlayLive


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
            play_by_play_url = "https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{}.json".format(self.game_id)
            response = requests.get(url=play_by_play_url, headers=HEADERS)

            if response.status_code == 200:
                json_data = response.json()
                play_by_play = json_data['game']['actions']
                for action in play_by_play:
                    play_by_play = PlayByPlayLive(action)
                    # from model get prediction
                    

                    producer.send(self.game_id + "-pbp-live", value=json.dumps(play_by_play.__dict__).encode('utf-8'))
                break

            time.sleep(5)  # Adjust the interval as needed

        producer.close()
