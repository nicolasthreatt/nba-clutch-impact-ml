import json
import logging
import threading

from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic

from src.api.api import API
from src.classes.PlayByPlayLive import PlayByPlayLive

logger = logging.getLogger(__name__)


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

        logger.info("Initializing Producer for topic=%s", self.topic)
        self._create_topic_if_missing()

    def _create_topic_if_missing(self):
        admin = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
        existing_topics = admin.list_topics()

        if self.topic not in existing_topics:
            logger.info("Creating Kafka topic: %s", self.topic)
            admin.create_topics([
                NewTopic(
                    name=self.topic,
                    num_partitions=1,
                    replication_factor=1
                )
            ])

        admin.close()

    def stop(self):
        logger.info("Stopping Producer thread")
        self.stop_event.set()
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Producer stopped cleanly")

    def run(self):
        logger.info("Producer thread started")

        game = self.api.load_live_game_boxscore(self.game_id)
        if not game:
            logger.error(f"No game data found for game_id {self.game_id}")
            raise RuntimeError(f"Cannot start producer: No game data for game_id {self.game_id}")

        home_team_id = game.get("game", {}).get("homeTeam", {}).get("teamId")
        away_team_id = game.get("game", {}).get("awayTeam", {}).get("teamId")
        if home_team_id is None or away_team_id is None:
            raise ValueError(f"Cannot start producer: Could not find home or away team in game data")

        self.producer = KafkaProducer(bootstrap_servers=self.bootstrap_servers)

        try:
            while not self.stop_event.is_set():
                data = self.api.load_play_by_play_live(self.game_id)
                if not data:
                    logger.debug("No data received")
                    self.stop_event.wait(self.poll_interval)
                    continue

                actions = data.get("game", {}).get("actions", [])
                for action in actions:
                    action_number = action.get("actionNumber")
                    if self.last_action_number is not None and action_number <= self.last_action_number:
                        continue

                    pbp = PlayByPlayLive(self.game_id, home_team_id, action)
                    self.producer.send(self.topic, value=json.dumps(pbp.__dict__).encode("utf-8"))
                    logger.debug("Sent action %s to topic %s", action_number, self.topic)

                    self.last_action_number = action_number

                self.stop_event.wait(self.poll_interval)

        except Exception as e:
            logger.exception(f"Producer exception: {e}")

        finally:
            self.stop()
