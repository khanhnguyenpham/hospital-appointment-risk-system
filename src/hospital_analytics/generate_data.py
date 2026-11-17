from __future__ import annotations

import hashlib
from datetime import datetime

import numpy as np
import pandas as pd

from .config import RANDOM_SEED, RAW_APPOINTMENTS, ensure_directories

DEPARTMENTS = {
    "Internal Medicine": {"weight": 0.27, "base_wait": 24, "duration": 18},
    "Pediatrics": {"weight": 0.20, "base_wait": 19, "duration": 16},
    "Cardiology": {"weight": 0.15, "base_wait": 31, "duration": 24},
    "Orthopedics": {"weight": 0.15, "base_wait": 27, "duration": 21},
    "Ophthalmology": {"weight": 0.13, "base_wait": 22, "duration": 17},
    "Endocrinology": {"weight": 0.10, "base_wait": 25, "duration": 20},
}

AGE_GROUPS = ["0-17", "18-24", "25-44", "45-64", "65+"]
DISTRICTS = ["Central Buon Ma Thuot", "Outer Buon Ma Thuot", "Outside Buon Ma Thuot"]
INSURANCE_TYPES = ["Public", "Private", "Self-pay"]


def _sigmoid(value: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-value))


def _patient_id(index: int, seed: int) -> str:
    raw = f"portfolio-patient-{seed}-{index}".encode()
    return hashlib.sha256(raw).hexdigest()[:12]


def generate_appointments(rows: int = 8000, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2025-01-01")
    end = pd.Timestamp("2026-10-31")
    day_count = (end - start).days + 1

    appointment_dates = start + pd.to_timedelta(rng.integers(0, day_count, rows), unit="D")
    # Outpatient activity is lower on Sundays. Move most Sunday rows to Monday.
    sunday_mask = appointment_dates.dayofweek == 6
    appointment_dates = appointment_dates.where(~sunday_mask, appointment_dates + pd.offsets.Day(1))

    department_names = list(DEPARTMENTS)
    department_weights = [DEPARTMENTS[name]["weight"] for name in department_names]
    departments = rng.choice(department_names, size=rows, p=department_weights)

    hours = rng.choice(
        np.arange(7, 17),
        size=rows,
        p=[0.08, 0.13, 0.13, 0.12, 0.10, 0.08, 0.10, 0.10, 0.09, 0.07],
    )
    lead_days = np.clip(rng.gamma(shape=2.2, scale=5.0, size=rows).round().astype(int), 0, 60)
    booked_at = (
        appointment_dates - pd.to_timedelta(lead_days, unit="D") + pd.to_timedelta(rng.integers(8, 17, rows), unit="h")
    )

    patient_pool = max(1800, rows // 3)
    patient_numbers = rng.integers(0, patient_pool, size=rows)
    patient_ids = np.array([_patient_id(int(value), seed) for value in patient_numbers])

    age_groups = rng.choice(AGE_GROUPS, size=rows, p=[0.16, 0.11, 0.31, 0.29, 0.13])
    districts = rng.choice(DISTRICTS, size=rows, p=[0.46, 0.32, 0.22])
    insurance = rng.choice(INSURANCE_TYPES, size=rows, p=[0.71, 0.12, 0.17])
    prior_visits = np.clip(rng.poisson(2.3, rows), 0, 15)
    prior_no_shows = np.minimum(rng.binomial(prior_visits, 0.13), 5)

    reminder_probability = np.where(lead_days >= 2, 0.78, 0.38)
    reminder_sent = rng.binomial(1, reminder_probability)

    rainy_season = np.isin(appointment_dates.month, [5, 6, 7, 8, 9, 10]).astype(int)
    monday = (appointment_dates.dayofweek == 0).astype(int)
    outside_city = (districts == "Outside Buon Ma Thuot").astype(int)
    early_hour = (hours <= 8).astype(int)
    self_pay = (insurance == "Self-pay").astype(int)

    log_odds = (
        -2.25
        + 0.045 * lead_days
        + 0.70 * prior_no_shows
        - 0.62 * reminder_sent
        + 0.28 * rainy_season
        + 0.24 * monday
        + 0.35 * outside_city
        + 0.18 * early_hour
        + 0.16 * self_pay
        + rng.normal(0, 0.25, rows)
    )
    no_show = rng.binomial(1, _sigmoid(log_odds))
    cancellation_probability = np.clip(0.035 + 0.002 * lead_days, 0.03, 0.15)
    cancelled = rng.binomial(1, cancellation_probability)
    status = np.where(cancelled == 1, "Cancelled", np.where(no_show == 1, "No-show", "Completed"))
    no_show = (status == "No-show").astype(int)

    scheduled_time = appointment_dates + pd.to_timedelta(hours, unit="h")
    arrival_offset = np.clip(rng.normal(-7, 13, rows).round(), -45, 45)
    arrival_time = scheduled_time + pd.to_timedelta(arrival_offset, unit="m")

    base_wait = np.array([DEPARTMENTS[name]["base_wait"] for name in departments])
    peak_effect = np.where(np.isin(hours, [9, 10, 14]), 8, 0)
    wait_minutes = np.clip(rng.normal(base_wait + peak_effect, 11), 2, 95).round(1)
    service_start_time = arrival_time + pd.to_timedelta(wait_minutes, unit="m")
    base_duration = np.array([DEPARTMENTS[name]["duration"] for name in departments])
    consultation_minutes = np.clip(rng.normal(base_duration, 5), 6, 55).round(1)

    not_completed = status != "Completed"
    arrival_time = pd.Series(arrival_time).mask(not_completed)
    service_start_time = pd.Series(service_start_time).mask(not_completed)
    wait_minutes = pd.Series(wait_minutes).mask(not_completed)
    consultation_minutes = pd.Series(consultation_minutes).mask(not_completed)

    frame = pd.DataFrame(
        {
            "appointment_id": [f"APT-{i + 1:06d}" for i in range(rows)],
            "patient_id": patient_ids,
            "appointment_date": appointment_dates,
            "booked_at": booked_at,
            "department": departments,
            "appointment_hour": hours,
            "age_group": age_groups,
            "district": districts,
            "insurance_type": insurance,
            "prior_visits": prior_visits,
            "prior_no_shows": prior_no_shows,
            "reminder_sent": reminder_sent,
            "status": status,
            "arrival_time": arrival_time,
            "service_start_time": service_start_time,
            "wait_minutes": wait_minutes,
            "consultation_minutes": consultation_minutes,
            "no_show": no_show,
            "lead_days": lead_days,
            "weekday": appointment_dates.dayofweek,
            "month": appointment_dates.month,
        }
    )
    return frame.sort_values(["appointment_date", "appointment_hour", "appointment_id"]).reset_index(drop=True)


def save_raw_data(rows: int = 8000, seed: int = RANDOM_SEED) -> pd.DataFrame:
    ensure_directories()
    frame = generate_appointments(rows=rows, seed=seed)
    frame.to_csv(RAW_APPOINTMENTS, index=False, date_format="%Y-%m-%d %H:%M:%S")
    return frame


if __name__ == "__main__":
    data = save_raw_data()
    print(f"Generated {len(data):,} appointments at {datetime.now():%Y-%m-%d %H:%M}")
