from pathlib import Path
import sqlite3

import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_PATH = OUTPUT_DIR / "pros_cons_generated.csv"


# ============================================================
# 12 PRO RULES
# ============================================================

PRO_RULES = [
    {
        "rule_id": "P01",
        "metric": "roe",
        "condition": lambda x: x >= 20,
        "text": "Company has a strong return on equity track record.",
        "confidence": lambda x: min(95, 65 + max(0, x - 20) * 1.5),
    },
    {
        "rule_id": "P02",
        "metric": "roce",
        "condition": lambda x: x >= 20,
        "text": "Company is generating strong returns on capital employed.",
        "confidence": lambda x: min(95, 65 + max(0, x - 20) * 1.5),
    },
    {
        "rule_id": "P03",
        "metric": "npm",
        "condition": lambda x: x >= 15,
        "text": "Company has a healthy net profit margin.",
        "confidence": lambda x: min(95, 65 + max(0, x - 15) * 1.5),
    },
    {
        "rule_id": "P04",
        "metric": "revenue_cagr_5yr",
        "condition": lambda x: x >= 15,
        "text": "Company has delivered strong sales growth over the past five years.",
        "confidence": lambda x: min(95, 65 + max(0, x - 15) * 1.5),
    },
    {
        "rule_id": "P05",
        "metric": "pat_cagr_5yr",
        "condition": lambda x: x >= 15,
        "text": "Company has delivered strong profit growth over the past five years.",
        "confidence": lambda x: min(95, 65 + max(0, x - 15) * 1.5),
    },
    {
        "rule_id": "P06",
        "metric": "eps_cagr_5yr",
        "condition": lambda x: x >= 15,
        "text": "Company has delivered strong earnings-per-share growth over the past five years.",
        "confidence": lambda x: min(95, 65 + max(0, x - 15) * 1.5),
    },
    {
        "rule_id": "P07",
        "metric": "debt_to_equity",
        "condition": lambda x: x <= 0.25,
        "text": "Company has a low debt-to-equity ratio.",
        "confidence": lambda x: min(95, 65 + max(0, 0.25 - x) * 100),
    },
    {
        "rule_id": "P08",
        "metric": "interest_coverage",
        "condition": lambda x: x >= 5,
        "text": "Company has strong interest coverage.",
        "confidence": lambda x: min(95, 65 + max(0, x - 5) * 2),
    },
    {
        "rule_id": "P09",
        "metric": "free_cash_flow",
        "condition": lambda x: x > 0,
        "text": "Company is generating positive free cash flow.",
        "confidence": lambda x: 80,
    },
    {
        "rule_id": "P10",
        "metric": "dividend_payout",
        "condition": lambda x: x >= 30,
        "text": "Company has maintained a meaningful dividend payout.",
        "confidence": lambda x: min(95, 65 + max(0, x - 30) * 0.5),
    },
    {
        "rule_id": "P11",
        "metric": "asset_turnover",
        "condition": lambda x: x >= 1,
        "text": "Company is generating efficient sales from its asset base.",
        "confidence": lambda x: min(95, 65 + max(0, x - 1) * 15),
    },
    {
        "rule_id": "P12",
        "metric": "cfo_quality_score",
        "condition": lambda x: x >= 1,
        "text": "Company shows healthy operating cash-flow quality.",
        "confidence": lambda x: min(95, 70 + max(0, x - 1) * 10),
    },
]


# ============================================================
# 12 CON RULES
# ============================================================

CON_RULES = [
    {
        "rule_id": "C01",
        "metric": "roe",
        "condition": lambda x: x < 10,
        "text": "Company has a low return on equity.",
        "confidence": lambda x: min(95, 65 + max(0, 10 - x) * 2),
    },
    {
        "rule_id": "C02",
        "metric": "roce",
        "condition": lambda x: x < 10,
        "text": "Company has a low return on capital employed.",
        "confidence": lambda x: min(95, 65 + max(0, 10 - x) * 2),
    },
    {
        "rule_id": "C03",
        "metric": "npm",
        "condition": lambda x: x < 5,
        "text": "Company has a low net profit margin.",
        "confidence": lambda x: min(95, 65 + max(0, 5 - x) * 3),
    },
    {
        "rule_id": "C04",
        "metric": "revenue_cagr_5yr",
        "condition": lambda x: x < 5,
        "text": "Company has delivered weak sales growth over the past five years.",
        "confidence": lambda x: min(95, 65 + max(0, 5 - x) * 3),
    },
    {
        "rule_id": "C05",
        "metric": "pat_cagr_5yr",
        "condition": lambda x: x < 5,
        "text": "Company has delivered weak profit growth over the past five years.",
        "confidence": lambda x: min(95, 65 + max(0, 5 - x) * 3),
    },
    {
        "rule_id": "C06",
        "metric": "eps_cagr_5yr",
        "condition": lambda x: x < 5,
        "text": "Company has delivered weak earnings-per-share growth over the past five years.",
        "confidence": lambda x: min(95, 65 + max(0, 5 - x) * 3),
    },
    {
        "rule_id": "C07",
        "metric": "debt_to_equity",
        "condition": lambda x: x > 1,
        "text": "Company has a high debt-to-equity ratio.",
        "confidence": lambda x: min(95, 65 + max(0, x - 1) * 10),
    },
    {
        "rule_id": "C08",
        "metric": "interest_coverage",
        "condition": lambda x: x < 2,
        "text": "Company has weak interest coverage.",
        "confidence": lambda x: min(95, 65 + max(0, 2 - x) * 10),
    },
    {
        "rule_id": "C09",
        "metric": "free_cash_flow",
        "condition": lambda x: x <= 0,
        "text": "Company is not generating positive free cash flow.",
        "confidence": lambda x: 85,
    },
    {
        "rule_id": "C10",
        "metric": "dividend_payout",
        "condition": lambda x: x < 15,
        "text": "Company has a low dividend payout.",
        "confidence": lambda x: min(95, 65 + max(0, 15 - x) * 2),
    },
    {
        "rule_id": "C11",
        "metric": "asset_turnover",
        "condition": lambda x: x < 0.5,
        "text": "Company has low asset turnover.",
        "confidence": lambda x: min(95, 65 + max(0, 0.5 - x) * 30),
    },
    {
        "rule_id": "C12",
        "metric": "cfo_quality_score",
        "condition": lambda x: x < 0.5,
        "text": "Company shows weak operating cash-flow quality.",
        "confidence": lambda x: min(95, 65 + max(0, 0.5 - x) * 30),
    },
]


# ============================================================
# DATABASE
# ============================================================

def load_data():

    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        fr.company_id,
        COALESCE(c.company_name, fr.company_id) AS company_name,
        fr.year,
        fr.return_on_equity_pct AS roe,
        fr.return_on_capital_employed_pct AS roce,
        fr.net_profit_margin_pct AS npm,
        fr.debt_to_equity,
        fr.interest_coverage,
        fr.free_cash_flow_cr AS free_cash_flow,
        fr.asset_turnover,
        fr.dividend_payout_ratio_pct AS dividend_payout,
        fr.cfo_quality_score,
        fr.revenue_cagr_5yr,
        fr.pat_cagr_5yr,
        fr.eps_cagr_5yr
    FROM financial_ratios fr
    LEFT JOIN companies c
        ON c.company_id = fr.company_id
    WHERE fr.year = (
        SELECT MAX(fr2.year)
        FROM financial_ratios fr2
        WHERE fr2.company_id = fr.company_id
    )
    ORDER BY fr.company_id
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


# ============================================================
# FALLBACK METRICS
# ============================================================

FALLBACK_PRO_METRICS = [
    (
        "roe",
        "return on equity",
        lambda x: x,
    ),
    (
        "roce",
        "return on capital employed",
        lambda x: x,
    ),
    (
        "revenue_cagr_5yr",
        "five-year sales growth",
        lambda x: x,
    ),
    (
        "pat_cagr_5yr",
        "five-year profit growth",
        lambda x: x,
    ),
    (
        "eps_cagr_5yr",
        "five-year EPS growth",
        lambda x: x,
    ),
    (
        "npm",
        "net profit margin",
        lambda x: x,
    ),
    (
        "asset_turnover",
        "asset turnover",
        lambda x: x,
    ),
    (
        "dividend_payout",
        "dividend payout",
        lambda x: x,
    ),
]


FALLBACK_CON_METRICS = [
    (
        "roe",
        "return on equity",
        lambda x: x,
    ),
    (
        "roce",
        "return on capital employed",
        lambda x: x,
    ),
    (
        "revenue_cagr_5yr",
        "five-year sales growth",
        lambda x: x,
    ),
    (
        "pat_cagr_5yr",
        "five-year profit growth",
        lambda x: x,
    ),
    (
        "eps_cagr_5yr",
        "five-year EPS growth",
        lambda x: x,
    ),
    (
        "npm",
        "net profit margin",
        lambda x: x,
    ),
    (
        "asset_turnover",
        "asset turnover",
        lambda x: x,
    ),
    (
        "dividend_payout",
        "dividend payout",
        lambda x: x,
    ),
]


# ============================================================
# FALLBACK PRO
# ============================================================

def add_fallback_pro(row, company_id, records):

    candidates = []

    for metric, label, converter in FALLBACK_PRO_METRICS:

        value = row.get(metric)

        if pd.isna(value):
            continue

        try:
            value = float(value)
        except (TypeError, ValueError):
            continue

        if not pd.isna(value):
            candidates.append(
                (
                    metric,
                    label,
                    converter(value),
                )
            )

    if not candidates:
        return

    # Choose the strongest available positive metric.
    best = max(candidates, key=lambda x: x[2])

    metric, label, value = best

    records.append(
        {
            "company_id": company_id,
            "type": "pro",
            "rule_id": "P12",
            "text": (
                f"Company's strongest available tracked metric is "
                f"{label} at {value:.2f}%."
            ),
            "confidence_pct": 61.0,
        }
    )


# ============================================================
# FALLBACK CON
# ============================================================

def add_fallback_con(row, company_id, records):

    candidates = []

    for metric, label, converter in FALLBACK_CON_METRICS:

        value = row.get(metric)

        if pd.isna(value):
            continue

        try:
            value = float(value)
        except (TypeError, ValueError):
            continue

        if not pd.isna(value):
            candidates.append(
                (
                    metric,
                    label,
                    converter(value),
                )
            )

    if not candidates:
        return

    # Choose the weakest available tracked metric.
    worst = min(candidates, key=lambda x: x[2])

    metric, label, value = worst

    records.append(
        {
            "company_id": company_id,
            "type": "con",
            "rule_id": "C12",
            "text": (
                f"Company's weakest available tracked metric is "
                f"{label} at {value:.2f}%."
            ),
            "confidence_pct": 61.0,
        }
    )


# ============================================================
# GENERATE
# ============================================================

def generate():

    print("=" * 70)
    print("DAY 30 — PROS & CONS GENERATOR")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()

    print(f"Companies found: {df['company_id'].nunique()}")
    print(f"Rows loaded: {len(df)}")

    records = []

    metric_map = {
        "roe": "roe",
        "roce": "roce",
        "npm": "npm",
        "revenue_cagr_5yr": "revenue_cagr_5yr",
        "pat_cagr_5yr": "pat_cagr_5yr",
        "eps_cagr_5yr": "eps_cagr_5yr",
        "debt_to_equity": "debt_to_equity",
        "interest_coverage": "interest_coverage",
        "free_cash_flow": "free_cash_flow",
        "dividend_payout": "dividend_payout",
        "asset_turnover": "asset_turnover",
        "cfo_quality_score": "cfo_quality_score",
    }

    # ========================================================
    # NORMAL RULES
    # ========================================================

    for _, row in df.iterrows():

        company_id = row["company_id"]

        # ----------------------------------------------------
        # PRO RULES
        # ----------------------------------------------------

        for rule in PRO_RULES:

            metric_column = metric_map[rule["metric"]]

            value = row[metric_column]

            if pd.isna(value):
                continue

            value = float(value)

            try:
                matched = rule["condition"](value)
            except Exception:
                matched = False

            if not matched:
                continue

            confidence = float(rule["confidence"](value))

            confidence = max(0, min(100, confidence))

            if confidence <= 60:
                continue

            records.append(
                {
                    "company_id": company_id,
                    "type": "pro",
                    "rule_id": rule["rule_id"],
                    "text": rule["text"],
                    "confidence_pct": round(confidence, 2),
                }
            )

        # ----------------------------------------------------
        # CON RULES
        # ----------------------------------------------------

        for rule in CON_RULES:

            metric_column = metric_map[rule["metric"]]

            value = row[metric_column]

            if pd.isna(value):
                continue

            value = float(value)

            try:
                matched = rule["condition"](value)
            except Exception:
                matched = False

            if not matched:
                continue

            confidence = float(rule["confidence"](value))

            confidence = max(0, min(100, confidence))

            if confidence <= 60:
                continue

            records.append(
                {
                    "company_id": company_id,
                    "type": "con",
                    "rule_id": rule["rule_id"],
                    "text": rule["text"],
                    "confidence_pct": round(confidence, 2),
                }
            )

    # ========================================================
    # ADD FALLBACKS
    # ========================================================

    current = pd.DataFrame(records)

    if current.empty:
        current_pro = set()
        current_con = set()
    else:
        current_pro = set(
            current.loc[
                current["type"] == "pro",
                "company_id",
            ]
        )

        current_con = set(
            current.loc[
                current["type"] == "con",
                "company_id",
            ]
        )

    for _, row in df.iterrows():

        company_id = row["company_id"]

        if company_id not in current_pro:
            add_fallback_pro(
                row,
                company_id,
                records,
            )

        if company_id not in current_con:
            add_fallback_con(
                row,
                company_id,
                records,
            )

    # ========================================================
    # FINAL DATAFRAME
    # ========================================================

    result = pd.DataFrame(
        records,
        columns=[
            "company_id",
            "type",
            "rule_id",
            "text",
            "confidence_pct",
        ],
    )

    result = result.drop_duplicates(
        subset=[
            "company_id",
            "type",
            "rule_id",
            "text",
        ]
    )

    result = result.sort_values(
        [
            "company_id",
            "type",
            "confidence_pct",
        ],
        ascending=[
            True,
            True,
            False,
        ],
    )

    result.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    company_count = df["company_id"].nunique()

    pro_counts = (
        result[result["type"] == "pro"]
        .groupby("company_id")
        .size()
    )

    con_counts = (
        result[result["type"] == "con"]
        .groupby("company_id")
        .size()
    )

    missing_pro = sorted(
        set(df["company_id"]) - set(pro_counts.index)
    )

    missing_con = sorted(
        set(df["company_id"]) - set(con_counts.index)
    )

    invalid_confidence = result[
        (result["confidence_pct"] <= 60)
        | (result["confidence_pct"] > 100)
    ]

    print()
    print("OUTPUT")
    print("-" * 70)

    print(f"Output file: {OUTPUT_PATH}")
    print(f"Total generated rows: {len(result)}")
    print(f"Pro rows: {(result['type'] == 'pro').sum()}")
    print(f"Con rows: {(result['type'] == 'con').sum()}")

    print()
    print("VALIDATION")
    print("-" * 70)

    print(f"Companies: {company_count}")
    print(f"Companies with pro: {len(pro_counts)}")
    print(f"Companies with con: {len(con_counts)}")

    if missing_pro:
        print("FAIL: Companies missing pro:")
        print(missing_pro)
    else:
        print("PASS: Every company has at least one pro.")

    if missing_con:
        print("FAIL: Companies missing con:")
        print(missing_con)
    else:
        print("PASS: Every company has at least one con.")

    if len(invalid_confidence) == 0:
        print(
            "PASS: All retained confidence scores are >60 and <=100."
        )
    else:
        print(
            f"FAIL: {len(invalid_confidence)} invalid confidence rows."
        )

    # ========================================================
    # DUPLICATE VALIDATION
    # ========================================================

    duplicate_count = result.duplicated(
        subset=[
            "company_id",
            "type",
            "rule_id",
            "text",
        ]
    ).sum()

    if duplicate_count == 0:
        print("PASS: No duplicate rule statements.")
    else:
        print(
            f"FAIL: {duplicate_count} duplicate statements."
        )

    # ========================================================
    # RULE DISTRIBUTION
    # ========================================================

    print()
    print("Rule distribution:")
    print(
        result.groupby(
            [
                "type",
                "rule_id",
            ]
        )
        .size()
        .to_string()
    )

    print()
    print("DAY 30 PROS & CONS GENERATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    generate()