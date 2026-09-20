import json
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

IDENTIFIER_COLUMNS = {
    "flow id", "source ip", "destination ip", "src ip", "dst ip",
    "timestamp", "date", "time"
}


def normalize_column_name(name: str) -> str:
    """Strip odd spaces/characters while keeping readable CICIDS column names."""
    name = str(name).replace("\ufeff", "").strip()
    name = re.sub(r"\s+", " ", name)
    return name


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [normalize_column_name(c) for c in df.columns]
    return df


def find_label_column(columns: Iterable[str]) -> str:
    for col in columns:
        if normalize_column_name(col).lower() in {"label", "class", "target", "attack"}:
            return col
    raise ValueError("Could not find a label column. Expected a column named Label/Class/Target/Attack.")


def broad_attack_label(value: object) -> str:
    """Map CICIDS2017's detailed labels into stable, interview-friendly attack families."""
    text = str(value).strip().lower()
    text = text.replace("�", " ").replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text)

    if text in {"benign", "normal", "0"} or "benign" in text:
        return "BENIGN"
    if "ddos" in text:
        return "DDoS"
    if "dos" in text or "slowloris" in text or "slowhttptest" in text or "hulk" in text or "goldeneye" in text:
        return "DoS"
    if "portscan" in text or "port scan" in text:
        return "PortScan"
    if "brute" in text or "patator" in text or "ftp" in text or "ssh" in text:
        return "BruteForce"
    if "bot" in text:
        return "Bot"
    if "web attack" in text or "xss" in text or "sql injection" in text:
        return "WebAttack"
    if "infiltration" in text:
        return "Infiltration"
    if "heartbleed" in text:
        return "Heartbleed"
    return str(value).strip() or "Unknown"


def clean_numeric_frame(df: pd.DataFrame, feature_columns=None) -> pd.DataFrame:
    """Convert a feature frame to numeric values and normalize +/- infinity."""
    out = normalize_columns(df)
    if feature_columns is not None:
        for col in feature_columns:
            if col not in out.columns:
                out[col] = np.nan
        out = out[list(feature_columns)]
    for col in out.columns:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.replace([np.inf, -np.inf], np.nan)
    return out


def choose_feature_columns(df: pd.DataFrame, label_col: str, max_missing_fraction: float = 0.40):
    """Choose useful numeric-looking features while dropping IDs, constants and mostly-empty fields."""
    candidates = []
    for col in df.columns:
        low = col.lower().strip()
        if col == label_col or low in IDENTIFIER_COLUMNS:
            continue
        series = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
        if series.isna().mean() > max_missing_fraction:
            continue
        if series.nunique(dropna=True) <= 1:
            continue
        candidates.append(col)
    if not candidates:
        raise ValueError("No usable numeric feature columns were found.")
    return candidates


def save_json(data, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
