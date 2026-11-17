from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "models"
FIGURE_DIR = PROJECT_ROOT / "reports" / "figures"
WEB_DIR = PROJECT_ROOT / "web"

RAW_APPOINTMENTS = RAW_DIR / "appointments.csv"
CLEAN_APPOINTMENTS = PROCESSED_DIR / "appointments_clean.csv"
DATABASE_PATH = PROCESSED_DIR / "hospital_operations.db"
MODEL_PATH = MODEL_DIR / "no_show_model.joblib"
METRICS_PATH = MODEL_DIR / "model_metrics.json"
MODEL_CARD_PATH = PROJECT_ROOT / "docs" / "model_card.md"

RANDOM_SEED = 42


def ensure_directories() -> None:
    for directory in (RAW_DIR, PROCESSED_DIR, MODEL_DIR, FIGURE_DIR, WEB_DIR):
        directory.mkdir(parents=True, exist_ok=True)
