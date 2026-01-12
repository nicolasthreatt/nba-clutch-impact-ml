import argparse


def cli() -> argparse.Namespace:
    """Command line argument parser."""

    parser = argparse.ArgumentParser(description='NBA Clutch Impact Command Line Interface')

    parser.add_argument('--game_id', type=str, required=True, help='Game ID')
    parser.add_argument('--topic', type=str, required=False, default="play-by-test", help='Consumer topic name')

    return parser.parse_args()
