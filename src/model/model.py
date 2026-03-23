import joblib
import pandas as pd

from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import brier_score_loss


class WinProbabilityModel:
    """Logistic Regression Model for predicting home team win probability."""

    MODEL_PATH = "models/win_probability.joblib"

    def __init__(self):
        # Features
        self.raw_features = [
            "period",
            "pc_time",
            "away_score",
            "home_score",
            "possession_team",
            "event_team",
        ]
        self.feature_columns = self.raw_features + ["event_code"]
        self.scaled_features = [f"{feature}_scaled" for feature in self.feature_columns]
        self.event_codes = None

        # Target
        self.target = "home_win"

        # Model
        self.scaler = StandardScaler()
        self.model = LogisticRegression(
            max_iter=1000,            # Allow more iterations to ensure the model converges
            solver="lbfgs",           # Optimization algorithm (Limited-memory BFGS)
            class_weight="balanced",  # Adjusts for imbalanced target classes automatically
        )

    def _preprocess(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """Preprocess dataframe to handle missing data, encode events, and scale features."""
        if not fit and self.event_codes is None:
            raise RuntimeError("WinProbabilityModel must be fit or loaded before inference")

        # Drop rows missing required features
        df = df.dropna(subset=self.raw_features)

        # Fill missing events
        df["event_msg_type"] = df["event_msg_type"].fillna("MISSING")
        df["event_msg_action_type"] = df["event_msg_action_type"].fillna("Unknown")

        # Reformat enum columns
        df["possession_team"] = df["possession_team"].astype(int)
        df["event_team"] = df["event_team"].astype(int)

        # Reformat fouls
        is_foul = df["event_msg_type"] == "Foul"
        df.loc[is_foul, "event_msg_type"] += " - " + df.loc[is_foul, "event_msg_action_type"]

        # Encode event messages
        if fit:
            self.event_codes = df["event_msg_type"].astype("category").cat.categories
        df["event_code"] = pd.Categorical(df["event_msg_type"], categories=self.event_codes).codes

        # Scale features
        scale = self.scaler.fit_transform if fit else self.scaler.transform
        df[self.scaled_features] = scale(df[self.feature_columns])

        return df

    def fit(self, df: pd.DataFrame):
        """Fits logistic regression model on labeled training data."""
        df = self._preprocess(df, fit=True)

        X = df[self.scaled_features].values
        y = df[self.target].values

        self.model.fit(X, y)

    def evaluate(self, df: pd.DataFrame) -> float:
        """Evaluate model accuracy on the given dataframe.

           Accuracy is the percentage of correctly predicted label
            = correct_predictions / total_predictions
        """
        df = self._preprocess(df, fit=False)

        X = df[self.scaled_features].values
        y = df[self.target].values

        return self.model.score(X, y)

    def brier_score(self, df: pd.DataFrame) -> float:
        """Calculate Brier score for predicted home win probabilities."""
        df = self._preprocess(df, fit=False)

        X = df[self.scaled_features].values
        y_true = df[self.target].values
        y_prob = self.model.predict_proba(X)[:, 1]

        return float(brier_score_loss(y_true, y_prob))

    def predict_win_probs(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates away and home teams win probability for each play."""
        df = self._preprocess(df, fit=False)

        X = df[self.scaled_features].values
        probs = self.model.predict_proba(X)

        return df.assign(
            predicted_winner=self.model.predict(X),
            home_win_probability=probs[:, 1],
            away_win_probability=probs[:, 0],
        )

    def save(self, path: str = None):
        """Save model artifacts locally."""
        path = Path(path or self.MODEL_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(
            {
                "model": self.model,
                "scaler": self.scaler,
                "event_codes": self.event_codes,
                "raw_features": self.raw_features,
                "feature_columns": self.feature_columns,
                "scaled_features": self.scaled_features,
            },
            path,
        )

    @classmethod
    def load(cls, path: str = None) -> "WinProbabilityModel":
        """Load saved model locally."""
        data = joblib.load(path or cls.MODEL_PATH)

        instance = cls()
        instance.model = data["model"]
        instance.scaler = data["scaler"]
        instance.event_codes = data["event_codes"]
        instance.raw_features = data["raw_features"]
        instance.feature_columns = data.get("feature_columns", instance.raw_features + ["event_code"])
        instance.scaled_features = data["scaled_features"]

        return instance
