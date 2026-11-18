from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import (
    METRICS_PATH,
    MODEL_CARD_PATH,
    MODEL_PATH,
    RANDOM_SEED,
    ensure_directories,
)
from .features import (
    CATEGORICAL_FEATURES,
    MODEL_FEATURES,
    NUMERIC_FEATURES,
    TARGET,
    chronological_split,
    modelling_frame,
)
from .monitoring import probability_reference

MAX_REVIEW_RATE = 0.30
SCHEMA_VERSION = "1.0"


def build_model() -> Pipeline:
    numeric_pipeline = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        [
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        [
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000, random_state=RANDOM_SEED)),
        ]
    )


def _operational_threshold(y_true: pd.Series, probabilities: np.ndarray) -> float:
    """Choose the best F1 threshold without exceeding reminder-team capacity."""
    thresholds = np.arange(0.20, 0.81, 0.01)
    candidates: list[tuple[float, float]] = []
    for threshold in thresholds:
        review_rate = float((probabilities >= threshold).mean())
        if review_rate <= MAX_REVIEW_RATE:
            score = f1_score(y_true, probabilities >= threshold, zero_division=0)
            candidates.append((float(score), float(threshold)))
    if not candidates:
        return float(np.quantile(probabilities, 1 - MAX_REVIEW_RATE))
    return max(candidates, key=lambda item: (item[0], item[1]))[1]


def expected_calibration_error(
    y_true: pd.Series | np.ndarray,
    probabilities: np.ndarray,
    bins: int = 10,
) -> float:
    if bins < 2:
        raise ValueError("bins must be at least 2")
    targets = np.asarray(y_true, dtype=float)
    values = np.asarray(probabilities, dtype=float)
    if len(targets) != len(values) or len(values) == 0:
        raise ValueError("targets and probabilities must have the same non-zero length")

    edges = np.linspace(0.0, 1.0, bins + 1)
    assignments = np.digitize(values, edges[1:-1], right=True)
    error = 0.0
    for index in range(bins):
        mask = assignments == index
        if mask.any():
            error += float(mask.mean()) * abs(float(targets[mask].mean()) - float(values[mask].mean()))
    return error


def _metrics(y_true: pd.Series, probabilities: np.ndarray, threshold: float) -> dict[str, float | int]:
    predictions = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()
    return {
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 4),
        "brier_score": round(float(brier_score_loss(y_true, probabilities)), 4),
        "expected_calibration_error": round(expected_calibration_error(y_true, probabilities), 4),
        "accuracy": round(float(accuracy_score(y_true, predictions)), 4),
        "precision": round(float(precision_score(y_true, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, predictions, zero_division=0)), 4),
        "review_rate": round(float(predictions.mean()), 4),
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }


def _subgroup_metrics(test: pd.DataFrame, probabilities: np.ndarray, threshold: float) -> list[dict]:
    working = test[["department", TARGET]].copy()
    working["probability"] = probabilities
    results = []
    for department, group in working.groupby("department"):
        local_probabilities = group["probability"].to_numpy()
        local_metrics = _metrics(group[TARGET], local_probabilities, threshold)
        results.append({"department": department, "rows": len(group), **local_metrics})
    return sorted(results, key=lambda item: item["department"])


def _threshold_table(y_true: pd.Series, probabilities: np.ndarray, selected: float) -> list[dict]:
    values = sorted({0.40, 0.50, round(selected, 2), 0.60, 0.70})
    return [{"threshold": value, **_metrics(y_true, probabilities, value)} for value in values]


def _coefficient_summary(model: Pipeline, limit: int = 10) -> list[dict[str, float | str]]:
    names = model.named_steps["preprocessor"].get_feature_names_out()
    coefficients = model.named_steps["classifier"].coef_[0]
    order = np.argsort(np.abs(coefficients))[::-1][:limit]
    return [
        {
            "feature": str(names[index]).replace("numeric__", "").replace("categorical__", ""),
            "coefficient": round(float(coefficients[index]), 4),
        }
        for index in order
    ]


def _data_fingerprint(frame: pd.DataFrame) -> str:
    hashed = pd.util.hash_pandas_object(frame[[*MODEL_FEATURES, TARGET]], index=False).values
    return hashlib.sha256(hashed.tobytes()).hexdigest()


def _write_model_card(metrics: dict) -> None:
    test = metrics["test"]
    baseline = metrics["baseline"]
    content = f"""# Model card — rủi ro bỏ hẹn ngoại trú

## Mục đích sử dụng

Mô hình xếp hạng các lịch hẹn cần nhân viên xem xét để ưu tiên nhắc lịch. Điểm số **không được dùng** để hủy, trì hoãn, từ chối khám hoặc đưa ra quyết định lâm sàng.

## Dữ liệu và cách đánh giá

- 100% dữ liệu tổng hợp được tạo trong repository; không có hồ sơ bệnh nhân thật.
- Chia train/validation/test theo thời gian để tránh đưa thông tin tương lai vào huấn luyện.
- Tập test là giai đoạn {metrics["test_period_start"]} đến {metrics["test_period_end"]}.
- Ngưỡng được chọn trên validation với giới hạn tối đa {metrics["max_review_rate"]:.0%} lịch hẹn phải xem xét.

## Kết quả tham chiếu

| Chỉ số | Logistic regression | Baseline theo tỷ lệ lớp |
|---|---:|---:|
| ROC-AUC | {test["roc_auc"]:.4f} | {baseline["roc_auc"]:.4f} |
| Brier score | {test["brier_score"]:.4f} | {baseline["brier_score"]:.4f} |
| Expected calibration error | {test["expected_calibration_error"]:.4f} | {baseline["expected_calibration_error"]:.4f} |
| Precision | {test["precision"]:.4f} | {baseline["precision"]:.4f} |
| Recall | {test["recall"]:.4f} | {baseline["recall"]:.4f} |
| F1 | {test["f1"]:.4f} | {baseline["f1"]:.4f} |

Ngưỡng quyết định: **{metrics["threshold"]:.2f}**. Tỷ lệ đưa vào hàng đợi trên test: **{test["review_rate"]:.1%}**.

## Giới hạn và kiểm soát

- Kết quả trên dữ liệu tổng hợp không chứng minh hiệu quả tại bệnh viện thật.
- Biến `reminder_sent` chỉ phản ánh mối liên hệ trong dữ liệu, không chứng minh tác động nhân quả.
- Theo dõi PSI, tỷ lệ đưa vào hàng đợi và hiệu năng theo khoa trước khi dựa vào kết quả.
- Luôn giữ người phụ trách trong vòng quyết định và ghi lại hành động vận hành.
- Cần đánh giá riêng tư, bảo mật, thiên lệch và an toàn trước mọi thử nghiệm thực tế.

Phiên bản mô hình: `{metrics["model_version"]}` · Schema: `{metrics["schema_version"]}`
"""
    MODEL_CARD_PATH.write_text(content, encoding="utf-8")


def train_and_save(frame: pd.DataFrame) -> tuple[Pipeline, dict]:
    ensure_directories()
    model_data = modelling_frame(frame)
    train, validation, test = chronological_split(model_data)

    model = build_model()
    model.fit(train[MODEL_FEATURES], train[TARGET])

    validation_probabilities = model.predict_proba(validation[MODEL_FEATURES])[:, 1]
    threshold = _operational_threshold(validation[TARGET], validation_probabilities)
    test_probabilities = model.predict_proba(test[MODEL_FEATURES])[:, 1]
    train_probabilities = model.predict_proba(train[MODEL_FEATURES])[:, 1]
    reference_edges, reference_distribution = probability_reference(train_probabilities)

    dummy = DummyClassifier(strategy="prior", random_state=RANDOM_SEED)
    dummy.fit(train[MODEL_FEATURES], train[TARGET])
    dummy_probabilities = dummy.predict_proba(test[MODEL_FEATURES])[:, 1]

    fingerprint = _data_fingerprint(model_data)
    model_version = f"v1-{fingerprint[:8]}"
    metrics = {
        "model_name": "Logistic regression có tiền xử lý",
        "model_version": model_version,
        "schema_version": SCHEMA_VERSION,
        "trained_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "data_fingerprint": fingerprint,
        "threshold": round(threshold, 2),
        "max_review_rate": MAX_REVIEW_RATE,
        "train_rows": len(train),
        "validation_rows": len(validation),
        "test_rows": len(test),
        "test_period_start": str(test["appointment_date"].min().date()),
        "test_period_end": str(test["appointment_date"].max().date()),
        "validation": _metrics(validation[TARGET], validation_probabilities, threshold),
        "test": _metrics(test[TARGET], test_probabilities, threshold),
        "baseline": _metrics(test[TARGET], dummy_probabilities, threshold),
        "threshold_sensitivity": _threshold_table(test[TARGET], test_probabilities, threshold),
        "department_metrics": _subgroup_metrics(test, test_probabilities, threshold),
        "top_coefficients": _coefficient_summary(model),
    }

    bundle = {
        "model": model,
        "threshold": threshold,
        "features": MODEL_FEATURES,
        "model_version": model_version,
        "schema_version": SCHEMA_VERSION,
        "reference_probability_edges": reference_edges,
        "reference_probability_distribution": reference_distribution,
    }
    joblib.dump(bundle, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_model_card(metrics)
    return model, metrics
