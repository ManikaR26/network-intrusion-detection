import argparse
from pathlib import Path
import pandas as pd

from src.inference import analyze_dataframe


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a network-flow CSV from the command line.")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--output", type=Path, default=Path("reports/predictions.csv"))
    args = parser.parse_args()

    df = pd.read_csv(args.csv, low_memory=False)
    results, info = analyze_dataframe(df)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.output, index=False)
    print(results["Prediction"].value_counts().to_string())
    print("\nRisk counts:")
    print(results["Risk"].value_counts().to_string())
    print(f"\nSaved predictions: {args.output}")
    if info["missing_features"]:
        print(f"Filled {len(info['missing_features'])} missing feature(s) using training medians.")
