import time

from src.topics.producer import Producer
from src.topics.consumer import Consumer

from cli import cli


def main(game_id: str):
    
    tasks = [Producer(game_id), Consumer(game_id)]

    for task in tasks:
        task.start()

    try:
        while True:
            time.sleep(1)
    finally:
        for task in tasks:
            task.stop()
        for task in tasks:
            task.join()
        print("Streaming stopped.")


if __name__ == "__main__":
    args = cli()
    main(args.game_id)
