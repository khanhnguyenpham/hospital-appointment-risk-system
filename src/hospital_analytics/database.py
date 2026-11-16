from __future__ import annotations

import sqlite3

import pandas as pd

from .config import CLEAN_APPOINTMENTS, DATABASE_PATH, RAW_APPOINTMENTS, ensure_directories
from .data_quality import assert_valid_appointments
from .generate_data import DEPARTMENTS

DATE_COLUMNS = ["appointment_date", "booked_at", "arrival_time", "service_start_time"]


def load_raw_data() -> pd.DataFrame:
    frame = pd.read_csv(RAW_APPOINTMENTS, parse_dates=DATE_COLUMNS)
    return frame


def clean_and_validate(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned["appointment_date"] = pd.to_datetime(cleaned["appointment_date"]).dt.normalize()
    for column in ["appointment_hour", "prior_visits", "prior_no_shows", "reminder_sent", "no_show", "lead_days", "weekday", "month"]:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="raise").astype(int)
    assert_valid_appointments(cleaned)
    return cleaned.sort_values(["appointment_date", "appointment_hour", "appointment_id"]).reset_index(drop=True)


def build_database(frame: pd.DataFrame) -> None:
    ensure_directories()
    sql_ready = frame.copy()
    for column in DATE_COLUMNS:
        sql_ready[column] = pd.to_datetime(sql_ready[column]).dt.strftime("%Y-%m-%d %H:%M:%S")
        sql_ready.loc[frame[column].isna(), column] = None

    departments = pd.DataFrame(
        [
            {
                "department": name,
                "baseline_wait_minutes": values["base_wait"],
                "baseline_consultation_minutes": values["duration"],
            }
            for name, values in DEPARTMENTS.items()
        ]
    )

    with sqlite3.connect(DATABASE_PATH) as connection:
        sql_ready.to_sql("appointments", connection, if_exists="replace", index=False)
        departments.to_sql("departments", connection, if_exists="replace", index=False)
        connection.executescript(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_appointments_id
                ON appointments(appointment_id);
            CREATE INDEX IF NOT EXISTS idx_appointments_date
                ON appointments(appointment_date);
            CREATE INDEX IF NOT EXISTS idx_appointments_department
                ON appointments(department);
            CREATE INDEX IF NOT EXISTS idx_appointments_status
                ON appointments(status);
            """
        )


def prepare_data_store() -> pd.DataFrame:
    frame = clean_and_validate(load_raw_data())
    ensure_directories()
    frame.to_csv(CLEAN_APPOINTMENTS, index=False, date_format="%Y-%m-%d %H:%M:%S")
    build_database(frame)
    return frame

