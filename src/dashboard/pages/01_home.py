from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import get_companies, get_ratios


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MARKET_CAP_PATH = PROJECT_ROOT / "data" / "source" / "market_cap.xlsx"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Nifty 100 Financial Overview",
    page_icon="🏠",
    layout="wide",
)


# ============================================================
# HELPERS
# ============================================================

def fmt_number(value, decimals=2):
    if pd.isna(value):
        return "N/A"
    return f"{value:,.{decimals}f}"


def fmt_pct(value, decimals=2):
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}%"


# ============================================================
# MARKET DATA
# ============================================================

@st.cache_data(ttl=600)
def load_market_data():
    """Load market valuation data from market_cap.xlsx."""

    try:
        df = pd.read_excel(MARKET_CAP_PATH)

        required = [
            "company_id",
            "year",
            "pe_ratio",
            "pb_ratio",
            "dividend_yield_pct",
        ]

        missing = [
            col for col in required
            if col not in df.columns
        ]

        if missing:
            return pd.DataFrame()

        df["year"] = pd.to_numeric(
            df["year"],
            errors="coerce"
        )

        for col in [
            "pe_ratio",
            "pb_ratio",
            "dividend_yield_pct",
        ]:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

        return df

    except Exception:
        return pd.DataFrame()


# ============================================================
# LOAD HOME DATA
# ============================================================

@st.cache_data(ttl=600)
def load_home_data(year):
    """
    Build the Home dashboard dataset.

    Ratios are loaded company-by-company because
    get_ratios() expects a specific company identifier.
    """

    companies = get_companies().copy()
    market = load_market_data()

    if companies.empty:
        return pd.DataFrame()

    # --------------------------------------------------------
    # Company information
    # --------------------------------------------------------

    companies = companies.rename(
        columns={
            "broad_sector": "sector"
        }
    )

    company_cols = [
        col
        for col in [
            "company_id",
            "company_name",
            "sector",
            "ticker",
            "symbol",
        ]
        if col in companies.columns
    ]

    companies = companies[company_cols].drop_duplicates(
        subset=["company_id"]
    )

    # --------------------------------------------------------
    # Load ratios for every company
    # --------------------------------------------------------

    ratio_frames = []

    for company_id in companies["company_id"].dropna().unique():

        try:
            company_ratios = get_ratios(
                company_id,
                year
            )

            if (
                company_ratios is not None
                and not company_ratios.empty
            ):
                ratio_frames.append(company_ratios)

        except Exception:
            continue

    if ratio_frames:
        ratios = pd.concat(
            ratio_frames,
            ignore_index=True
        )
    else:
        ratios = pd.DataFrame()

    # --------------------------------------------------------
    # Normalize ratios
    # --------------------------------------------------------

    if not ratios.empty:

        if "year" in ratios.columns:
            ratios["year"] = pd.to_numeric(
                ratios["year"],
                errors="coerce"
            )

            ratios = ratios[
                ratios["year"] == int(year)
            ].copy()

        if "company_id" in ratios.columns:
            ratios = ratios.drop_duplicates(
                subset=["company_id"],
                keep="last"
            )

    # --------------------------------------------------------
    # Merge companies + ratios
    # --------------------------------------------------------

    if not ratios.empty and "company_id" in ratios.columns:

        df = companies.merge(
            ratios,
            on="company_id",
            how="left",
            suffixes=("", "_ratio"),
        )

    else:

        df = companies.copy()

    # --------------------------------------------------------
    # Merge market data
    # --------------------------------------------------------

    if not market.empty:

        market_year = market[
            market["year"] == int(year)
        ].copy()

        market_year = market_year.drop_duplicates(
            subset=["company_id"],
            keep="last"
        )

        market_cols = [
            col
            for col in [
                "company_id",
                "pe_ratio",
                "pb_ratio",
                "dividend_yield_pct",
            ]
            if col in market_year.columns
        ]

        if market_cols:

            df = df.merge(
                market_year[market_cols],
                on="company_id",
                how="left",
            )

    return df


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("Dashboard")

available_years = list(range(2019, 2025))

selected_year = st.sidebar.selectbox(
    "Financial Year",
    available_years,
    index=available_years.index(2024),
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "Select a financial year to update the market-wide metrics."
)


# ============================================================
# LOAD DATA
# ============================================================

df = load_home_data(selected_year)


# ============================================================
# HEADER
# ============================================================

st.title("🏠 Nifty 100 Financial Overview")

st.caption(
    "Market-wide financial performance across the "
    "92-company analytics universe."
)


if df.empty:
    st.error("Unable to load dashboard data.")
    st.stop()


# ============================================================
# KEY METRICS
# ============================================================

roe_col = "return_on_equity_pct"
debt_col = "debt_to_equity"
cagr_col = "revenue_cagr_5yr"
score_col = "composite_quality_score"


# ------------------------------------------------------------
# Average ROE
# ------------------------------------------------------------

if roe_col in df.columns:

    avg_roe = pd.to_numeric(
        df[roe_col],
        errors="coerce"
    ).dropna().mean()

else:
    avg_roe = None


# ------------------------------------------------------------
# Median P/E
# ------------------------------------------------------------

if "pe_ratio" in df.columns:

    pe_values = pd.to_numeric(
        df["pe_ratio"],
        errors="coerce"
    ).dropna()

    median_pe = (
        pe_values.median()
        if not pe_values.empty
        else None
    )

else:
    median_pe = None


# ------------------------------------------------------------
# Median D/E
# ------------------------------------------------------------

if debt_col in df.columns:

    de_values = pd.to_numeric(
        df[debt_col],
        errors="coerce"
    ).dropna()

    median_de = (
        de_values.median()
        if not de_values.empty
        else None
    )

else:
    median_de = None


# ------------------------------------------------------------
# Total Companies
# ------------------------------------------------------------

total_companies = df["company_id"].nunique()


# ------------------------------------------------------------
# Median Revenue CAGR
# ------------------------------------------------------------

if cagr_col in df.columns:

    cagr_values = pd.to_numeric(
        df[cagr_col],
        errors="coerce"
    ).dropna()

    median_cagr = (
        cagr_values.median()
        if not cagr_values.empty
        else None
    )

else:
    median_cagr = None


# ------------------------------------------------------------
# Debt-Free Companies
# ------------------------------------------------------------

if debt_col in df.columns:

    debt_values = pd.to_numeric(
        df[debt_col],
        errors="coerce"
    )

    debt_free_count = int(
        (debt_values.fillna(999) <= 0).sum()
    )

else:
    debt_free_count = 0


# ============================================================
# KPI DISPLAY
# ============================================================

st.subheader(
    f"Key Metrics — {selected_year}"
)

k1, k2, k3, k4, k5, k6 = st.columns(6)


with k1:

    st.metric(
        "Average ROE",
        fmt_pct(avg_roe)
    )


with k2:

    st.metric(
        "Median P/E",
        fmt_number(median_pe)
    )


with k3:

    st.metric(
        "Median D/E",
        fmt_number(median_de)
    )


with k4:

    st.metric(
        "Total Companies",
        f"{total_companies:,}"
    )


with k5:

    st.metric(
        "Median Revenue CAGR (5Y)",
        fmt_pct(median_cagr)
    )


with k6:

    st.metric(
        "Debt-Free Companies",
        f"{debt_free_count:,}"
    )


st.markdown("---")


# ============================================================
# SECTOR DISTRIBUTION + TOP 5
# ============================================================

left_col, right_col = st.columns([1, 1])


# ============================================================
# SECTOR DONUT
# ============================================================

with left_col:

    st.subheader("🏭 Sector Distribution")

    if "sector" in df.columns:

        sector_df = (
            df[
                df["sector"].notna()
                & (
                    df["sector"]
                    .astype(str)
                    .str.strip()
                    != ""
                )
            ]
            .groupby(
                "sector",
                as_index=False
            )
            .size()
            .rename(
                columns={
                    "size": "companies"
                }
            )
            .sort_values(
                "companies",
                ascending=False
            )
        )

        if not sector_df.empty:

            fig = px.pie(
                sector_df,
                names="sector",
                values="companies",
                hole=0.55,
            )

            fig.update_traces(
                textposition="inside",
                textinfo="percent",
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Companies: %{value}<br>"
                    "Share: %{percent}"
                    "<extra></extra>"
                ),
            )

            fig.update_layout(
                height=430,
                margin=dict(
                    l=10,
                    r=10,
                    t=20,
                    b=10,
                ),
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info(
                "Sector data unavailable."
            )

    else:

        st.info(
            "Sector data unavailable."
        )


# ============================================================
# TOP 5 COMPOSITE SCORES
# ============================================================

with right_col:

    st.subheader("🏆 Top 5 Composite Scores")

    if score_col in df.columns:

        top5 = df.copy()

        top5[score_col] = pd.to_numeric(
            top5[score_col],
            errors="coerce"
        )

        top5 = (
            top5[
                top5[score_col].notna()
            ]
            .sort_values(
                score_col,
                ascending=False
            )
            .head(5)
        )

        if not top5.empty:

            display_cols = [
                "company_id",
                "company_name",
                "sector",
                score_col,
            ]

            display_cols = [
                col
                for col in display_cols
                if col in top5.columns
            ]

            display_df = top5[
                display_cols
            ].copy()

            display_df = display_df.rename(
                columns={
                    "company_id": "Ticker",
                    "company_name": "Company",
                    "sector": "Sector",
                    score_col: "Composite Score",
                }
            )

            if "Composite Score" in display_df.columns:

                display_df[
                    "Composite Score"
                ] = pd.to_numeric(
                    display_df[
                        "Composite Score"
                    ],
                    errors="coerce"
                ).round(2)

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "Composite score data unavailable."
            )

    else:

        st.info(
            "Composite score data unavailable."
        )


# ============================================================
# DATA COVERAGE
# ============================================================

st.markdown("---")

st.subheader("📊 Data Coverage")

coverage_cols = st.columns(4)


with coverage_cols[0]:

    st.metric(
        "Companies",
        f"{df['company_id'].nunique():,}"
    )


with coverage_cols[1]:

    if roe_col in df.columns:

        roe_coverage = int(
            df[roe_col].notna().sum()
        )

    else:

        roe_coverage = 0

    st.metric(
        "ROE Coverage",
        f"{roe_coverage}/{total_companies}"
    )


with coverage_cols[2]:

    if "pe_ratio" in df.columns:

        pe_coverage = int(
            df["pe_ratio"].notna().sum()
        )

    else:

        pe_coverage = 0

    st.metric(
        "P/E Coverage",
        f"{pe_coverage}/{total_companies}"
    )


with coverage_cols[3]:

    if cagr_col in df.columns:

        cagr_coverage = int(
            df[cagr_col].notna().sum()
        )

    else:

        cagr_coverage = 0

    st.metric(
        "Revenue CAGR Coverage",
        f"{cagr_coverage}/{total_companies}"
    )


# ============================================================
# FOOTER
# ============================================================

st.caption(
    f"Nifty 100 Financial Analytics • "
    f"Financial Year {selected_year}"
)