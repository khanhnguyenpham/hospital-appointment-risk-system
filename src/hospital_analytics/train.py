from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import METRICS_PATH, MODEL_PATH, RANDOM_SEED, ensure_directories
from .features import CATEGORICAL_FEATURES, MODEL_FEATURES, NUMERIC_FEATURES, TARGET, chronological_split, modelling_frame


def build_model() -> Pipeline:
    numeric_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        [
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        [
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_SEED)),
        ]
    )


def _best_f1_threshold(y_true: pd.Series, probabilities: np.ndarray) -> float:
    thresholds = np.arange(0.20, 0.81, 0.01)
    scores = [f1_score(y_true, probabilities >= threshold, zero_division=0) for threshold in thresholds]
    return float(thresholds[int(np.argmax(scores))])


def _metrics(y_true: pd.Series, probabilities: np.ndarray, threshold: float) -> dict[str, float]:
    predictions = (probabilities >= threshold).astype(int)
    return {
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 4),
        "accuracy": round(float(accuracy_score(y_true, predictions)), 4),
        "precision": round(float(precision_score(y_true, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, predictions, zero_division=0)), 4),
    }


def train_and_save(frame: pd.DataFrame) -> tuple[Pipeline, dict]:
    ensure_directories()
    model_data = modelling_frame(frame)
    train, validation, test = chronological_split(model_data)

    model = build_model()
    model.fit(train[MODEL_FEATURES], train[TARGET])

    validation_probabilities = model.predict_proba(validation[MODEL_FEATURES])[:, 1]
    threshold = _best_f1_threshold(validation[TARGET], validation_probabilities)
    test_probabilities = model.predict_proba(test[MODEL_FEATURES])[:, 1]

    metrics = {
        "threshold": round(threshold, 2),
        "train_rows": int(len(train)),
        "validation_rows": int(len(validation)),
        "test_rows": int(len(test)),
        "test_period_start": str(test["appointment_date"].min().date()),
        "test_period_end": str(test["appointment_date"].max().date()),
        "test": _metrics(test[TARGET], test_probabilities, threshold),
    }

    joblib.dump({"model": model, "threshold": threshold, "features": MODEL_FEATURES}, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return model, metrics

