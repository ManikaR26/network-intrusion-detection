import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from config import RAW_DIR, PROCESSED_DIR, DEFAULT_MAX_PER_CLASS, RANDOM_STATE
from src.common import broad_attack_label, find_label_column, normalize_columns


def prepare(input_dir: Path, output: Path, max_per_class: int, chunksize: int = 100_000):
    csv_files = sorted(input_dir.rglob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found inside {input_dir}. Extract CIC-IDS2017 MachineLearningCSV files there first."
        )

    kept = defaultdict(int)
    collected = []
    rng = np.random.default_rng(RANDOM_STATE)

    print(f"Found {len(csv_files)} CSV file(s).")
    for file in csv_files:
        print(f"Reading: {file.name}")
        for chunk in pd.read_csv(file, low_memory=False, chunksize=chunksize, encoding_errors="replace"):
            chunk = normalize_columns(chunk)
            try:
                label_col = find_label_column(chunk.columns)
            except ValueError:
                print(f"  Skipping {file.name}: label column not found.")
                break

            chunk[label_col] = chunk[label_col].map(broad_attack_label)
            chunk = chunk.dropna(subset=[label_col])

            for label, group in chunk.groupby(label_col):
                remaining = max_per_class - kept[label]
                if remaining <= 0:
                    continue
                if len(group) > remaining:
                    # deterministic random sample from the current chunk
                    seed = int(rng.integers(0, 2**31 - 1))
                    group = group.sample(remaining, random_state=seed)
                collected.append(group)
                kept[label] += len(group)

    if not collected:
        raise RuntimeError("No rows were collected from the dataset.")

    df = pd.concat(collected, ignore_index=True)
    label_col = find_label_column(df.columns)
    if label_col != "Label":
        df = df.rename(columns={label_col: "Label"})
    df = df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)

    print("\nPrepared dataset:", output)
    print("Rows:", f"{len(df):,}")
    print("Class counts:")
    print(df["Label"].value_counts().to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare CIC-IDS2017 CSVs for local training.")
    parser.add_argument("--input-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--output", type=Path, default=PROCESSED_DIR / "cicids2017_prepared.csv")
    parser.add_argument("--max-per-class", type=int, default=DEFAULT_MAX_PER_CLASS,
                        help="Maximum rows retained for each attack family (keeps laptop training manageable).")
    parser.add_argument("--chunksize", type=int, default=100_000)
    args = parser.parse_args()
    prepare(args.input_dir, args.output, args.max_per_class, args.chunksize)
