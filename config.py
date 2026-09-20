from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DEMO_DIR = DATA_DIR / "demo"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"

LABEL_COLUMN = "Label"
RANDOM_STATE = 42
DEFAULT_MAX_PER_CLASS = 5000
DEFAULT_DEMO_ROWS = 6000

for directory in [RAW_DIR, PROCESSED_DIR, DEMO_DIR, MODELS_DIR, REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
