import pandas as pd
import sqlite3

# Load parsed analysis values
parsed = pd.read_csv("output/analysis_parsed.csv")

# Connect to database
conn = sqlite3.connect("db/nifty100.db")

# Get Ratio Engine data
query = """
SELECT
    company_id,
    year,
    revenue_cagr_3yr,
    revenue_cagr_5yr,
    revenue_cagr_10yr,
    pat_cagr_3yr,
    pat_cagr_5yr,
    pat_cagr_10yr
FROM financial_ratios
WHERE company_id IN (?, ?, ?, ?, ?)
ORDER BY company_id, year DESC
"""

companies = ["HDFCBANK", "SBILIFE", "TCS", "WIPRO", "INFY"]

ratio = pd.read_sql_query(
    query,
    conn,
    params=companies
)

conn.close()

# Keep latest available year for each company
ratio = ratio.drop_duplicates("company_id")

results = []

for _, row in parsed.iterrows():

    if row["metric_type"] not in ["revenue_cagr", "pat_cagr"]:
        continue

    company = row["company_id"]
    metric = row["metric_type"]
    years = int(row["period_years"])
    parsed_value = float(row["value_pct"])

    matching = ratio[ratio["company_id"] == company]

    if matching.empty:
        continue

    ratio_row = matching.iloc[0]

    column = f"{metric}_{years}yr"
    ratio_value = ratio_row[column]

    if pd.isna(ratio_value):
        continue

    divergence = abs(parsed_value - float(ratio_value))

    results.append({
        "company_id": company,
        "metric_type": metric,
        "period_years": years,
        "parsed_pct": parsed_value,
        "ratio_engine_pct": float(ratio_value),
        "divergence_pp": round(divergence, 2),
        "manual_review": divergence > 5
    })

# Create validation table
validation = pd.DataFrame(results)

print("=" * 70)
print("DAY 29 — CAGR CROSS-VALIDATION")
print("=" * 70)

print(validation.to_string(index=False))

print("\n" + "=" * 70)
print("MANUAL REVIEW — DIVERGENCE > 5 PERCENTAGE POINTS")
print("=" * 70)

manual = validation[validation["manual_review"]]

if manual.empty:
    print("None")
else:
    print(manual.to_string(index=False))

# Save outputs
validation.to_csv(
    "output/cagr_cross_validation.csv",
    index=False
)

manual.to_csv(
    "output/cagr_manual_review.csv",
    index=False
)

print("\nSaved:")
print("output/cagr_cross_validation.csv")
print("output/cagr_manual_review.csv")
print("\nDAY 29 CROSS-VALIDATION COMPLETE")