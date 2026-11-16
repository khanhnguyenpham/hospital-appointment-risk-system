from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from hospital_analytics.config import CLEAN_APPOINTMENTS, METRICS_PATH, MODEL_PATH
from hospital_analytics.features import MODEL_FEATURES

st.set_page_config(page_title="Hospital Operations Analytics", layout="wide")


@st.cache_data
def load_data() -> pd.DataFrame:
    frame = pd.read_csv(CLEAN_APPOINTMENTS, parse_dates=["appointment_date", "booked_at"])
    return frame


@st.cache_resource
def load_model_bundle():
    return joblib.load(MODEL_PATH)


if not CLEAN_APPOINTMENTS.exists() or not MODEL_PATH.exists():
    st.error("Run `python run_pipeline.py` before opening the dashboard.")
    st.stop()

data = load_data()
bundle = load_model_bundle()
metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))

st.title("Hospital Appointment Operations")
st.caption("Synthetic portfolio data - operational decision support, not clinical advice")

with st.sidebar:
    st.header("Filters")
    departments = st.multiselect("Department", sorted(data["department"].unique()))
    date_min = data["appointment_date"].min().date()
    date_max = data["appointment_date"].max().date()
    date_range = st.date_input("Appointment date", value=(date_min, date_max), min_value=date_min, max_value=date_max)

filtered = data.copy()
if departments:
    filtered = filtered[filtered["department"].isin(departments)]
if len(date_range) == 2:
    filtered = filtered[filtered["appointment_date"].dt.date.between(date_range[0], date_range[1])]

active = filtered[filtered["status"] != "Cancelled"]
completed = filtered[filtered["status"] == "Completed"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Appointments", f"{len(filtered):,}")
col2.metric("No-show rate", f"{active['no_show'].mean() * 100:.1f}%" if len(active) else "-")
col3.metric("Average wait", f"{completed['wait_minutes'].mean():.1f} min" if len(completed) else "-")
col4.metric("Model test ROC-AUC", f"{metrics['test']['roc_auc']:.3f}")

monthly = (
    active.assign(month_period=active["appointment_date"].dt.to_period("M").astype(str))
    .groupby("month_period", as_index=False)
    .agg(appointments=("appointment_id", "count"), no_show_rate=("no_show", "mean"))
)

left, right = st.columns(2)
with left:
    st.subheader("Monthly demand")
    st.plotly_chart(px.line(monthly, x="month_period", y="appointments", markers=True), use_container_width=True)
with right:
    st.subheader("No-show rate by department")
    department_rate = active.groupby("department", as_index=False)["no_show"].mean()
    department_rate["no_show_rate_pct"] = department_rate["no_show"] * 100
    st.plotly_chart(
        px.bar(department_rate.sort_values("no_show_rate_pct"), x="no_show_rate_pct", y="department", orientation="h"),
        use_container_width=True,
    )

st.subheader("Reminder comparison")
reminder = active.groupby("reminder_sent", as_index=False).agg(appointments=("appointment_id", "count"), no_show_rate=("no_show", "mean"))
reminder["reminder"] = reminder["reminder_sent"].map({0: "Not sent", 1: "Sent"})
reminder["no_show_rate_pct"] = reminder["no_show_rate"] * 100
st.plotly_chart(px.bar(reminder, x="reminder", y="no_show_rate_pct", text_auto=".1f"), use_container_width=True)
st.info("This comparison is descriptive. It does not prove that reminders caused the difference.")

st.subheader("Retrospective risk review")
st.caption("Latest historical records, shown to inspect model behavior. Production scoring would use future scheduled appointments.")
risk_candidates = filtered[filtered["status"] != "Cancelled"].copy()
if len(risk_candidates):
    latest_date = risk_candidates["appointment_date"].max()
    risk_candidates = risk_candidates[risk_candidates["appointment_date"] >= latest_date - pd.Timedelta(days=30)]
    risk_candidates["risk_probability"] = bundle["model"].predict_proba(risk_candidates[MODEL_FEATURES])[:, 1]
    queue = risk_candidates.nlargest(20, "risk_probability")[
        ["appointment_id", "appointment_date", "department", "appointment_hour", "lead_days", "prior_no_shows", "reminder_sent", "risk_probability"]
    ]
    queue["risk_probability"] = (queue["risk_probability"] * 100).round(1).astype(str) + "%"
    st.dataframe(queue, use_container_width=True, hide_index=True)

