import importlib
from pathlib import Path

packages = ["numpy", "pandas", "sklearn", "xgboost", "torch", "streamlit", "plotly", "joblib"]
failed = []
for name in packages:
    try:
        module = importlib.import_module(name)
        version = getattr(module, "__version__", "installed")
        print(f"[OK] {name}: {version}")
    except Exception as exc:
        failed.append((name, str(exc)))
        print(f"[FAIL] {name}: {exc}")

model_dir = Path(__file__).resolve().parent / "models"
required = ["xgboost_classifier.joblib", "autoencoder.pt", "feature_columns.json"]
for name in required:
    print(f"[{'OK' if (model_dir/name).exists() else 'INFO'}] model/{name}")

if failed:
    raise SystemExit("\nSome Python packages are missing. Run setup_windows.bat.")
print("\nEnvironment looks ready.")
