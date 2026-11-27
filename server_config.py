"""Runtime configuration kept separate from request handling."""

import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SURVEY_DB_PATH = os.path.join(BASE_DIR, "data", "tobakost_survey_warehouse.db")
LEGACY_DB_PATH = os.path.join(BASE_DIR, "data", "tobakost_warehouse.db")
DB_PATH = os.getenv(
    "TOBAKOST_DB_PATH",
    SURVEY_DB_PATH if os.path.exists(SURVEY_DB_PATH) else LEGACY_DB_PATH,
)
MODEL_PKL_PATH = os.path.join(BASE_DIR, "models", "best_rf_model.pkl")
FRONTEND_HTML_PATH = os.path.join(BASE_DIR, "frontend", "index.html")
NORMALIZE_SCRIPT_PATH = os.path.join(BASE_DIR, "etl", "normalize_survey.py")
ETL_SCRIPT_PATH = os.path.join(BASE_DIR, "etl", "run_survey_star_schema.py")
TRAIN_SCRIPT_PATH = os.path.join(BASE_DIR, "models", "train_models.py")
HOST = os.getenv("TOBAKOST_HOST", "127.0.0.1")
PORT = int(os.getenv("TOBAKOST_PORT", "8000"))
ADMIN_API_KEY = os.getenv("TOBAKOST_ADMIN_API_KEY", "")
