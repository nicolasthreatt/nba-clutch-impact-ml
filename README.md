# nba-clutch-impact-ml

ML pipelines for NBA clutch analytics that ingests NBA play-by-play data, filters to clutch moments, trains a win-probability model, and computes a clutch impact score based on win-probability deltas.

## Motivation
Clutch performance can swing close games. This repo provides both offline analysis and live win-probability scoring so you can quantify late-game impact for teams and players.

## Setup
1. Create a Python 3.10+ environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Data
Data is pulled from NBA endpoints:
- Batch: `stats.nba.com` (`leaguegamefinder`, `playbyplayv3`)
- Live: `cdn.nba.com` live play-by-play JSON

Batch data is cached in SQLite at `data/nba_clutch.sqlite`.

## Usage
### Batch pipeline
1. Fetch clutch events for a season.
2. Cache clutch events in SQLite.
3. Train `WinProbabilityModel`.
4. Evaluate accuracy and Brier score.
5. Predict win probabilities.
6. Compute clutch impact ratings.

CLI args:
- `--train-season`: training season, defaults to `2024-25`
- `--test-season`: evaluation season, defaults to `2025-26`
- `--refresh`: ignore cached SQLite data and refetch season data from NBA APIs
- `--dry-run`: run the batch pipeline without writing to SQLite or saving the model

Examples:
```bash
python batch.py --train-season 2024-25 --test-season 2025-26
python batch.py --train-season 2024-25 --test-season 2025-26 --refresh
python batch.py --train-season 2024-25 --test-season 2025-26 --dry-run
```

### Streaming pipeline
Requires a local Kafka broker at `localhost:9092`.

CLI args:
- `--game_id`: NBA game ID to stream, required
- `--topic`: Kafka topic name, defaults to `play-by-test`

Start streaming:
```bash
python streaming.py --game_id 0022400001
python streaming.py --game_id 0022400001 --topic play-by-test
```

This starts a producer that polls live play-by-play and a consumer that loads a trained model and runs inference on each event.

## Training
The model lives in `src/model/model.py` and uses logistic regression. Training expects a dataframe with features:
- `period`
- `pc_time`
- `away_score`
- `home_score`
- `possession_team`
- `event_team`
- `event_msg_type`
- `event_msg_action_type`
- `home_win` (Target)

## Evaluation
- Accuracy: `WinProbabilityModel.evaluate()`
- Brier score: `WinProbabilityModel.brier_score()`
- Calibration curves: `src/plots/calibration_curve.py`

## Example Outputs
- Per-event win probabilities (`home_win_probability`, `away_win_probability`)
- Player clutch impact ratings (sum of win-probability deltas)
- Aggregated clutch leaderboard

## Layout
- `batch.py`: batch training and evaluation entry point
- `streaming.py`: live producer/consumer entry point
- `src/api/`: NBA API client
- `src/data/`: data processing and clutch filtering
- `src/model/`: win-probability model
- `src/analysis/`: clutch impact scoring
- `src/topics/`: Kafka producer/consumer
- `src/classes/`: domain objects and enums
