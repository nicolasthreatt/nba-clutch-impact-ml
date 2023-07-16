#!/usr/bin/env python
# TODO: MOVE BACK TO src/strreaming/
import json
import requests
import time
import threading
from kafka import KafkaConsumer, KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from src.classes.PlayByPlay import PlayByPlayLive

TOPIC = "play-by-test"

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
    def __init__(self):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()

    def run(self):
        producer = KafkaProducer(bootstrap_servers='localhost:9092')

        # while not self.stop_event.is_set():
        while True:
            game_id = "0042200401"
            play_by_play_url = "https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{}.json".format(game_id)
            response = requests.get(url=play_by_play_url, headers=HEADERS)

            if response.status_code == 200:
                json_data = response.json()
                play_by_play = json_data['game']['actions']
                for action in play_by_play:
                    play_by_play = PlayByPlayLive(action)
                    producer.send(TOPIC, value=json.dumps(play_by_play.__dict__).encode('utf-8'))
                break

            time.sleep(5)  # Adjust the interval as needed

        producer.close()


class Consumer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()

    def run(self):
        consumer = KafkaConsumer(
            bootstrap_servers='localhost:9092',
            auto_offset_reset='earliest',
            consumer_timeout_ms=1000
        )
        consumer.subscribe([TOPIC])

        while not self.stop_event.is_set():
            for message in consumer:
                print(message)
                if self.stop_event.is_set():
                    break

        consumer.close()


def main():
    # Create 'topic_name' Kafka topic
    # Use try-except to avoid error if topic already exists
    try:
        admin = KafkaAdminClient(bootstrap_servers='localhost:9092')
        topic = NewTopic(name='topic_name', num_partitions=1, replication_factor=1)
        admin.create_topics([topic])
    except Exception:
        pass

    # Create threads of a producer and a consumer
    tasks = [Producer(), Consumer()]

    # Start threads of a producer and a consumer to 'topic_name' Kafka topic
    for t in tasks:
        t.start()

    # Sleep for 10 seconds
    time.sleep(10)

    # Stop threads
    for task in tasks:
        task.stop()


if __name__ == "__main__":
    main()
