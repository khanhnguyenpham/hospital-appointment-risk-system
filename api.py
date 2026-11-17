from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from hospital_analytics.config import (
    CLEAN_APPOINTMENTS,
    METRICS_PATH,
    MODEL_PATH,
    WEB_DIR,
)
from hospital_analytics.features import MODEL_FEATURES
from hospital_analytics.monitoring import monitoring_report

Department = Literal[
    "Internal Medicine",
    "Pediatrics",
    "Cardiology",
    "Orthopedics",
    "Ophthalmology",
    "Endocrinology",
]
AgeGroup = Literal["0-17", "18-24", "25-44", "45-64", "65+"]
District = Literal["Central Buon Ma Thuot", "Outer Buon Ma Thuot", "Outside Buon Ma Thuot"]
Insurance = Literal["Public", "Private", "Self-pay"]

app = FastAPI(
    title="API hỗ trợ ưu tiên nhắc lịch ngoại trú",
    version="1.0.0",
    description="Hệ thống portfolio trên dữ liệu tổng hợp; không phải hệ thống lâm sàng.",
)


class AppointmentRequest(BaseModel):
    department: Department
    appointment_hour: int = Field(ge=7, le=16)
    weekday: int = Field(ge=0, le=6)
    month: int = Field(default=11, ge=1, le=12)
    lead_days: int = Field(ge=0, le=365)
    prior_visits: int = Field(default=0, ge=0, le=100)
    prior_no_shows: int = Field(ge=0, le=100)
    reminder_sent: int = Field(ge=0, le=1)
    age_group: AgeGroup
    district: District
    insurance_type: Insurance

    @model_validator(mode="after")
    def no_show_history_is_possible(self):
        if self.prior_no_shows > self.prior_visits:
            raise ValueError("Số lần bỏ hẹn trước không thể lớn hơn tổng số lần khám trước")
        return self


class AppointmentBatch(BaseModel):
    appointments: list[AppointmentRequest] = Field(min_length=1, max_length=500)


@lru_cache(maxsize=1)
def get_bundle():
    if not MODEL_PATH.exists():
        raise HTTPException(status_code=503, detail="Chưa có mô hình. Hãy chạy pipeline trước.")
    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def get_metrics() -> dict:
    if not METRICS_PATH.exists():
        raise HTTPException(status_code=503, detail="Chưa có metrics. Hãy chạy pipeline trước.")
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def get_data() -> pd.DataFrame:
    if not CLEAN_APPOINTMENTS.exists():
        raise HTTPException(status_code=503, detail="Chưa có dữ liệu đã xử lý. Hãy chạy pipeline trước.")
    return pd.read_csv(CLEAN_APPOINTMENTS, parse_dates=["appointment_date"])


def _frame(requests: list[AppointmentRequest]) -> pd.DataFrame:
    return pd.DataFrame([item.model_dump() for item in requests])[MODEL_FEATURES]


def _explain_row(model, row: pd.DataFrame, limit: int = 3) -> list[dict]:
    preprocessor = model.named_steps["preprocessor"]
    transformed = preprocessor.transform(row)
    values = transformed.toarray()[0] if hasattr(transformed, "toarray") else np.asarray(transformed)[0]
    names = preprocessor.get_feature_names_out()
    coefficients = model.named_steps["classifier"].coef_[0]
    contributions = values * coefficients
    order = np.argsort(np.abs(contributions))[::-1][:limit]
    return [
        {
            "feature": str(names[index]).replace("numeric__", "").replace("categorical__", ""),
            "direction": "increase" if contributions[index] >= 0 else "decrease",
            "contribution": round(float(contributions[index]), 4),
        }
        for index in order
    ]


def _predict_one(request: AppointmentRequest, bundle: dict) -> dict:
    row = _frame([request])
    probability = float(bundle["model"].predict_proba(row)[:, 1][0])
    threshold = float(bundle["threshold"])
    flagged = probability >= threshold
    return {
        "no_show_probability": round(probability, 4),
        "risk_label": "review" if flagged else "standard",
        "threshold": round(threshold, 2),
        "model_version": bundle["model_version"],
        "recommended_action": "Nhân viên xem xét nhắc lịch" if flagged else "Tiếp tục quy trình thông thường",
        "top_contributions": _explain_row(bundle["model"], row),
    }


@app.get("/", include_in_schema=False)
def home():
    index = WEB_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=503, detail="Giao diện web chưa sẵn sàng")
    return FileResponse(index)


@app.get("/health")
def health() -> dict:
    ready = MODEL_PATH.exists() and METRICS_PATH.exists() and CLEAN_APPOINTMENTS.exists()
    response = {"status": "ready" if ready else "not_ready", "service_version": "1.0.0"}
    if ready:
        response["model_version"] = get_bundle()["model_version"]
    return response


@app.get("/metadata")
def metadata() -> dict:
    return get_metrics()


@app.get("/analytics/summary")
def analytics_summary() -> dict:
    frame = get_data()
    active = frame[frame["status"] != "Cancelled"]
    completed = frame[frame["status"] == "Completed"]
    department = (
        active.groupby("department", as_index=False)
        .agg(appointments=("appointment_id", "count"), no_show_rate=("no_show", "mean"))
        .sort_values("no_show_rate", ascending=False)
    )
    monthly = (
        active.assign(month=active["appointment_date"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)
        .agg(appointments=("appointment_id", "count"), no_show_rate=("no_show", "mean"))
    )
    return {
        "appointments": len(frame),
        "active_appointments": len(active),
        "no_show_rate": round(float(active["no_show"].mean()), 4),
        "average_wait_minutes": round(float(completed["wait_minutes"].mean()), 1),
        "date_start": str(frame["appointment_date"].min().date()),
        "date_end": str(frame["appointment_date"].max().date()),
        "departments": department.round(4).to_dict(orient="records"),
        "monthly": monthly.round(4).to_dict(orient="records"),
    }


@app.post("/predict")
def predict(request: AppointmentRequest) -> dict:
    return _predict_one(request, get_bundle())


@app.post("/predict-batch")
def predict_batch(batch: AppointmentBatch) -> dict:
    bundle = get_bundle()
    results = [_predict_one(item, bundle) for item in batch.appointments]
    return {
        "count": len(results),
        "model_version": bundle["model_version"],
        "predictions": results,
    }


@app.post("/monitor")
def monitor(batch: AppointmentBatch) -> dict:
    bundle = get_bundle()
    probabilities = bundle["model"].predict_proba(_frame(batch.appointments))[:, 1]
    report = monitoring_report(
        probabilities,
        float(bundle["threshold"]),
        bundle["reference_probability_edges"],
        bundle["reference_probability_distribution"],
    )
    return {"model_version": bundle["model_version"], **report}


@app.get("/monitor/scenario")
@app.get("/monitor/demo", include_in_schema=False)
def monitor_demo(scenario: Literal["normal", "shifted"] = "normal") -> dict:
    """Return a reproducible monitoring example without exposing row-level data."""
    bundle = get_bundle()
    active = get_data().loc[lambda frame: frame["status"] != "Cancelled"].copy()
    sample = active.sample(n=min(500, len(active)), random_state=42)[MODEL_FEATURES].copy()
    if scenario == "shifted":
        sample["lead_days"] = np.clip(sample["lead_days"] + 30, 0, 365)
        sample["reminder_sent"] = 0
        sample["district"] = "Outside Buon Ma Thuot"
        sample["prior_no_shows"] = np.minimum(sample["prior_visits"], sample["prior_no_shows"] + 1)
    probabilities = bundle["model"].predict_proba(sample)[:, 1]
    report = monitoring_report(
        probabilities,
        float(bundle["threshold"]),
        bundle["reference_probability_edges"],
        bundle["reference_probability_distribution"],
    )
    return {"scenario": scenario, "model_version": bundle["model_version"], **report}


if WEB_DIR.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")
