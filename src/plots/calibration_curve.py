import matplotlib.pyplot as plt
import pandas as pd

from sklearn.calibration import calibration_curve


def plot_calibration_curve(
    df: pd.DataFrame,
    prob_col: str = "home_win_probability",
    target_col: str = "home_win",
    n_bins: int = 10,
):
    """Plot a calibration curve for predicted win probabilities."""
    if prob_col not in df.columns or target_col not in df.columns:
        raise ValueError(f"Missing columns: {prob_col} or {target_col}")

    y_true = df[target_col].astype(int)
    y_prob = df[prob_col].astype(float)

    fraction_positives, mean_predicate = calibration_curve(
        y_true,
        y_prob,
        n_bins=n_bins,
        strategy="uniform",
    )

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(mean_predicate, fraction_positives, marker="o", label="Model")
    ax.plot([0, 1], [0, 1], linestyle="--", color="black", label="Perfect")

    ax.set_title("Calibration Curve")
    ax.set_xlabel("Mean Predicted Probability")
    ax.set_ylabel("Fraction of Positives")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(loc="best")

    fig.tight_layout()
    plt.show()
