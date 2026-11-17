from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {
    "appointment_id",
    "patient_id",
    "appointment_date",
    "booked_at",
    "department",
    "appointment_hour",
    "age_group",
    "district",
    "insurance_type",
    "prior_visits",
    "prior_no_shows",
    "reminder_sent",
    "status",
    "no_show",
    "lead_days",
}


def validate_appointments(frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    missing_columns = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing_columns:
        errors.append(f"Missing columns: {', '.join(missing_columns)}")
        return errors

    if frame["appointment_id"].duplicated().any():
        errors.append("appointment_id contains duplicates")
    if frame["patient_id"].isna().any():
        errors.append("patient_id contains null values")
    if not frame["appointment_hour"].between(7, 16).all():
        errors.append("appointment_hour must be between 7 and 16")
    if (frame["lead_days"] < 0).any():
        errors.append("lead_days cannot be negative")
    if (frame["prior_no_shows"] > frame["prior_visits"]).any():
        errors.append("prior_no_shows cannot exceed prior_visits")
    if not set(frame["status"].dropna()).issubset({"Completed", "No-show", "Cancelled"}):
        errors.append("status contains an unexpected value")
    expected_target = (frame["status"] == "No-show").astype(int)
    if not expected_target.equals(frame["no_show"].astype(int)):
        errors.append("no_show does not match status")
    completed = frame["status"] == "Completed"
    if frame.loc[completed, "wait_minutes"].isna().any():
        errors.append("completed appointments require wait_minutes")
    return errors


def assert_valid_appointments(frame: pd.DataFrame) -> None:
    errors = validate_appointments(frame)
    if errors:
        raise ValueError("Data quality checks failed:\n- " + "\n- ".join(errors))
