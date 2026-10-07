"""
Sprint 3 - Composite Quality Score

0-100 composite score based on:
- Profitability: 35%
- Cash Quality: 30%
- Growth: 20%
- Leverage: 15%

Uses P10/P90 winsorisation and sector-relative normalization.
"""

from __future__ import annotations

import math
import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"


# ---------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------

def load_score_data():
    """
    Load the latest available financial-ratio record for each company,
    together with sector and latest net profit.
    """

    conn = sqlite3.connect(DB_PATH)

    query = """
        WITH latest AS (
            SELECT
                company_id,
                MAX(year) AS year
            FROM financial_ratios
            GROUP BY company_id
        )
        SELECT
            fr.company_id,
            fr.year,

            fr.net_profit_margin_pct,
            fr.return_on_equity_pct,
            fr.return_on_capital_employed_pct,

            fr.debt_to_equity,
            fr.interest_coverage,

            fr.free_cash_flow_cr,
            fr.cash_from_operations_cr,

            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,

            c.company_name,
            COALESCE(s.broad_sector, 'Unknown') AS broad_sector,

            p.net_profit

        FROM financial_ratios fr

        INNER JOIN latest l
            ON fr.company_id = l.company_id
            AND fr.year = l.year

        LEFT JOIN companies c
            ON fr.company_id = c.company_id

        LEFT JOIN (
            SELECT
                company_id,
                MAX(broad_sector) AS broad_sector
            FROM sectors
            GROUP BY company_id
        ) s
            ON fr.company_id = s.company_id

        LEFT JOIN profitandloss p
            ON fr.company_id = p.company_id
            AND fr.year = p.year
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


def load_historical_fcf():
    """Load historical FCF values for FCF CAGR calculation."""

    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            free_cash_flow_cr
        FROM financial_ratios
        ORDER BY company_id, year
        """,
        conn,
    )

    conn.close()

    return df


# ---------------------------------------------------------------------
# FCF CAGR
# ---------------------------------------------------------------------

def calculate_fcf_cagr(history):
    """
    Calculate FCF CAGR using the earliest and latest available
    positive FCF values for each company.

    A CAGR is returned only when both endpoints are positive
    and the period is greater than zero.
    """

    rows = []

    for company_id, group in history.groupby("company_id"):

        group = group.dropna(
            subset=["free_cash_flow_cr"]
        ).sort_values("year")

        if group.empty:
            continue

        positive = group[
            group["free_cash_flow_cr"] > 0
        ]

        if len(positive) < 2:
            continue

        start = positive.iloc[0]
        end = positive.iloc[-1]

        start_fcf = float(start["free_cash_flow_cr"])
        end_fcf = float(end["free_cash_flow_cr"])

        start_year = int(start["year"])
        end_year = int(end["year"])

        years = end_year - start_year

        if years <= 0:
            continue

        try:
            cagr = (
                (end_fcf / start_fcf) ** (1 / years) - 1
            ) * 100
        except (ValueError, ZeroDivisionError, OverflowError):
            continue

        if math.isfinite(cagr):
            rows.append(
                {
                    "company_id": company_id,
                    "fcf_cagr_5yr": cagr,
                }
            )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# Winsorisation and normalization
# ---------------------------------------------------------------------

def winsorize_series(series):
    """
    Cap values at the 10th and 90th percentiles.
    """

    s = pd.to_numeric(series, errors="coerce")

    valid = s.dropna()

    if valid.empty:
        return s

    p10 = valid.quantile(0.10)
    p90 = valid.quantile(0.90)

    return s.clip(lower=p10, upper=p90)


def normalize_0_100(series, inverse=False):
    """
    Convert a metric to a 0-100 score after P10/P90 winsorisation.

    inverse=True means lower raw values receive higher scores.
    """

    s = winsorize_series(series)

    valid = s.dropna()

    if valid.empty:
        return pd.Series(index=series.index, dtype=float)

    minimum = valid.min()
    maximum = valid.max()

    if maximum == minimum:
        result = pd.Series(
            50.0,
            index=series.index,
            dtype=float,
        )
    else:
        result = (
            (s - minimum)
            / (maximum - minimum)
            * 100
        )

    if inverse:
        result = 100 - result

    return result


# ---------------------------------------------------------------------
# Composite score
# ---------------------------------------------------------------------

def calculate_composite_scores(df):
    """
    Calculate the Sprint 3 composite quality score.

    Profitability = 35%
        ROE  = 15%
        ROCE = 10%
        NPM  = 10%

    Cash Quality = 30%
        FCF CAGR       = 15%
        CFO/PAT ratio  = 10%
        FCF positive   = 5%

    Growth = 20%
        Revenue CAGR = 10%
        PAT CAGR     = 10%

    Leverage = 15%
        D/E  = 10%
        ICR  = 5%
    """

    result = df.copy()

    # ---------------------------------------------------------------
    # CFO / PAT ratio
    # ---------------------------------------------------------------

    result["cfo_pat_ratio"] = (
        pd.to_numeric(
            result["cash_from_operations_cr"],
            errors="coerce",
        )
        /
        pd.to_numeric(
            result["net_profit"],
            errors="coerce",
        )
    )

    result.loc[
        ~result["cfo_pat_ratio"].replace(
            [float("inf"), float("-inf")],
            pd.NA,
        ).notna(),
        "cfo_pat_ratio",
    ] = pd.NA

    # ---------------------------------------------------------------
    # FCF positive flag
    # ---------------------------------------------------------------

    result["fcf_positive"] = (
        pd.to_numeric(
            result["free_cash_flow_cr"],
            errors="coerce",
        ) > 0
    ).astype(float)

    result.loc[
        result["free_cash_flow_cr"].isna(),
        "fcf_positive",
    ] = pd.NA

    # ---------------------------------------------------------------
    # Metric scores
    # ---------------------------------------------------------------

    result["roe_score"] = normalize_0_100(
        result["return_on_equity_pct"]
    )

    result["roce_score"] = normalize_0_100(
        result["return_on_capital_employed_pct"]
    )

    result["npm_score"] = normalize_0_100(
        result["net_profit_margin_pct"]
    )

    result["fcf_cagr_score"] = normalize_0_100(
        result["fcf_cagr_5yr"]
    )

    result["cfo_pat_score"] = normalize_0_100(
        result["cfo_pat_ratio"]
    )

    result["revenue_growth_score"] = normalize_0_100(
        result["revenue_cagr_5yr"]
    )

    result["pat_growth_score"] = normalize_0_100(
        result["pat_cagr_5yr"]
    )

    result["de_score"] = normalize_0_100(
        result["debt_to_equity"],
        inverse=True,
    )

    result["icr_score"] = normalize_0_100(
        result["interest_coverage"]
    )

    # ---------------------------------------------------------------
    # Weighted components
    # ---------------------------------------------------------------

    result["profitability_score"] = (
        result["roe_score"] * 0.15
        + result["roce_score"] * 0.10
        + result["npm_score"] * 0.10
    )

    result["cash_quality_score"] = (
        result["fcf_cagr_score"] * 0.15
        + result["cfo_pat_score"] * 0.10
        + result["fcf_positive"] * 0.05 * 100
    )

    result["growth_score"] = (
        result["revenue_growth_score"] * 0.10
        + result["pat_growth_score"] * 0.10
    )

    result["leverage_score"] = (
        result["de_score"] * 0.10
        + result["icr_score"] * 0.05
    )

    # ---------------------------------------------------------------
    # Final score
    # ---------------------------------------------------------------

    score_columns = [
        "profitability_score",
        "cash_quality_score",
        "growth_score",
        "leverage_score",
    ]

    result["composite_quality_score"] = (
        result[score_columns]
        .sum(axis=1, min_count=1)
        .clip(lower=0, upper=100)
    )

    return result


# ---------------------------------------------------------------------
# Sector-relative normalization
# ---------------------------------------------------------------------

def apply_sector_relative_score(df):
    """
    Normalize the final composite score within broad_sector.

    The highest-quality company within a sector approaches 100,
    while the lowest approaches 0.
    """

    result = df.copy()

    def sector_score(group):
        score = group["composite_quality_score"]

        if score.notna().sum() <= 1:
            return pd.Series(
                50.0,
                index=group.index,
            )

        minimum = score.min()
        maximum = score.max()

        if maximum == minimum:
            return pd.Series(
                50.0,
                index=group.index,
            )

        return (
            (score - minimum)
            / (maximum - minimum)
            * 100
        )

    result["sector_relative_quality_score"] = (
        result.groupby(
            "broad_sector",
            group_keys=False,
        ).apply(
            sector_score,
            include_groups=False,
        )
    )

    return result


# ---------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------

def build_quality_scores():
    """
    Build the complete Sprint 3 quality-score dataset.
    """

    df = load_score_data()

    historical_fcf = load_historical_fcf()

    fcf_cagr = calculate_fcf_cagr(
        historical_fcf
    )

    df = df.merge(
        fcf_cagr,
        on="company_id",
        how="left",
    )

    df = calculate_composite_scores(df)

    df = apply_sector_relative_score(df)

    return df


# ---------------------------------------------------------------------
# Database update
# ---------------------------------------------------------------------

def save_scores_to_database(df):
    """
    Save the final sector-relative score to financial_ratios.
    """

    conn = sqlite3.connect(DB_PATH)

    rows = 0

    for row in df.itertuples(index=False):

        conn.execute(
            """
            UPDATE financial_ratios
            SET composite_quality_score = ?
            WHERE company_id = ?
              AND year = ?
            """,
            (
                None
                if pd.isna(
                    row.sector_relative_quality_score
                )
                else float(
                    row.sector_relative_quality_score
                ),
                row.company_id,
                int(row.year),
            ),
        )

        rows += 1

    conn.commit()
    conn.close()

    return rows


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "\nSPRINT 3 - DAY 17 "
        "COMPOSITE QUALITY SCORE\n"
    )

    scores = build_quality_scores()

    print(
        "Companies scored:",
        len(scores),
    )

    print(
        "FCF CAGR available:",
        scores["fcf_cagr_5yr"].notna().sum(),
    )

    print(
        "Composite scores available:",
        scores["composite_quality_score"].notna().sum(),
    )

    print("\nTop 10:")

    columns = [
        "company_id",
        "company_name",
        "broad_sector",
        "composite_quality_score",
        "sector_relative_quality_score",
    ]

    print(
        scores.sort_values(
            "sector_relative_quality_score",
            ascending=False,
        )[columns]
        .head(10)
        .to_string(index=False)
    )

    updated = save_scores_to_database(scores)

    print(
        "\nDatabase rows updated:",
        updated,
    )

    print(
        "\nDAY 17 QUALITY SCORE COMPLETE"
    )