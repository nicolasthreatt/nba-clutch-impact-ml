import json
import threading

from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic

from src.api.api import API
from src.classes.PlayByPlayLive import PlayByPlayLive

class Producer(threading.Thread):
    def __init__(self, game_id: str, poll_interval: float = 0.25):
        super().__init__()
        self.stop_event = threading.Event()
        self.bootstrap_servers = "localhost:9092"
        self.game_id = game_id
        self.topic = f"{self.game_id}-pbp-live"
        self.api = API(timeout=3)
        self.producer = None
        self.last_action_number = None
        self.poll_interval = poll_interval

        self._create_topic_if_missing()

    def _create_topic_if_missing(self):
        admin = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers, client_id='test')
        existing_topics = admin.list_topics()

        if self.topic not in existing_topics:
            admin.create_topics([NewTopic(name=self.topic, num_partitions=1, replication_factor=1)])

        admin.close()

    def stop(self):
        self.stop_event.set()
        if self.producer:
            self.producer.flush()
            self.producer.close()
            print("Producer stopped.")

    def run(self):
        self.producer = KafkaProducer(bootstrap_servers=self.bootstrap_servers)  # TODO: ADD CHECKPOINTING

        try:
            while not self.stop_event.is_set():
                data = self.api.load_play_by_play_live(self.game_id)
                if not data:
                    self.stop_event.wait(self.poll_interval)
                    continue

                actions = data.get("game", {}).get("actions", [])
                for action in actions:
                    action_number = action.get("actionNumber")
                    if self.last_action_number is not None and action_number <= self.last_action_number:
                        continue

                    pbp = PlayByPlayLive(self.game_id, action)
                    self.producer.send(self.topic, value=json.dumps(pbp.__dict__).encode("utf-8"))

                    self.last_action_number = action_number

                self.stop_event.wait(self.poll_interval)

        except Exception as e:
            print(f"Producer exception: {e}")  # TODO: ADD LOGGING

        finally:
            self.stop()
