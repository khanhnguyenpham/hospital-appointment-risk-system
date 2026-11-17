from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from hospital_analytics.config import MODEL_PATH


def score_file(source: Path, output: Path, model_path: Path = MODEL_PATH) -> int:
    bundle = joblib.load(model_path)
    frame = pd.read_csv(source)
    missing = set(bundle["features"]) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing model features: {sorted(missing)}")
    probabilities = bundle["model"].predict_proba(frame[bundle["features"]])[:, 1]
    result = frame.copy()
    result["no_show_probability"] = probabilities.round(4)
    result["risk_label"] = np.where(probabilities >= bundle["threshold"], "review", "standard")
    result = result.sort_values("no_show_probability", ascending=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    return len(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Chấm điểm một batch lịch hẹn")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = score_file(args.source, args.output)
    print(f"Đã chấm {rows:,} dòng -> {args.output}")


if __name__ == "__main__":
    main()
