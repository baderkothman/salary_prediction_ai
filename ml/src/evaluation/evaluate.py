"""Regression evaluation metrics, kept separate from training so the same
metric computation can be reused for train-set, test-set, and (later)
prediction-quality checks without redefining formulas in multiple places.
"""

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def compute_regression_metrics(y_true, y_pred) -> dict:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "r2": float(r2_score(y_true, y_pred)),
    }
