from __future__ import annotations

import pandas as pd

TARGET = "no_show"
NUMERIC_FEATURES = [
    "appointment_hour",
    "weekday",
    "month",
    "lead_days",
    "prior_visits",
    "prior_no_shows",
    "reminder_sent",
]
CATEGORICAL_FEATURES = ["department", "age_group", "district", "insurance_type"]
MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def modelling_frame(frame: pd.DataFrame) -> pd.DataFrame:
    eligible = frame.loc[frame["status"] != "Cancelled", MODEL_FEATURES + [TARGET, "appointment_date", "appointment_id"]].copy()
    return eligible.sort_values("appointment_date").reset_index(drop=True)


def chronological_split(frame: pd.DataFrame, train_fraction: float = 0.70, validation_fraction: float = 0.15):
    if train_fraction <= 0 or validation_fraction <= 0 or train_fraction + validation_fraction >= 1:
        raise ValueError("Split fractions must be positive and leave data for testing")
    ordered = frame.sort_values("appointment_date").reset_index(drop=True)
    train_end = int(len(ordered) * train_fraction)
    validation_end = int(len(ordered) * (train_fraction + validation_fraction))
    return ordered.iloc[:train_end], ordered.iloc[train_end:validation_end], ordered.iloc[validation_end:]

