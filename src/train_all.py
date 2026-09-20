import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.utils.class_weight import compute_sample_weight
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from xgboost import XGBClassifier

from config import DEMO_DIR, MODELS_DIR, REPORTS_DIR, RANDOM_STATE
from src.common import choose_feature_columns, find_label_column, normalize_columns, save_json


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


def reconstruction_errors(model, arr, device="cpu"):
    model.eval()
    with torch.no_grad():
        x = torch.tensor(arr, dtype=torch.float32, device=device)
        recon = model(x)
        err = torch.mean((recon - x) ** 2, dim=1)
    return err.cpu().numpy()


def train_autoencoder(x_benign, epochs=18, batch_size=256):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = Autoencoder(x_benign.shape[1]).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()
    loader = DataLoader(
        TensorDataset(torch.tensor(x_benign, dtype=torch.float32)),
        batch_size=min(batch_size, len(x_benign)), shuffle=True
    )
    model.train()
    for epoch in range(1, epochs + 1):
        losses = []
        for (batch,) in loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            recon = model(batch)
            loss = loss_fn(recon, batch)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
        if epoch == 1 or epoch % 5 == 0 or epoch == epochs:
            print(f"Autoencoder epoch {epoch:02d}/{epochs} | loss={np.mean(losses):.6f}")
    return model.cpu()


def main(data_path: Path, epochs: int):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        raise FileNotFoundError(f"Training data not found: {data_path}")

    print(f"Loading {data_path} ...")
    df = normalize_columns(pd.read_csv(data_path, low_memory=False))
    label_col = find_label_column(df.columns)
    if label_col != "Label":
        df = df.rename(columns={label_col: "Label"})
    df["Label"] = df["Label"].astype(str).str.strip()

    # Very tiny classes can break a stratified split and give meaningless metrics.
    class_counts = df["Label"].value_counts()
    tiny = class_counts[class_counts < 5].index.tolist()
    if tiny:
        print("Dropping classes with fewer than 5 rows:", ", ".join(map(str, tiny)))
        df = df[~df["Label"].isin(tiny)].reset_index(drop=True)

    feature_columns = choose_feature_columns(df, "Label")
    print(f"Using {len(feature_columns)} numeric features.")

    X = df[feature_columns].copy()
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors="coerce")
    X = X.replace([np.inf, -np.inf], np.nan)
    y_text = df["Label"].values

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_text)
    print("Classes:", ", ".join(label_encoder.classes_))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
    )

    imputer = SimpleImputer(strategy="median")
    X_train_imp = imputer.fit_transform(X_train)
    X_test_imp = imputer.transform(X_test)

    print("\nTraining XGBoost classifier...")
    classifier = XGBClassifier(
        n_estimators=220,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="multi:softprob",
        eval_metric="mlogloss",
        tree_method="hist",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )
    weights = compute_sample_weight(class_weight="balanced", y=y_train)
    classifier.fit(X_train_imp, y_train, sample_weight=weights)

    pred = classifier.predict(X_test_imp)
    accuracy = accuracy_score(y_test, pred)
    macro_f1 = f1_score(y_test, pred, average="macro", zero_division=0)
    macro_precision = precision_score(y_test, pred, average="macro", zero_division=0)
    macro_recall = recall_score(y_test, pred, average="macro", zero_division=0)
    print(f"XGBoost accuracy: {accuracy:.4f} | macro F1: {macro_f1:.4f}")

    all_ids = np.arange(len(label_encoder.classes_))
    report = classification_report(y_test, pred, labels=all_ids, target_names=label_encoder.classes_, zero_division=0, output_dict=True)
    pd.DataFrame(report).transpose().to_csv(REPORTS_DIR / "classification_report.csv")
    cm = confusion_matrix(y_test, pred, labels=all_ids)
    pd.DataFrame(cm, index=label_encoder.classes_, columns=label_encoder.classes_).to_csv(REPORTS_DIR / "confusion_matrix.csv")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_imp)
    X_test_scaled = scaler.transform(X_test_imp)

    benign_matches = np.where(label_encoder.classes_ == "BENIGN")[0]
    if len(benign_matches) == 0:
        raise ValueError("Dataset must include a BENIGN class for autoencoder anomaly training.")
    benign_id = int(benign_matches[0])
    benign_train = X_train_scaled[y_train == benign_id]
    if len(benign_train) < 50:
        raise ValueError("Not enough BENIGN training rows for autoencoder.")

    print(f"\nTraining autoencoder on {len(benign_train):,} BENIGN rows...")
    autoencoder = train_autoencoder(benign_train, epochs=epochs)
    benign_errors = reconstruction_errors(autoencoder, benign_train)
    threshold = float(np.percentile(benign_errors, 97.5))
    print(f"Autoencoder anomaly threshold (97.5th percentile): {threshold:.6f}")

    test_errors = reconstruction_errors(autoencoder, X_test_scaled)
    test_anomaly = test_errors > threshold
    true_attack = y_test != benign_id
    anomaly_recall = recall_score(true_attack, test_anomaly, zero_division=0)
    anomaly_precision = precision_score(true_attack, test_anomaly, zero_division=0)
    print(f"Autoencoder attack recall: {anomaly_recall:.4f} | precision: {anomaly_precision:.4f}")

    joblib.dump(classifier, MODELS_DIR / "xgboost_classifier.joblib")
    joblib.dump(label_encoder, MODELS_DIR / "label_encoder.joblib")
    joblib.dump(imputer, MODELS_DIR / "imputer.joblib")
    joblib.dump(scaler, MODELS_DIR / "scaler.joblib")
    torch.save({"state_dict": autoencoder.state_dict(), "input_dim": len(feature_columns)}, MODELS_DIR / "autoencoder.pt")
    save_json(feature_columns, MODELS_DIR / "feature_columns.json")
    save_json({"threshold": threshold}, MODELS_DIR / "anomaly_threshold.json")
    save_json({
        "data_path": str(data_path),
        "rows": int(len(df)),
        "features": int(len(feature_columns)),
        "classes": list(map(str, label_encoder.classes_)),
        "xgboost_accuracy": float(accuracy),
        "xgboost_macro_f1": float(macro_f1),
        "xgboost_macro_precision": float(macro_precision),
        "xgboost_macro_recall": float(macro_recall),
        "autoencoder_anomaly_precision": float(anomaly_precision),
        "autoencoder_anomaly_recall": float(anomaly_recall),
        "autoencoder_threshold": threshold,
    }, REPORTS_DIR / "training_metrics.json")

    print("\nSaved trained models to models/ and reports to reports/.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train XGBoost + PyTorch autoencoder.")
    parser.add_argument("--data", type=Path, default=DEMO_DIR / "demo_network_traffic.csv")
    parser.add_argument("--epochs", type=int, default=18)
    args = parser.parse_args()
    main(args.data, args.epochs)
