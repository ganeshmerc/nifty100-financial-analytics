import sqlite3
import pandas as pd

DB = "db/nifty100.db"

conn = sqlite3.connect(DB)

query = """
SELECT
    p.company_id,
    p.year,
    p.sales,
    p.net_profit,
    b.equity_capital,
    b.reserves,
    r.return_on_equity_pct,
    r.revenue_cagr_5yr
FROM profitandloss p
JOIN balancesheet b
    ON p.company_id = b.company_id
    AND p.year = b.year
JOIN financial_ratios r
    ON p.company_id = r.company_id
    AND p.year = r.year
WHERE r.return_on_equity_pct IS NOT NULL
ORDER BY p.company_id, p.year
"""

df = pd.read_sql(query, conn)

print("=" * 70)
print("SPRINT 2 MANUAL SPOT-CHECK")
print("=" * 70)

# Find companies with at least 6 years of usable data
companies = (
    df.groupby("company_id")
      .size()
      .loc[lambda x: x >= 6]
      .head(3)
      .index
      .tolist()
)

if len(companies) < 3:
    print("ERROR: Could not find 3 companies with sufficient data.")
    conn.close()
    raise SystemExit

all_pass = True

for company in companies:

    data = df[df["company_id"] == company].copy()
    data = data.sort_values("year")

    latest = data.iloc[-1]

    # ==========================================================
    # ROE MANUAL CALCULATION
    # ==========================================================

    equity = latest["equity_capital"] + latest["reserves"]

    if equity > 0:
        manual_roe = latest["net_profit"] / equity * 100
    else:
        manual_roe = None

    db_roe = latest["return_on_equity_pct"]

    if manual_roe is not None and pd.notna(db_roe):
        roe_diff = abs(manual_roe - db_roe)
    else:
        roe_diff = None

    # ==========================================================
    # REVENUE CAGR 5Y MANUAL CALCULATION
    # ==========================================================

    if len(data) >= 6:

        start = data.iloc[-6]["sales"]
        end = data.iloc[-1]["sales"]

        if start > 0 and end > 0:

            manual_cagr = (
                (end / start) ** (1 / 5) - 1
            ) * 100

        else:
            manual_cagr = None

    else:
        manual_cagr = None

    db_cagr = latest["revenue_cagr_5yr"]

    if manual_cagr is not None and pd.notna(db_cagr):
        cagr_diff = abs(manual_cagr - db_cagr)
    else:
        cagr_diff = None

    # ==========================================================
    # OUTPUT
    # ==========================================================

    print()
    print("-" * 70)
    print(f"Company: {company}")
    print(f"Latest year: {latest['year']}")

    print()
    print("ROE")
    print(f"  Manual : {manual_roe:.6f}" if manual_roe is not None else "  Manual : None")
    print(f"  DB     : {db_roe:.6f}" if pd.notna(db_roe) else "  DB     : None")
    print(f"  Diff   : {roe_diff:.6f}" if roe_diff is not None else "  Diff   : N/A")

    print()
    print("Revenue CAGR 5Y")
    print(
        f"  Manual : {manual_cagr:.6f}"
        if manual_cagr is not None
        else "  Manual : None"
    )
    print(
        f"  DB     : {db_cagr:.6f}"
        if pd.notna(db_cagr)
        else "  DB     : None"
    )
    print(
        f"  Diff   : {cagr_diff:.6f}"
        if cagr_diff is not None
        else "  Diff   : N/A"
    )

    # ==========================================================
    # PASS / FAIL
    # ==========================================================

    roe_pass = roe_diff is not None and roe_diff <= 0.1
    cagr_pass = cagr_diff is not None and cagr_diff <= 0.1

    print()

    if roe_pass:
        print("ROE CHECK: PASS")
    else:
        print("ROE CHECK: REVIEW")
        all_pass = False

    if cagr_pass:
        print("CAGR CHECK: PASS")
    else:
        print("CAGR CHECK: REVIEW")
        all_pass = False


print()
print("=" * 70)

if all_pass:
    print("OVERALL SPOT-CHECK: PASS")
    print("All 3 companies passed ROE and 5Y Revenue CAGR checks.")
else:
    print("OVERALL SPOT-CHECK: REVIEW")
    print("One or more checks require investigation.")

print("=" * 70)

conn.close()