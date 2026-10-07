import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import (
    get_companies,
    get_sectors,
    get_latest_ratios,
    get_pl,
    get_valuation,
)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Sector Analysis | Nifty 100 Analytics",
    page_icon="🏭",
    layout="wide",
)

# ============================================================
# LOAD DATA
# ============================================================

companies = get_companies()
sectors = get_sectors()
ratios = get_latest_ratios()

# ------------------------------------------------------------
# Make sure expected columns exist
# ------------------------------------------------------------

if sectors.empty:
    st.warning("No sector data is available.")
    st.stop()

if "sub_sector" not in sectors.columns:
    sectors["sub_sector"] = "N/A"

# Remove duplicate company-sector records
sectors = sectors.drop_duplicates(subset=["company_id", "sector"])

# ============================================================
# TITLE
# ============================================================

st.title("🏭 Sector Analysis")
st.caption(
    "Compare companies and financial performance across Nifty 100 sectors."
)

# ============================================================
# SECTOR SELECTION
# ============================================================

sector_list = sorted(
    sectors["sector"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

if not sector_list:
    st.warning("No sectors are available.")
    st.stop()

selected_sector = st.selectbox(
    "🏷️ Select Sector",
    sector_list,
)

# ============================================================
# FILTER SELECTED SECTOR
# ============================================================

sector_companies = sectors[
    sectors["sector"].astype(str) == selected_sector
].copy()

if sector_companies.empty:
    st.warning("No companies are available for this sector.")
    st.stop()

# ============================================================
# MERGE COMPANY INFORMATION
# ============================================================

company_columns = [
    col
    for col in [
        "company_id",
        "company_name",
        "ticker",
        "broad_sector",
    ]
    if col in companies.columns
]

company_data = companies[company_columns].drop_duplicates(
    subset=["company_id"]
)

sector_companies = sector_companies.merge(
    company_data,
    on="company_id",
    how="left",
)

# ============================================================
# MERGE FINANCIAL RATIOS
# ============================================================

if not ratios.empty and "company_id" in ratios.columns:
    ratio_columns = [
        col
        for col in [
            "company_id",
            "return_on_equity_pct",
            "debt_to_equity",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "operating_profit_margin_pct",
            "composite_quality_score",
        ]
        if col in ratios.columns
    ]

    ratio_data = ratios[ratio_columns].drop_duplicates(
        subset=["company_id"]
    )

    sector_companies = sector_companies.merge(
        ratio_data,
        on="company_id",
        how="left",
    )

# ============================================================
# GET REVENUE FROM P&L
# ============================================================

revenue_rows = []

for company_id in sector_companies["company_id"].dropna().unique():

    try:
        pl = get_pl(company_id)

        if pl is None or pl.empty:
            continue

        if "sales" not in pl.columns:
            continue

        pl = pl.copy()

        if "year" in pl.columns:
            pl = pl.sort_values("year")

        latest = pl.iloc[-1]

        revenue_rows.append(
            {
                "company_id": company_id,
                "revenue": latest.get("sales"),
            }
        )

    except Exception:
        continue

if revenue_rows:
    revenue_df = pd.DataFrame(revenue_rows)

    sector_companies = sector_companies.merge(
        revenue_df,
        on="company_id",
        how="left",
    )
else:
    sector_companies["revenue"] = pd.NA

# ============================================================
# MARKET CAP
# ============================================================

sector_companies["market_cap"] = pd.NA

try:
    valuation = get_valuation()

    if valuation is not None and not valuation.empty:

        valuation = valuation.copy()

        # Find market-cap column
        market_cap_col = None

        for col in [
            "market_cap_crore",
            "market_cap_cr",
            "market_cap",
            "Market Cap",
        ]:
            if col in valuation.columns:
                market_cap_col = col
                break

        if market_cap_col:

            # Try to find company identifier
            id_col = None

            for col in [
                "company_id",
                "ticker",
                "symbol",
            ]:
                if col in valuation.columns:
                    id_col = col
                    break

            if id_col:

                valuation_small = valuation[
                    [id_col, market_cap_col]
                ].copy()

                valuation_small = valuation_small.rename(
                    columns={
                        id_col: "company_id",
                        market_cap_col: "market_cap",
                    }
                )

                valuation_small = valuation_small.drop_duplicates(
                    subset=["company_id"]
                )

                sector_companies = sector_companies.drop(
                    columns=["market_cap"],
                    errors="ignore",
                )

                sector_companies = sector_companies.merge(
                    valuation_small,
                    on="company_id",
                    how="left",
                )

except Exception:
    pass

# ============================================================
# KPI SECTION
# ============================================================

st.subheader(f"📊 {selected_sector}")

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Companies",
    len(sector_companies),
)

roe_median = (
    pd.to_numeric(
        sector_companies.get("return_on_equity_pct"),
        errors="coerce",
    ).median()
)

de_median = (
    pd.to_numeric(
        sector_companies.get("debt_to_equity"),
        errors="coerce",
    ).median()
)

cagr_median = (
    pd.to_numeric(
        sector_companies.get("revenue_cagr_5yr"),
        errors="coerce",
    ).median()
)

k2.metric(
    "Median ROE",
    f"{roe_median:.2f}%"
    if pd.notna(roe_median)
    else "N/A",
)

k3.metric(
    "Median D/E",
    f"{de_median:.2f}"
    if pd.notna(de_median)
    else "N/A",
)

k4.metric(
    "Median Revenue CAGR",
    f"{cagr_median:.2f}%"
    if pd.notna(cagr_median)
    else "N/A",
)

# ============================================================
# BUBBLE CHART
# ============================================================

st.subheader("📈 Revenue vs ROE")

chart_df = sector_companies.copy()

chart_df["Revenue"] = pd.to_numeric(
    chart_df.get("revenue"),
    errors="coerce",
)

chart_df["ROE"] = pd.to_numeric(
    chart_df.get("return_on_equity_pct"),
    errors="coerce",
)

chart_df["Market Cap"] = pd.to_numeric(
    chart_df.get("market_cap"),
    errors="coerce",
)

chart_df["Company"] = chart_df["company_name"].fillna(
    chart_df["company_id"]
)

chart_df["Sub Sector"] = chart_df["sub_sector"].fillna("N/A")

chart_df = chart_df.dropna(
    subset=["Revenue", "ROE"]
)

if not chart_df.empty:

    size_col = "Market Cap"

    if chart_df["Market Cap"].notna().any():

        fig = px.scatter(
            chart_df,
            x="Revenue",
            y="ROE",
            size=size_col,
            color="Sub Sector",
            hover_name="Company",
            hover_data=[
                "company_id",
                "Revenue",
                "ROE",
            ],
            title=f"{selected_sector} — Revenue vs ROE",
        )

    else:

        fig = px.scatter(
            chart_df,
            x="Revenue",
            y="ROE",
            color="Sub Sector",
            hover_name="Company",
            hover_data=[
                "company_id",
                "Revenue",
                "ROE",
            ],
            title=f"{selected_sector} — Revenue vs ROE",
        )

    fig.update_layout(
        height=550,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

else:

    st.info(
        "Revenue/ROE data is not available for enough companies "
        "to display the bubble chart."
    )

# ============================================================
# SECTOR MEDIAN METRICS
# ============================================================

st.subheader("📋 Sector Median Metrics")

metric_map = {
    "ROE (%)": "return_on_equity_pct",
    "ROCE (%)": "return_on_capital_employed_pct",
    "Net Profit Margin (%)": "net_profit_margin_pct",
    "Operating Margin (%)": "operating_profit_margin_pct",
    "Debt / Equity": "debt_to_equity",
    "Interest Coverage": "interest_coverage",
    "Revenue CAGR 5Y (%)": "revenue_cagr_5yr",
    "PAT CAGR 5Y (%)": "pat_cagr_5yr",
}

median_rows = []

for label, column in metric_map.items():

    if column in sector_companies.columns:

        values = pd.to_numeric(
            sector_companies[column],
            errors="coerce",
        )

        median_value = values.median()

        median_rows.append(
            {
                "Metric": label,
                "Sector Median": (
                    round(median_value, 2)
                    if pd.notna(median_value)
                    else None
                ),
            }
        )

median_df = pd.DataFrame(median_rows)

if not median_df.empty:
    st.dataframe(
        median_df,
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# COMPANY LIST
# ============================================================

st.subheader("🏢 Companies in this Sector")

display_columns = [
    col
    for col in [
        "company_id",
        "company_name",
        "sector",
        "sub_sector",
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "composite_quality_score",
    ]
    if col in sector_companies.columns
]

display_df = sector_companies[display_columns].copy()

rename_map = {
    "company_id": "Ticker",
    "company_name": "Company",
    "sector": "Sector",
    "sub_sector": "Sub Sector",
    "return_on_equity_pct": "ROE %",
    "debt_to_equity": "D/E",
    "revenue_cagr_5yr": "Revenue CAGR 5Y %",
    "pat_cagr_5yr": "PAT CAGR 5Y %",
    "composite_quality_score": "Quality Score",
}

display_df = display_df.rename(columns=rename_map)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)

# ============================================================
# DATA COVERAGE
# ============================================================

st.caption(
    f"Showing {len(display_df)} companies in the {selected_sector} sector."
)