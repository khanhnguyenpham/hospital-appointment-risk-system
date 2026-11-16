from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from .config import FIGURE_DIR, ensure_directories


def create_figures(frame: pd.DataFrame) -> None:
    ensure_directories()
    active = frame.loc[frame["status"] != "Cancelled"].copy()

    department = (
        active.groupby("department", as_index=False)
        .agg(appointments=("appointment_id", "count"), no_show_rate=("no_show", "mean"))
        .sort_values("no_show_rate")
    )
    fig, axis = plt.subplots(figsize=(9, 5))
    axis.barh(department["department"], department["no_show_rate"] * 100, color="#247ba0")
    axis.set_xlabel("No-show rate (%)")
    axis.set_title("No-show rate by department")
    axis.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "no_show_by_department.png", dpi=160)
    plt.close(fig)

    completed = frame.loc[frame["status"] == "Completed"]
    wait = completed.groupby("department")["wait_minutes"].mean().sort_values()
    fig, axis = plt.subplots(figsize=(9, 5))
    axis.barh(wait.index, wait.values, color="#70c1b3")
    axis.set_xlabel("Average wait (minutes)")
    axis.set_title("Average waiting time by department")
    axis.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "wait_time_by_department.png", dpi=160)
    plt.close(fig)


def operational_summary(frame: pd.DataFrame) -> dict[str, float | int]:
    active = frame.loc[frame["status"] != "Cancelled"]
    completed = frame.loc[frame["status"] == "Completed"]
    return {
        "appointments": int(len(frame)),
        "completed": int((frame["status"] == "Completed").sum()),
        "no_show_rate_pct": round(float(active["no_show"].mean() * 100), 2),
        "avg_wait_minutes": round(float(completed["wait_minutes"].mean()), 1),
    }

