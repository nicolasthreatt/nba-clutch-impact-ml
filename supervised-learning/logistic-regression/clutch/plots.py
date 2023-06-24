# plots.py
import matplotlib.pyplot as plt
import pandas as pd

def plot_accurary(df: pd.DataFrame) -> None:
    
    fig, ax = plt.subplots(figsize=(15, 10))
    
    home_win_filter = df['home_win'] == 1
    away_win_filter = df['home_win'] == 0

    ax.scatter(
        df.loc[home_win_filter, ''].values,
        df.loc[home_win_filter, ''].values,
        c='green',
        label='Home Team Win',
        alpha=0.5
    )
    ax.scatter(
        df.loc[away_win_filter, ''].values,
        df.loc[away_win_filter, ''].values,
        c='red',
        label='Away Team Win',
        alpha=0.5
    )

    ax.axhline(y=0.5, color='black', linestyle='--')

    ax.axhspan(0.5, 1, alpha=0.2, color='green')
    ax.axhspan(0, 0.4999, alpha=0.2, color='red')

    ax.set_xlabel('Actual Outcome')
    ax.set_ylabel('Predicted Outcome')
    ax.set_title('Logistic Regression Model Accuracy')
    # ax.set_ylim(0, 1)

    ax.legend(loc='best')

    fig.tight_layout()
    plt.show()
