import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from config import DEMO_DIR, RANDOM_STATE

FEATURES = [
    "Destination Port", "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
    "Total Length of Fwd Packets", "Total Length of Bwd Packets", "Fwd Packet Length Mean",
    "Bwd Packet Length Mean", "Flow Bytes/s", "Flow Packets/s", "Flow IAT Mean",
    "Flow IAT Std", "Fwd IAT Mean", "Bwd IAT Mean", "Fwd PSH Flags", "SYN Flag Count",
    "RST Flag Count", "ACK Flag Count", "Packet Length Mean", "Average Packet Size",
    "Init_Win_bytes_forward", "Init_Win_bytes_backward", "Active Mean", "Idle Mean"
]

LABELS = ["BENIGN", "DDoS", "DoS", "PortScan", "BruteForce", "Bot", "WebAttack"]


def _positive(rng, mean, sd, n, floor=0.0):
    return np.clip(rng.normal(mean, sd, n), floor, None)


def make_class(rng, label, n):
    # Synthetic but structured data ONLY for verifying the code pipeline.
    # Real project training should use CIC-IDS2017.
    base = pd.DataFrame(index=np.arange(n))
    attack = label != "BENIGN"

    if label == "BENIGN":
        port = rng.choice([53, 80, 443, 22, 123, 8080], n, p=[.10,.20,.45,.08,.07,.10])
        duration = _positive(rng, 450000, 300000, n)
        fwd = _positive(rng, 14, 8, n)
        bwd = _positive(rng, 12, 7, n)
        bytes_rate = _positive(rng, 60000, 40000, n)
        pkt_rate = _positive(rng, 80, 55, n)
        syn = rng.binomial(1, .06, n)
        rst = rng.binomial(1, .02, n)
    elif label == "DDoS":
        port = rng.choice([80, 443, 8080], n)
        duration = _positive(rng, 90000, 65000, n)
        fwd = _positive(rng, 85, 35, n)
        bwd = _positive(rng, 8, 5, n)
        bytes_rate = _positive(rng, 1_800_000, 650_000, n)
        pkt_rate = _positive(rng, 2200, 700, n)
        syn = rng.binomial(1, .70, n)
        rst = rng.binomial(1, .08, n)
    elif label == "DoS":
        port = rng.choice([80, 443], n)
        duration = _positive(rng, 180000, 130000, n)
        fwd = _positive(rng, 55, 25, n)
        bwd = _positive(rng, 10, 6, n)
        bytes_rate = _positive(rng, 950000, 420000, n)
        pkt_rate = _positive(rng, 950, 350, n)
        syn = rng.binomial(1, .45, n)
        rst = rng.binomial(1, .10, n)
    elif label == "PortScan":
        port = rng.integers(1, 65535, n)
        duration = _positive(rng, 30000, 22000, n)
        fwd = _positive(rng, 4, 2, n)
        bwd = _positive(rng, 2, 2, n)
        bytes_rate = _positive(rng, 18000, 10000, n)
        pkt_rate = _positive(rng, 600, 300, n)
        syn = rng.binomial(1, .82, n)
        rst = rng.binomial(1, .35, n)
    elif label == "BruteForce":
        port = rng.choice([21, 22, 80, 443], n, p=[.25,.35,.20,.20])
        duration = _positive(rng, 220000, 120000, n)
        fwd = _positive(rng, 18, 7, n)
        bwd = _positive(rng, 14, 6, n)
        bytes_rate = _positive(rng, 90000, 45000, n)
        pkt_rate = _positive(rng, 180, 80, n)
        syn = rng.binomial(1, .30, n)
        rst = rng.binomial(1, .12, n)
    elif label == "Bot":
        port = rng.choice([80, 443, 6667, 53], n)
        duration = _positive(rng, 700000, 380000, n)
        fwd = _positive(rng, 30, 14, n)
        bwd = _positive(rng, 24, 11, n)
        bytes_rate = _positive(rng, 260000, 150000, n)
        pkt_rate = _positive(rng, 260, 140, n)
        syn = rng.binomial(1, .18, n)
        rst = rng.binomial(1, .06, n)
    else:  # WebAttack
        port = rng.choice([80, 443, 8080], n)
        duration = _positive(rng, 350000, 180000, n)
        fwd = _positive(rng, 24, 9, n)
        bwd = _positive(rng, 20, 8, n)
        bytes_rate = _positive(rng, 160000, 80000, n)
        pkt_rate = _positive(rng, 210, 90, n)
        syn = rng.binomial(1, .14, n)
        rst = rng.binomial(1, .05, n)

    base["Destination Port"] = port
    base["Flow Duration"] = duration
    base["Total Fwd Packets"] = fwd
    base["Total Backward Packets"] = bwd
    base["Total Length of Fwd Packets"] = fwd * _positive(rng, 380 if not attack else 520, 160, n)
    base["Total Length of Bwd Packets"] = bwd * _positive(rng, 420, 150, n)
    base["Fwd Packet Length Mean"] = _positive(rng, 380 if not attack else 500, 120, n)
    base["Bwd Packet Length Mean"] = _positive(rng, 410, 130, n)
    base["Flow Bytes/s"] = bytes_rate
    base["Flow Packets/s"] = pkt_rate
    base["Flow IAT Mean"] = _positive(rng, 22000 if not attack else 5000, 7000, n)
    base["Flow IAT Std"] = _positive(rng, 9000, 5000, n)
    base["Fwd IAT Mean"] = _positive(rng, 26000 if not attack else 7000, 9000, n)
    base["Bwd IAT Mean"] = _positive(rng, 30000, 11000, n)
    base["Fwd PSH Flags"] = rng.binomial(1, .12 if not attack else .28, n)
    base["SYN Flag Count"] = syn
    base["RST Flag Count"] = rst
    base["ACK Flag Count"] = rng.binomial(1, .75 if not attack else .48, n)
    base["Packet Length Mean"] = _positive(rng, 400 if not attack else 470, 125, n)
    base["Average Packet Size"] = base["Packet Length Mean"] + _positive(rng, 20, 10, n)
    base["Init_Win_bytes_forward"] = rng.integers(0, 65535, n)
    base["Init_Win_bytes_backward"] = rng.integers(0, 65535, n)
    base["Active Mean"] = _positive(rng, 45000 if not attack else 16000, 16000, n)
    base["Idle Mean"] = _positive(rng, 85000 if not attack else 28000, 26000, n)
    base["Label"] = label
    return base


def generate(rows: int, output: Path):
    rng = np.random.default_rng(RANDOM_STATE)
    proportions = {
        "BENIGN": .45, "DDoS": .13, "DoS": .12, "PortScan": .10,
        "BruteForce": .08, "Bot": .06, "WebAttack": .06
    }
    frames = []
    assigned = 0
    for i, label in enumerate(LABELS):
        n = rows - assigned if i == len(LABELS)-1 else int(rows * proportions[label])
        assigned += n
        frames.append(make_class(rng, label, n))
    df = pd.concat(frames, ignore_index=True).sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    upload = output.parent / "upload_sample.csv"
    df.drop(columns=["Label"]).sample(min(350, len(df)), random_state=7).to_csv(upload, index=False)
    print(f"Created demo training data: {output} ({len(df):,} rows)")
    print(f"Created dashboard upload sample: {upload}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=6000)
    parser.add_argument("--output", type=Path, default=DEMO_DIR / "demo_network_traffic.csv")
    args = parser.parse_args()
    generate(args.rows, args.output)
