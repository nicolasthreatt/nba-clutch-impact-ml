# Description: Consumer class for Kafka topics
import json
import requests
import time
import threading
from kafka import KafkaConsumer, KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from src.classes.PlayByPlay import PlayByPlayLive


class Consumer(threading.Thread):
    def __init__(self, topic: str):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        self.topic = topic

    def stop(self):
        self.stop_event.set()

    def run(self):
        consumer = KafkaConsumer(
            bootstrap_servers='localhost:9092',
            auto_offset_reset='earliest',
            consumer_timeout_ms=1000
        )
        consumer.subscribe([self.topic])

        while not self.stop_event.is_set():
            for message in consumer:
                print(message)
                if self.stop_event.is_set():
                    break

        consumer.close()
