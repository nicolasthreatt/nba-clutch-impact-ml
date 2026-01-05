import threading

from kafka import KafkaConsumer


class Consumer(threading.Thread):
    def __init__(self, game_id: str):
        super().__init__()
        self.stop_event = threading.Event()
        self.bootstrap_servers = "localhost:9092"
        self.topic = f"{game_id}-pbp-live"
        self.consumer = None

    def stop(self):
        self.stop_event.set()
        if self.consumer:
            self.consumer.close()
            print("Consumer stopped.")

    def run(self):
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset='earliest',
            group_id='nba-clutch',
            enable_auto_commit=True,
            consumer_timeout_ms=500
        )

        try:
            while not self.stop_event.is_set():
                for message in self.consumer:
                    if self.stop_event.is_set():
                        break
                    print(message.value.decode("utf-8"))

        except Exception as e:
            print(f"Consumer exception: {e}")  # TODO: ADD LOGGING

        finally:
            self.stop()
