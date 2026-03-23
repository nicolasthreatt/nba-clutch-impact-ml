import json
import logging
import pandas as pd
import threading

from kafka import KafkaConsumer, KafkaProducer

from src.model.model import WinProbabilityModel

logger = logging.getLogger(__name__)


class Consumer(threading.Thread):
    def __init__(self, game_id: str):
        super().__init__()

        # Thread Info
        self.stop_event = threading.Event()

        # Kafka Info
        self.bootstrap_servers = "localhost:9092"
        self.topic = f"{game_id}-pbp-live"
        self.output_topic = f"{game_id}-wp-live"
        # self.output_topic = f"{game_id}-clutch-impact-live"
        self.consumer = None
        self.producer = None

        # Model Info
        self.model = WinProbabilityModel.load()
        self._prime_model()  # Avoid first-message latency

        logger.info("Initializing Consumer for topic=%s", self.topic)

    def _prime_model(self):
        dummy = pd.DataFrame(
            [
                {
                    "period": 4,
                    "pc_time": 300,
                    "away_score": 0,
                    "home_score": 0,
                    "possession_team": 0,
                    "event_team": 0,
                    "event_msg_type": "MISSING",
                    "event_msg_action_type": "Unknown",
                    "home_win": 0,
                }
            ]
        )
        self.model.predict_win_probs(dummy)

    def stop(self):
        logger.info("Stopping Consumer thread")
        self.stop_event.set()
        if self.consumer:
            self.consumer.commit()  # Final Checkpoint
            self.consumer.close()
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Consumer stopped.")

    def run(self):
        logger.info("Consumer thread started")

        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id="nba-clutch",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        self.producer = KafkaProducer(bootstrap_servers=self.bootstrap_servers)

        try:
            for message in self.consumer:
                if self.stop_event.is_set():
                    break
                self._compute_win_probabilities(message.value)
                self.consumer.commit_async()  # Async offset checkpoint to reduce replays
        except Exception:
            logger.exception("Consumer exception")
        finally:
            self.stop()

    def _compute_win_probabilities(self, msg: dict):
        try:
            df_msg = pd.DataFrame([msg])
            df_predict = self.model.predict_win_probs(df_msg)

            home_wp = float(df_predict["home_win_probability"].iloc[0])
            away_wp = float(df_predict["away_win_probability"].iloc[0])

            payload = json.dumps(
                {
                    **msg,
                    "home_wp": round(home_wp, 4),
                    "away_wp": round(away_wp, 4),
                },
                indent=2,
            )
            self.producer.send(self.output_topic, value=payload.encode("utf-8"))
            logger.debug("Published win probs to topic %s", self.output_topic)

        except Exception:
            logger.exception("Publish failed for msg: %s", json.dumps(msg, indent=2))
