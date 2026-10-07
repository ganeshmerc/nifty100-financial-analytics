import pandas as pd
from pathlib import Path

BASE = Path("data/source")

files = {
    "Balance Sheet": BASE / "balancesheet.xlsx",
    "Cash Flow": BASE / "cashflow.xlsx",
    "P&L": BASE / "profitandloss.xlsx",
}

targets = ["SBIN", "ATGL"]

print("=" * 70)
print("SOURCE EXCEL COMPANY CHECK")
print("=" * 70)

for label, path in files.items():
    print(f"\n{'-' * 70}")
    print(label)
    print(f"File: {path}")
    print("-" * 70)

    df = pd.read_excel(path)

    print("Columns:")
    print(df.columns.tolist())

    for target in targets:
        # Search all columns for the company ID
        mask = df.astype(str).apply(
            lambda col: col.str.strip().str.upper().eq(target)
        ).any(axis=1)

        matches = df[mask]

        print(f"\n{target}")
        print(f"Matching rows: {len(matches)}")

        if len(matches) > 0:
            print(matches.head(20).to_string(index=False))
        else:
            print("NOT FOUND")

print("\n" + "=" * 70)
print("CHECK COMPLETE")
print("=" * 70)
