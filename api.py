from __future__ import annotations

import sys
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from hospital_analytics.config import MODEL_PATH
from hospital_analytics.features import MODEL_FEATURES

app = FastAPI(title="Appointment No-show Risk API", version="0.1.0")


class AppointmentRequest(BaseModel):
    department: str
    appointment_hour: int = Field(ge=7, le=16)
    weekday: int = Field(ge=0, le=6)
    month: int = Field(default=11, ge=1, le=12)
    lead_days: int = Field(ge=0, le=365)
    prior_visits: int = Field(default=0, ge=0)
    prior_no_shows: int = Field(ge=0)
    reminder_sent: int = Field(ge=0, le=1)
    age_group: str
    district: str
    insurance_type: str


def get_bundle():
    if not MODEL_PATH.exists():
        raise HTTPException(status_code=503, detail="Model is not available. Run the pipeline first.")
    return joblib.load(MODEL_PATH)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok" if MODEL_PATH.exists() else "model_missing"}


@app.post("/predict")
def predict(request: AppointmentRequest) -> dict[str, float | str]:
    if request.prior_no_shows > request.prior_visits:
        raise HTTPException(status_code=422, detail="prior_no_shows cannot exceed prior_visits")
    bundle = get_bundle()
    row = pd.DataFrame([request.model_dump()])[MODEL_FEATURES]
    probability = float(bundle["model"].predict_proba(row)[:, 1][0])
    threshold = float(bundle["threshold"])
    return {
        "no_show_probability": round(probability, 4),
        "risk_label": "review" if probability >= threshold else "standard",
        "threshold": round(threshold, 2),
    }

