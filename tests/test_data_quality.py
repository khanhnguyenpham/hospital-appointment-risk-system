import pandas as pd

from hospital_analytics.data_quality import validate_appointments
from hospital_analytics.generate_data import generate_appointments


def test_generated_data_passes_quality_checks():
    frame = generate_appointments(rows=500, seed=7)
    assert validate_appointments(frame) == []


def test_duplicate_appointment_is_detected():
    frame = generate_appointments(rows=50, seed=7)
    duplicate = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    assert "appointment_id contains duplicates" in validate_appointments(duplicate)


def test_no_show_target_must_match_status():
    frame = generate_appointments(rows=50, seed=7)
    frame.loc[0, "no_show"] = 1 - int(frame.loc[0, "no_show"])
    assert "no_show does not match status" in validate_appointments(frame)

