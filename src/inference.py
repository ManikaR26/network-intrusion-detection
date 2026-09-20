from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
import torch
from torch import nn

from config import MODELS_DIR
from src.common import clean_numeric_frame, load_json, normalize_columns


class Autoencoder(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()
        hidden1 = max(16, min(64, input_dim * 2))
        hidden2 = max(8, min(32, input_dim))
        latent = max(4, min(12, input_dim // 2))
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden1), nn.ReLU(),
            nn.Linear(hidden1, hidden2), nn.ReLU(),
            nn.Linear(hidden2, latent), nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent, hidden2), nn.ReLU(),
            nn.Linear(hidden2, hidden1), nn.ReLU(),
            nn.Linear(hidden1, input_dim),
        )
    def forward(self, x):
        return self.decoder(self.encoder(x))


@lru_cache(maxsize=1)
def load_artifacts():
    required = [
        "xgboost_classifier.joblib", "label_encoder.joblib", "imputer.joblib", "scaler.joblib",
        "autoencoder.pt", "feature_columns.json", "anomaly_threshold.json"
    ]
    missing = [f for f in required if not (MODELS_DIR / f).exists()]
    if missing:
        raise FileNotFoundError("Missing model files: " + ", ".join(missing) + ". Run training first.")

    clf = joblib.load(MODELS_DIR / "xgboost_classifier.joblib")
    encoder = joblib.load(MODELS_DIR / "label_encoder.joblib")
    imputer = joblib.load(MODELS_DIR / "imputer.joblib")
    scaler = joblib.load(MODELS_DIR / "scaler.joblib")
    features = load_json(MODELS_DIR / "feature_columns.json")
    threshold = float(load_json(MODELS_DIR / "anomaly_threshold.json")["threshold"])
    checkpoint = torch.load(MODELS_DIR / "autoencoder.pt", map_location="cpu", weights_only=True)
    ae = Autoencoder(int(checkpoint["input_dim"]))
    ae.load_state_dict(checkpoint["state_dict"])
    ae.eval()
    return clf, encoder, imputer, scaler, features, threshold, ae


def analyze_dataframe(df: pd.DataFrame):
    clf, encoder, imputer, scaler, features, threshold, ae = load_artifacts()
    original = normalize_columns(df)
    provided = set(original.columns)
    missing = [c for c in features if c not in provided]
    present_fraction = 1 - len(missing) / max(len(features), 1)
    if present_fraction < 0.70:
        raise ValueError(
            f"Uploaded file only contains {present_fraction:.0%} of the model's required features. "
            "Use a CSV generated from the same dataset/features used during training."
        )

    X = clean_numeric_frame(original, features)
    X_imp = imputer.transform(X)
    probs = clf.predict_proba(X_imp)
    pred_ids = probs.argmax(axis=1)
    labels = encoder.inverse_transform(pred_ids)
    confidence = probs.max(axis=1)

    X_scaled = scaler.transform(X_imp)
    with torch.no_grad():
        t = torch.tensor(X_scaled, dtype=torch.float32)
        recon = ae(t)
        errors = torch.mean((recon - t) ** 2, dim=1).numpy()
    anomaly = errors > threshold

    risk = []
    for label, conf, is_anom in zip(labels, confidence, anomaly):
        if str(label).upper() != "BENIGN":
            risk.append("HIGH" if conf >= 0.75 else "MEDIUM")
        elif is_anom:
            risk.append("MEDIUM")
        else:
            risk.append("LOW")

    results = pd.DataFrame({
        "Prediction": labels,
        "Confidence": confidence,
        "Anomaly Score": errors,
        "Autoencoder Anomaly": anomaly,
        "Risk": risk,
    }, index=original.index)
    return results, {"missing_features": missing, "anomaly_threshold": threshold}
