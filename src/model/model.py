import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


class WinProbabilityModel:
    """Logistic Regression Model for predicting home team win probability."""

    def __init__(self):
        self.raw_features = [
            "period",
            "pc_time",
            "away_score",
            "home_score",
            "possession_team",
            "event_team",
            "event_code"
        ]
        self.scaled_features = [f"{feature}_scaled" for feature in self.raw_features]
        self.target = "home_win"

        self.scaler = StandardScaler()
        self.model = LogisticRegression(
            max_iter=1000,           # Allow more iterations to ensure the model converges
            solver="lbfgs",          # Optimization algorithm (Limited-memory BFGS)
            class_weight="balanced"  # Adjusts for imbalanced target classes automatically
        )

        self.event_codes = None

    def _preprocess(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """Preprocess dataframe to handle missing data, encode events, and scale features."""
        df = df.dropna(subset=["home_possession"]).copy()

        # Fill missing event data
        df["event_msg_type"] = df["event_msg_type"].fillna("MISSING")
        df["event_msg_action_type"] = df["event_msg_action_type"].fillna("Unknown")

        # Reformat fouls
        is_foul = df["event_msg_type"] == "Foul"
        df.loc[is_foul, "event_msg_type"] += " - " + df.loc[is_foul, "event_msg_action_type"]

        # Encode event messages for model
        if fit:
            self.event_codes = df["event_msg_type"].astype("category").cat.categories
        df["event_code"] = pd.Categorical(df["event_msg_type"], categories=self.event_codes).codes

        # Scale features
        scaler_func = self.scaler.fit_transform if fit else self.scaler.transform
        df[self.scaled_features] = scaler_func(df[self.raw_features])

        return df

    def fit(self, df: pd.DataFrame):
        """Fit logistic regression model to training data with target column."""
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

    def predict_win_probs(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates away and home teams win probability for each play."""
        df = self._preprocess(df, fit=False)
        X = df[self.scaled_features].values

        probs = self.model.predict_proba(X)
        df = df.assign(
            predicted_winner=self.model.predict(X),
            home_win_probability=probs[:, 1],
            away_win_probability=probs[:, 0],
        )
        return df
