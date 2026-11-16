from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from hospital_analytics.config import RAW_APPOINTMENTS
from hospital_analytics.database import prepare_data_store
from hospital_analytics.generate_data import save_raw_data
from hospital_analytics.reporting import create_figures, operational_summary
from hospital_analytics.train import train_and_save


def main() -> None:
    if not RAW_APPOINTMENTS.exists():
        save_raw_data()
    frame = prepare_data_store()
    _, model_metrics = train_and_save(frame)
    create_figures(frame)

    print("Pipeline completed")
    print(json.dumps(operational_summary(frame), indent=2))
    print("Model test metrics")
    print(json.dumps(model_metrics["test"], indent=2))


if __name__ == "__main__":
    main()

