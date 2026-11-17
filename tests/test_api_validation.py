import pytest
from pydantic import ValidationError

from api import AppointmentRequest


def test_hour_range_is_validated():
    with pytest.raises(ValidationError):
        AppointmentRequest(
            department="Cardiology",
            appointment_hour=3,
            weekday=1,
            lead_days=10,
            prior_visits=1,
            prior_no_shows=0,
            reminder_sent=1,
            age_group="45-64",
            district="Central Buon Ma Thuot",
            insurance_type="Public",
        )
