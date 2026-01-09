import time
import logging

from src.api.cli import cli
from src.logging_config import setup_logging
from src.topics.producer import Producer
from src.topics.consumer import Consumer


def main(game_id: str):
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting streaming for game_id=%s", game_id)

    tasks = [Producer(game_id), Consumer(game_id)]

    for task in tasks:
        task.start()

    try:
        while True:
            time.sleep(1)
    finally:
        logger.info("Stopping streaming...")
        for task in tasks:
            task.stop()
        for task in tasks:
            task.join()
        logger.info("Streaming stopped.")


if __name__ == "__main__":
    args = cli()
    main(args.game_id)
