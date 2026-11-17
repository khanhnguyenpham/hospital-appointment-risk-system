from fastapi.testclient import TestClient

from api import app

client = TestClient(app)

VALID_APPOINTMENT = {
    "department": "Cardiology",
    "appointment_hour": 8,
    "weekday": 0,
    "month": 9,
    "lead_days": 18,
    "prior_visits": 3,
    "prior_no_shows": 2,
    "reminder_sent": 0,
    "age_group": "45-64",
    "district": "Outside Buon Ma Thuot",
    "insurance_type": "Public",
}


def test_health_exposes_running_model_version():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["model_version"].startswith("v1-")


def test_prediction_contract_and_explanation():
    response = client.post("/predict", json=VALID_APPOINTMENT)
    assert response.status_code == 200
    payload = response.json()
    assert 0 <= payload["no_show_probability"] <= 1
    assert payload["risk_label"] in {"review", "standard"}
    assert len(payload["top_contributions"]) == 3


def test_impossible_history_is_rejected():
    appointment = {**VALID_APPOINTMENT, "prior_visits": 1, "prior_no_shows": 2}
    response = client.post("/predict", json=appointment)
    assert response.status_code == 422


def test_monitoring_contract():
    response = client.post("/monitor", json={"appointments": [VALID_APPOINTMENT] * 20})
    assert response.status_code == 200
    payload = response.json()
    assert payload["sample_size"] == 20
    assert payload["status"] in {"stable", "watch", "investigate"}
    assert payload["psi"] >= 0


def test_monitoring_demo_separates_reference_and_shifted_batches():
    normal = client.get("/monitor/demo?scenario=normal").json()
    shifted = client.get("/monitor/demo?scenario=shifted").json()
    assert normal["status"] == "stable"
    assert shifted["psi"] > normal["psi"]
    assert shifted["status"] == "investigate"


def test_web_demo_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "Ưu tiên nhắc lịch" in response.text
