import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"
CONFIG_PATH = PROJECT_ROOT / "config" / "screener_config.yaml"
MARKET_CAP_PATH = PROJECT_ROOT / "data" / "source" / "market_cap.xlsx"


# ============================================================
# CONFIG
# ============================================================

def load_config():
    """Load analyst-editable screener configuration."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


# ============================================================
# MARKET CAP / VALUATION DATA
# ============================================================

def load_market_cap_data():
    """
    Load market-cap and valuation data.

    Matching key:
        company_id + year
    """

    required_columns = [
        "company_id",
        "year",
        "market_cap_crore",
        "enterprise_value_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "dividend_yield_pct",
    ]

    if not MARKET_CAP_PATH.exists():
        raise FileNotFoundError(
            f"Market-cap file not found:\n{MARKET_CAP_PATH}"
        )

    df = pd.read_excel(MARKET_CAP_PATH)

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"market_cap.xlsx is missing columns: {missing}"
        )

    df = df[required_columns].copy()

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df = (
        df.sort_values(["company_id", "year"])
        .drop_duplicates(
            subset=["company_id", "year"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    return df


# ============================================================
# LOAD SCREENER DATA
# ============================================================

def load_screener_data():
    """
    Load the latest available financial-ratio record
    for each company and merge valuation data.
    """

    conn = sqlite3.connect(DB_PATH)

    query = """
    WITH latest_year AS (
        SELECT
            company_id,
            MAX(year) AS latest_year
        FROM financial_ratios
        GROUP BY company_id
    )

    SELECT
        fr.company_id,
        fr.year,

        c.company_name,

        COALESCE(
            s.broad_sector,
            c.broad_sector
        ) AS broad_sector,

        fr.return_on_equity_pct,
        fr.return_on_capital_employed_pct,
        fr.return_on_assets_pct,

        fr.debt_to_equity,
        fr.interest_coverage,
        fr.icr_label,
        fr.asset_turnover,

        fr.free_cash_flow_cr,
        fr.cash_from_operations_cr,
        fr.cfo_quality_score,

        fr.revenue_cagr_3yr,
        fr.revenue_cagr_5yr,

        fr.pat_cagr_5yr,
        fr.eps_cagr_5yr,

        fr.operating_profit_margin_pct,
        fr.net_profit_margin_pct,

        fr.dividend_payout_ratio_pct,

        fr.earnings_per_share,
        fr.book_value_per_share,

        pl.sales,
        pl.net_profit

    FROM financial_ratios fr

    INNER JOIN latest_year ly
        ON fr.company_id = ly.company_id
        AND fr.year = ly.latest_year

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

    LEFT JOIN profitandloss pl
        ON fr.company_id = pl.company_id
        AND fr.year = pl.year

    ORDER BY fr.company_id
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df = (
        df.sort_values(["company_id", "year"])
        .drop_duplicates(
            subset=["company_id"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    market_cap = load_market_cap_data()

    df = df.merge(
        market_cap,
        on=["company_id", "year"],
        how="left",
        validate="one_to_one",
    )

    return df


# ============================================================
# HISTORICAL D/E
# ============================================================

def load_historical_de_data():
    """Load historical D/E data for turnaround screening."""

    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        company_id,
        year,
        debt_to_equity
    FROM financial_ratios
    ORDER BY company_id, year
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    return df


def apply_debt_to_equity_declining(df):
    """
    Keep companies whose latest D/E is lower than
    their previous available year's D/E.
    """

    historical = load_historical_de_data()

    historical = historical.sort_values(
        ["company_id", "year"]
    )

    historical["previous_debt_to_equity"] = (
        historical
        .groupby("company_id")["debt_to_equity"]
        .shift(1)
    )

    latest = (
        historical
        .groupby("company_id")
        .tail(1)
        .copy()
    )

    latest["debt_to_equity_declining"] = (
        latest["debt_to_equity"].notna()
        & latest["previous_debt_to_equity"].notna()
        & (
            latest["debt_to_equity"]
            < latest["previous_debt_to_equity"]
        )
    )

    declining_ids = set(
        latest.loc[
            latest["debt_to_equity_declining"],
            "company_id",
        ]
    )

    return df[
        df["company_id"].isin(declining_ids)
    ].copy()


# ============================================================
# BASIC FILTER HELPERS
# ============================================================

def _apply_min(df, column, value):
    """Apply strict minimum threshold."""

    if column not in df.columns:
        raise KeyError(
            f"Required screener column not found: {column}"
        )

    return df[
        df[column].notna()
        & (df[column] > value)
    ].copy()


def _apply_max(df, column, value):
    """Apply strict maximum threshold."""

    if column not in df.columns:
        raise KeyError(
            f"Required screener column not found: {column}"
        )

    return df[
        df[column].notna()
        & (df[column] < value)
    ].copy()


def _apply_equals(df, column, value):
    """Apply equality threshold."""

    if column not in df.columns:
        raise KeyError(
            f"Required screener column not found: {column}"
        )

    return df[
        df[column].notna()
        & (df[column] == value)
    ].copy()


# ============================================================
# APPLY FILTERS
# ============================================================

def apply_filters(df, filters):
    """
    Apply all Sprint 3 screener filters.

    Supported metrics include:

    ROE
    ROCE
    FCF
    Revenue CAGR 3Y / 5Y
    PAT CAGR 5Y
    EPS CAGR 5Y
    OPM
    P/E
    P/B
    Dividend Yield
    Dividend Payout
    ICR
    Market Cap
    Net Profit
    Asset Turnover
    Sales
    D/E
    D/E declining
    """

    result = df.copy()

    filter_mapping = {

        "roe_min": (
            "return_on_equity_pct",
            "min",
        ),

        "roce_min": (
            "return_on_capital_employed_pct",
            "min",
        ),

        "free_cash_flow_min": (
            "free_cash_flow_cr",
            "min",
        ),

        "revenue_cagr_5yr_min": (
            "revenue_cagr_5yr",
            "min",
        ),

        "revenue_cagr_3yr_min": (
            "revenue_cagr_3yr",
            "min",
        ),

        "pat_cagr_5yr_min": (
            "pat_cagr_5yr",
            "min",
        ),

        "operating_profit_margin_min": (
            "operating_profit_margin_pct",
            "min",
        ),

        "interest_coverage_min": (
            "interest_coverage",
            "min",
        ),

        "net_profit_min": (
            "net_profit",
            "min",
        ),

        "eps_cagr_5yr_min": (
            "eps_cagr_5yr",
            "min",
        ),

        "asset_turnover_min": (
            "asset_turnover",
            "min",
        ),

        "sales_min": (
            "sales",
            "min",
        ),

        "dividend_payout_max": (
            "dividend_payout_ratio_pct",
            "max",
        ),

        "pe_max": (
            "pe_ratio",
            "max",
        ),

        "pb_max": (
            "pb_ratio",
            "max",
        ),

        "dividend_yield_min": (
            "dividend_yield_pct",
            "min",
        ),

        "market_cap_min": (
            "market_cap_crore",
            "min",
        ),
    }

    for filter_name, filter_value in filters.items():

        # ----------------------------------------------------
        # D/E MAX
        # ----------------------------------------------------

        if filter_name == "debt_to_equity_max":

            if "broad_sector" not in result.columns:
                raise KeyError(
                    "broad_sector is required for D/E filtering."
                )

            financials = result[
                result["broad_sector"]
                .fillna("")
                .astype(str)
                .str.strip()
                .eq("Financials")
            ].copy()

            non_financials = result[
                ~result["company_id"].isin(
                    financials["company_id"]
                )
            ].copy()

            non_financials = _apply_max(
                non_financials,
                "debt_to_equity",
                filter_value,
            )

            result = pd.concat(
                [
                    non_financials,
                    financials,
                ],
                ignore_index=True,
            )

            continue

        # ----------------------------------------------------
        # D/E EQUALS
        # ----------------------------------------------------

        if filter_name == "debt_to_equity_equals":

            result = _apply_equals(
                result,
                "debt_to_equity",
                filter_value,
            )

            continue

        # ----------------------------------------------------
        # ICR
        # ----------------------------------------------------

        if filter_name == "interest_coverage_min":

            debt_free = (
                result["icr_label"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
                .eq("debt free")
            )

            passes_numeric = (
                result["interest_coverage"].notna()
                & (
                    result["interest_coverage"]
                    > filter_value
                )
            )

            result = result[
                debt_free | passes_numeric
            ].copy()

            continue

        # ----------------------------------------------------
        # D/E DECLINING
        # ----------------------------------------------------

        if filter_name == "debt_to_equity_declining":

            if bool(filter_value):
                result = apply_debt_to_equity_declining(
                    result
                )

            continue

        # ----------------------------------------------------
        # STANDARD FILTERS
        # ----------------------------------------------------

        if filter_name in filter_mapping:

            column, operation = filter_mapping[
                filter_name
            ]

            if operation == "min":

                result = _apply_min(
                    result,
                    column,
                    filter_value,
                )

            elif operation == "max":

                result = _apply_max(
                    result,
                    column,
                    filter_value,
                )

    return result.reset_index(drop=True)


# ============================================================
# P10 / P90 WINSORISED NORMALISATION
# ============================================================

def winsorised_score(series, higher_is_better=True):
    """
    Convert a numeric series into a 0-100 score.

    Extreme values are capped at P10/P90 before scaling.
    """

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    valid = numeric.dropna()

    if valid.empty:
        return pd.Series(
            50.0,
            index=series.index,
            dtype=float,
        )

    p10 = valid.quantile(0.10)
    p90 = valid.quantile(0.90)

    if pd.isna(p10) or pd.isna(p90):
        return pd.Series(
            50.0,
            index=series.index,
            dtype=float,
        )

    if p10 == p90:
        score = pd.Series(
            50.0,
            index=series.index,
            dtype=float,
        )
        score[numeric.notna()] = 50.0
        return score

    capped = numeric.clip(
        lower=p10,
        upper=p90,
    )

    if higher_is_better:
        score = (
            (capped - p10)
            / (p90 - p10)
            * 100
        )
    else:
        score = (
            (p90 - capped)
            / (p90 - p10)
            * 100
        )

    return score.fillna(50.0)


# ============================================================
# SECTOR-RELATIVE NORMALISATION
# ============================================================

def sector_relative_score(
    df,
    column,
    higher_is_better=True,
):
    """
    Calculate P10/P90 winsorised scores within each
    broad sector.

    This ensures companies are evaluated relative to
    their sector peers.
    """

    score = pd.Series(
        np.nan,
        index=df.index,
        dtype=float,
    )

    if "broad_sector" not in df.columns:
        return winsorised_score(
            df[column],
            higher_is_better,
        )

    for sector, indexes in df.groupby(
        "broad_sector",
        dropna=False,
    ).groups.items():

        values = df.loc[indexes, column]

        score.loc[indexes] = winsorised_score(
            values,
            higher_is_better,
        )

    return score.fillna(50.0)


# ============================================================
# COMPOSITE QUALITY SCORE
# ============================================================

def calculate_composite_quality_score(df):
    """
    Calculate Sprint 3 composite quality score.

    Weighting:

    Profitability 35%
        ROE 15%
        ROCE 10%
        NPM 10%

    Cash Quality 30%
        FCF CAGR 15%
        CFO/PAT ratio 10%
        FCF positive flag 5%

    Growth 20%
        Revenue CAGR 10%
        PAT CAGR 10%

    Leverage 15%
        D/E score 10%
        ICR score 5%

    All metrics are P10/P90 winsorised and normalised
    within broad sector.
    """

    result = df.copy()

    # --------------------------------------------------------
    # FCF CAGR
    # --------------------------------------------------------

    if "company_id" in result.columns:

        conn = sqlite3.connect(DB_PATH)

        fcf_history = pd.read_sql_query(
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

        fcf_history["year"] = pd.to_numeric(
            fcf_history["year"],
            errors="coerce",
        )

        fcf_history["free_cash_flow_cr"] = pd.to_numeric(
            fcf_history["free_cash_flow_cr"],
            errors="coerce",
        )

        def calculate_fcf_cagr(group):
            group = (
                group
                .dropna(subset=["year", "free_cash_flow_cr"])
                .sort_values("year")
            )

            if len(group) < 2:
                return np.nan

            first = group.iloc[0]
            last = group.iloc[-1]

            first_value = first["free_cash_flow_cr"]
            last_value = last["free_cash_flow_cr"]

            years = last["year"] - first["year"]

            if (
                years <= 0
                or first_value <= 0
                or last_value <= 0
            ):
                return np.nan

            return (
                (
                    last_value
                    / first_value
                )
                ** (1 / years)
                - 1
            ) * 100

        fcf_cagr = (
            fcf_history
            .groupby("company_id")
            .apply(
                calculate_fcf_cagr,
                include_groups=False,
            )
            .rename("fcf_cagr")
            .reset_index()
        )

        result = result.merge(
            fcf_cagr,
            on="company_id",
            how="left",
        )

    # --------------------------------------------------------
    # CFO / PAT ratio
    # --------------------------------------------------------

    result["cfo_pat_ratio"] = np.nan

    if (
        "cash_from_operations_cr" in result.columns
        and "net_profit" in result.columns
    ):

        valid_pat = (
            result["net_profit"].notna()
            & (
                result["net_profit"]
                != 0
            )
        )

        result.loc[
            valid_pat,
            "cfo_pat_ratio",
        ] = (
            result.loc[
                valid_pat,
                "cash_from_operations_cr",
            ]
            / result.loc[
                valid_pat,
                "net_profit",
            ]
        )

    # --------------------------------------------------------
    # FCF positive flag
    # --------------------------------------------------------

    result["fcf_positive_flag"] = (
        pd.to_numeric(
            result["free_cash_flow_cr"],
            errors="coerce",
        )
        > 0
    ).astype(float)

    # --------------------------------------------------------
    # Sector-relative component scores
    # --------------------------------------------------------

    # Profitability
    result["score_roe"] = sector_relative_score(
        result,
        "return_on_equity_pct",
        higher_is_better=True,
    )

    result["score_roce"] = sector_relative_score(
        result,
        "return_on_capital_employed_pct",
        higher_is_better=True,
    )

    result["score_npm"] = sector_relative_score(
        result,
        "net_profit_margin_pct",
        higher_is_better=True,
    )

    result["profitability_score"] = (
        result["score_roe"] * 0.15
        + result["score_roce"] * 0.10
        + result["score_npm"] * 0.10
    )

    # Cash quality
    result["score_fcf_cagr"] = sector_relative_score(
        result,
        "fcf_cagr",
        higher_is_better=True,
    )

    result["score_cfo_pat"] = sector_relative_score(
        result,
        "cfo_pat_ratio",
        higher_is_better=True,
    )

    result["score_fcf_positive"] = (
        result["fcf_positive_flag"] * 100
    )

    result["cash_quality_score"] = (
        result["score_fcf_cagr"] * 0.15
        + result["score_cfo_pat"] * 0.10
        + result["score_fcf_positive"] * 0.05
    )

    # Growth
    result["score_revenue_cagr"] = sector_relative_score(
        result,
        "revenue_cagr_5yr",
        higher_is_better=True,
    )

    result["score_pat_cagr"] = sector_relative_score(
        result,
        "pat_cagr_5yr",
        higher_is_better=True,
    )

    result["growth_score"] = (
        result["score_revenue_cagr"] * 0.10
        + result["score_pat_cagr"] * 0.10
    )

    # Leverage
    result["score_de"] = sector_relative_score(
        result,
        "debt_to_equity",
        higher_is_better=False,
    )

    # Debt-free companies receive maximum ICR score.
    icr_score = sector_relative_score(
        result,
        "interest_coverage",
        higher_is_better=True,
    )

    debt_free = (
        result["icr_label"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("debt free")
    )

    icr_score.loc[debt_free] = 100.0

    result["score_icr"] = icr_score

    result["leverage_score"] = (
        result["score_de"] * 0.10
        + result["score_icr"] * 0.05
    )

    # --------------------------------------------------------
    # FINAL 0-100 COMPOSITE
    # --------------------------------------------------------

    result["composite_quality_score"] = (
        result["profitability_score"]
        + result["cash_quality_score"]
        + result["growth_score"]
        + result["leverage_score"]
    )

    result["composite_quality_score"] = (
        result["composite_quality_score"]
        .clip(0, 100)
        .round(4)
    )

    return result


# ============================================================
# RUN PRESET
# ============================================================

def run_preset(preset_name):
    """Run a named preset and return results sorted by score."""

    config = load_config()

    if preset_name not in config["presets"]:
        raise ValueError(
            f"Unknown preset: {preset_name}"
        )

    preset = config["presets"][preset_name]

    df = load_screener_data()

    result = apply_filters(
        df,
        preset["filters"],
    )

    # --------------------------------------------------------
    # Day 17 composite score
    # --------------------------------------------------------

    result = calculate_composite_quality_score(
        result
    )

    # --------------------------------------------------------
    # Sort highest score first
    # --------------------------------------------------------

    result = result.sort_values(
        by="composite_quality_score",
        ascending=False,
        na_position="last",
    )

    return result.reset_index(drop=True)


# ============================================================
# LIST PRESETS
# ============================================================

def list_presets():
    """Return configured preset names."""

    config = load_config()

    return list(
        config["presets"].keys()
    )


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("SPRINT 3 SCREENER ENGINE")
    print("=" * 70)

    data = load_screener_data()

    print(
        f"\nLatest company records loaded: {len(data)}"
    )

    print(
        "Unique companies:",
        data["company_id"].nunique(),
    )

    print(
        "Market-cap matches:",
        data["market_cap_crore"].notna().sum(),
    )

    print(
        "Market-cap missing:",
        data["market_cap_crore"].isna().sum(),
    )

    print("\nPreset results:")

    for preset in list_presets():

        result = run_preset(preset)

        print(
            f"\n{preset}"
            f" -> {len(result)} companies"
        )

        if not result.empty:

            display_columns = [
                "company_id",
                "company_name",
                "year",
                "return_on_equity_pct",
                "debt_to_equity",
                "composite_quality_score",
            ]

            print(
                result[
                    display_columns
                ]
                .head(5)
                .to_string(index=False)
            )

    print("\n" + "=" * 70)
    print("SCREENER ENGINE COMPLETE")
    print("=" * 70)