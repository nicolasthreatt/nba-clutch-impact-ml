import argparse

from src.classes.Mode import Mode


def cli(mode: Mode = Mode.STREAMING) -> argparse.Namespace:
    """Parse command line arguments for the requested pipeline."""
    parser = argparse.ArgumentParser(description="NBA Clutch Impact Command Line Interface")

    if mode == Mode.BATCH:
        parser.description = "NBA clutch batch pipeline"
        parser.add_argument("--train-season", type=str, default="2024-25", help="Training season")
        parser.add_argument("--test-season", type=str, default="2025-26", help="Evaluation season")
        parser.add_argument(
            "--refresh",
            action="store_true",
            help="Refresh SQLite cache from NBA APIs before training",
        )
    elif mode == Mode.STREAMING:
        parser.add_argument("--game_id", type=str, required=True, help="Game ID")
        parser.add_argument("--topic", type=str, required=False, default="play-by-test", help="Consumer topic name")
    else:
        raise ValueError(f"Unsupported CLI mode: {mode}")

    return parser.parse_args()
