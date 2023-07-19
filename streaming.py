# Description: This file is the main file for the streaming application.
import argparse
import time
import threading
from src.topics.producer import Producer
from src.topics.consumer import Consumer


def cli():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description='Streaming application')
    parser.add_argument('-id', '--game-id', type=str, required=True, help='Game ID')
    parser.add_argument('-t', '--topic', type=str, required=True, help='Topic name')
    args = parser.parse_args()

    return args


def main(game_id: str, out_topic: str):
    """Main function for the streaming application.

    Args:
        game_id (str): The game ID.
        out_topic (str): The name of the topic to write to.
    """
    
    # Create threads of a producer and a consumer
    tasks = [Producer(game_id), Consumer(out_topic)]

    # Start threads of a producer and a consumer to 'topic_name' Kafka topic
    for t in tasks:
        t.start()

    # Sleep for 10 seconds
    time.sleep(10)

    # Stop threads
    for task in tasks:
        task.stop()


if __name__ == "__main__":
    args = cli()
    main(args.game_id, args.topic)
