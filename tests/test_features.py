from hospital_analytics.features import chronological_split, modelling_frame
from hospital_analytics.generate_data import generate_appointments


def test_chronological_split_has_no_time_overlap():
    frame = modelling_frame(generate_appointments(rows=1000, seed=11))
    train, validation, test = chronological_split(frame)
    assert train["appointment_date"].max() <= validation["appointment_date"].min()
    assert validation["appointment_date"].max() <= test["appointment_date"].min()
    assert len(train) + len(validation) + len(test) == len(frame)


def test_cancelled_appointments_are_not_used_for_modelling():
    raw = generate_appointments(rows=500, seed=11)
    model_data = modelling_frame(raw)
    cancelled_ids = set(raw.loc[raw["status"] == "Cancelled", "appointment_id"])
    assert cancelled_ids.isdisjoint(set(model_data["appointment_id"]))

