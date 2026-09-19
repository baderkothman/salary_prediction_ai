"""Feature/preprocessing definition shared only within the ml/ training code.

The deployed backend never imports this — it loads the already-fitted
Pipeline (preprocessing + model serialized together), so this module's only
consumer is ml/src/training/train.py. This keeps the invariant from
architecture.md #4: preprocessing and model can never drift apart because
there is exactly one copy of the transform logic, and it travels inside the
joblib artifact.
"""

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

CATEGORICAL_FEATURES = [
    "experience_level",
    "employment_type",
    "job_title",
    "employee_residence",
    "company_location",
    "company_size",
]

# remote_ratio is numeric (0/50/100) but ordered/meaningful as a number
# (on-site < hybrid < remote), so it stays a passthrough numeric feature
# rather than being one-hot encoded like the other categoricals.
NUMERIC_FEATURES = ["work_year", "remote_ratio"]

FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("numeric", "passthrough", NUMERIC_FEATURES),
        ]
    )
