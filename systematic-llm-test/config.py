from pathlib import Path

BASE_DIR = Path(__file__).parent

GCP_PROJECT = "infinitas-ds-ai-poc"
GCP_LOCATION = "us-central1"

MODELS: list[str] = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]

N_ITERATIONS = 3

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
TAMPERED_DIR = DATA_DIR / "tampered"
AUGMENTED_DIR = DATA_DIR / "augmented"
STANDALONE_DIR = DATA_DIR / "standalone"

LABELS_PATH = BASE_DIR / "labels" / "manifest.csv"
RESULTS_DIR = BASE_DIR / "results"

RATE_LIMIT_RPM = 60
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 5

MLFLOW_EXPERIMENT = "vlm-fraud-detection"
MLFLOW_TRACKING_URI = str(BASE_DIR / "mlruns")
