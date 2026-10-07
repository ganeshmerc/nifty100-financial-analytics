"""
Sprint 5 - Day 31
Cash Flow Intelligence

Outputs:
    output/cashflow_intelligence.xlsx
    output/distress_alerts.csv
"""

from pathlib import Path
import sqlite3

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"

INTELLIGENCE_OUTPUT = OUTPUT_DIR / "cashflow_intelligence.xlsx"
DISTRESS_OUTPUT = OUTPUT_DIR / "distress_alerts.csv"


def free_cash_flow(operating_activity, investing_activity):
    """Free Cash Flow = CFO + Investing Activity."""
    return operating_activity + investing_activity


def cfo_quality_score(cfo, pat):
    """
    CFO/PAT ratio and quality classification.

    High Quality: > 1.0
    Moderate:     0.5 to 1.0
    Accrual Risk: < 0.5
    """
    if pat is None or pat == 0:
        return None, None

    ratio = cfo / pat

    if ratio > 1.0:
        label = "High Quality"
    elif ratio >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return ratio, label


def capex_intensity(investing_activity, sales):
    """
    CapEx intensity = abs(investing activity) / sales * 100.

    Asset Light:       < 3%
    Moderate:          3% to 8%
    Capital Intensive: > 8%
    """
    if sales is None or sales == 0:
        return None, None

    value = abs(investing_activity) / sales * 100

    if value < 3:
        label = "Asset Light"
    elif value <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return value, label


def fcf_conversion_rate(fcf, operating_profit):
    """FCF / Operating Profit * 100."""
    if operating_profit is None or operating_profit == 0:
        return None

    return (fcf / operating_profit) * 100


def fcf_cagr(first_fcf, latest_fcf, years):
    """Calculate FCF CAGR when both endpoint values are positive."""
    if (
        first_fcf is None
        or latest_fcf is None
        or first_fcf <= 0
        or latest_fcf <= 0
        or years <= 0
    ):
        return None

    return ((latest_fcf / first_fcf) ** (1 / years) - 1) * 100


def load_data():
    """Load company, sector, cash-flow and P&L data."""
    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        """
        SELECT company_id, company_name, ticker
        FROM companies
        """,
        conn,
    )

    sectors = pd.read_sql_query(
        """
        SELECT company_id, sector
        FROM sectors
        """,
        conn,
    )

    cashflow = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            operating_activity,
            investing_activity,
            financing_activity
        FROM cashflow
        ORDER BY company_id, year
        """,
        conn,
    )

    pnl = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            sales,
            net_profit,
            operating_profit
        FROM profitandloss
        ORDER BY company_id, year
        """,
        conn,
    )

    conn.close()

    return companies, sectors, cashflow, pnl


def calculate_company_metrics(company_id, sector, cashflow, pnl):
    """Calculate latest-year and historical cash-flow intelligence."""

    cf = cashflow[cashflow["company_id"] == company_id].copy()
    pl = pnl[pnl["company_id"] == company_id].copy()

    if cf.empty or pl.empty:
        return None, None

    merged = cf.merge(
        pl,
        on=["company_id", "year"],
        how="inner",
    ).sort_values("year")

    if merged.empty:
        return None, None

    merged["free_cash_flow"] = (
        merged["operating_activity"] + merged["investing_activity"]
    )

    # CFO/PAT ratio for every available year.
    merged["cfo_pat_ratio"] = merged.apply(
        lambda row: (
            row["operating_activity"] / row["net_profit"]
            if pd.notna(row["net_profit"]) and row["net_profit"] != 0
            else None
        ),
        axis=1,
    )

    # Average CFO/PAT ratio across available years.
    valid_cfo_ratios = merged["cfo_pat_ratio"].dropna()

    avg_cfo_quality_score = (
        valid_cfo_ratios.mean()
        if not valid_cfo_ratios.empty
        else None
    )

    if avg_cfo_quality_score is None:
        cfo_label = None
    elif avg_cfo_quality_score > 1.0:
        cfo_label = "High Quality"
    elif avg_cfo_quality_score >= 0.5:
        cfo_label = "Moderate"
    else:
        cfo_label = "Accrual Risk"

    # Latest year.
    latest = merged.iloc[-1]

    latest_capex_intensity, capex_label = capex_intensity(
        latest["investing_activity"],
        latest["sales"],
    )

    latest_fcf = latest["free_cash_flow"]

    # FCF conversion.
    conversion = fcf_conversion_rate(
        latest_fcf,
        latest["operating_profit"],
    )

    # 5-year FCF CAGR.
    fcf_cagr_value = None

    if len(merged) >= 6:
        first_5yr = merged.iloc[-6]
        fcf_cagr_value = fcf_cagr(
            first_5yr["free_cash_flow"],
            latest_fcf,
            5,
        )

    # Distress:
    # Latest CFO < 0 AND CFF > 0.
    distress_flag = bool(
        latest["operating_activity"] < 0
        and latest["financing_activity"] > 0
    )

    # Deleveraging:
    # Latest CFF < 0 AND borrowings declining YoY.
    #
    # The cash-flow table does not contain borrowings.
    # Therefore this cannot be calculated from the available source data.
    deleveraging_flag = False

    # Capital allocation label.
    if distress_flag:
        capital_allocation_label = "Distress / Financing Dependent"
    elif latest["financing_activity"] < 0:
        capital_allocation_label = "Shareholder Returns / Deleveraging"
    elif latest["financing_activity"] > 0:
        capital_allocation_label = "External Financing"
    else:
        capital_allocation_label = "Neutral"

    result = {
        "company_id": company_id,
        "sector": sector,
        "cfo_quality_score": (
            round(avg_cfo_quality_score, 4)
            if avg_cfo_quality_score is not None
            else None
        ),
        "cfo_quality_label": cfo_label,
        "capex_intensity_pct": (
            round(latest_capex_intensity, 4)
            if latest_capex_intensity is not None
            else None
        ),
        "capex_label": capex_label,
        "fcf_cagr_5yr": (
            round(fcf_cagr_value, 4)
            if fcf_cagr_value is not None
            else None
        ),
        "fcf_conversion_pct": (
            round(conversion, 4)
            if conversion is not None
            else None
        ),
        "distress_flag": distress_flag,
        "deleveraging_flag": deleveraging_flag,
        "capital_allocation_label": capital_allocation_label,
    }

    distress_record = None

    if distress_flag:
        distress_record = {
            "company_id": company_id,
            "year": int(latest["year"]),
            "cfo": latest["operating_activity"],
            "cff": latest["financing_activity"],
            "latest_net_profit": latest["net_profit"],
        }

    return result, distress_record


def main():
    print("=" * 70)
    print("DAY 31 — CASH FLOW INTELLIGENCE")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    companies, sectors, cashflow, pnl = load_data()

    print(f"Companies in universe: {len(companies)}")
    print(f"Companies with cash flow data: {cashflow['company_id'].nunique()}")
    print(f"Companies with P&L data: {pnl['company_id'].nunique()}")

    sector_map = dict(
        zip(sectors["company_id"], sectors["sector"])
    )

    results = []
    distress_records = []
    skipped = []

    for company_id in companies["company_id"]:
        sector = sector_map.get(company_id)

        result, distress_record = calculate_company_metrics(
            company_id,
            sector,
            cashflow,
            pnl,
        )

        if result is None:
            skipped.append(company_id)
            continue

        results.append(result)

        if distress_record is not None:
            distress_records.append(distress_record)

    intelligence_df = pd.DataFrame(results)

    required_columns = [
        "company_id",
        "sector",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation_label",
    ]

    intelligence_df = intelligence_df[required_columns]

    distress_df = pd.DataFrame(
        distress_records,
        columns=[
            "company_id",
            "year",
            "cfo",
            "cff",
            "latest_net_profit",
        ],
    )

    intelligence_df.to_excel(
        INTELLIGENCE_OUTPUT,
        index=False,
    )

    distress_df.to_csv(
        DISTRESS_OUTPUT,
        index=False,
    )

    print()
    print("OUTPUT")
    print(f"Cash flow intelligence: {INTELLIGENCE_OUTPUT}")
    print(f"Distress alerts:        {DISTRESS_OUTPUT}")

    print()
    print("VALIDATION")
    print(f"Generated companies: {len(intelligence_df)}")
    print(f"Skipped companies:   {len(skipped)}")

    if skipped:
        print(f"Skipped: {skipped}")

    print(f"Distress alerts: {len(distress_df)}")

    print()
    print("CFO QUALITY DISTRIBUTION")
    print(
        intelligence_df["cfo_quality_label"]
        .value_counts(dropna=False)
        .to_string()
    )

    print()
    print("CAPEX DISTRIBUTION")
    print(
        intelligence_df["capex_label"]
        .value_counts(dropna=False)
        .to_string()
    )

    print()
    print("CAPITAL ALLOCATION DISTRIBUTION")
    print(
        intelligence_df["capital_allocation_label"]
        .value_counts(dropna=False)
        .to_string()
    )

    print()
    print("DAY 31 CASH FLOW INTELLIGENCE COMPLETE")


if __name__ == "__main__":
    main()