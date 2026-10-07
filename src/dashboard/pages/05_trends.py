import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
)


st.set_page_config(
    page_title="Trends | Nifty 100 Analytics",
    page_icon="📈",
    layout="wide",
)


# =========================================================
# HEADER
# =========================================================
st.title("📈 Financial Trends")
st.caption(
    "Analyze long-term financial trends for any Nifty 100 company."
)


# =========================================================
# LOAD COMPANIES
# =========================================================
companies = get_companies()

if companies.empty:
    st.error("Company data is not available.")
    st.stop()


companies = companies.copy()

companies["display_name"] = (
    companies["company_name"].fillna("").astype(str)
    + " ("
    + companies["company_id"].fillna("").astype(str)
    + ")"
)

companies = companies.sort_values("company_name")


# =========================================================
# COMPANY SEARCH
# =========================================================
selected_display = st.selectbox(
    "🔎 Select Company",
    companies["display_name"].tolist(),
)


selected_row = companies[
    companies["display_name"] == selected_display
].iloc[0]


company_id = str(
    selected_row["company_id"]
)


# =========================================================
# LOAD RATIOS
# =========================================================
ratios = get_ratios(company_id)

if ratios.empty:
    st.warning(
        f"No financial ratio data is available for {company_id}."
    )
    st.stop()


ratios = ratios.copy()

ratios["year"] = pd.to_numeric(
    ratios["year"],
    errors="coerce",
)

ratios = ratios.dropna(
    subset=["year"]
).sort_values("year")


# =========================================================
# AVAILABLE METRICS
# =========================================================
metric_map = {
    "ROE": "return_on_equity_pct",
    "ROCE": "return_on_capital_employed_pct",
    "Net Profit Margin": "net_profit_margin_pct",
    "Operating Profit Margin": "operating_profit_margin_pct",
    "Debt / Equity": "debt_to_equity",
    "Interest Coverage": "interest_coverage",
    "Revenue CAGR 5Y": "revenue_cagr_5yr",
    "PAT CAGR 5Y": "pat_cagr_5yr",
    "EPS CAGR 5Y": "eps_cagr_5yr",
    "Free Cash Flow": "free_cash_flow_cr",
    "Net Debt": "net_debt_cr",
    "Asset Turnover": "asset_turnover",
}


available_metrics = [
    label
    for label, column in metric_map.items()
    if column in ratios.columns
]


if not available_metrics:
    st.warning(
        "No supported financial metrics are available."
    )
    st.stop()


# =========================================================
# METRIC SELECTION
# =========================================================
selected_metrics = st.multiselect(
    "📊 Select up to 3 metrics",
    available_metrics,
    default=available_metrics[:2],
    max_selections=3,
)


if not selected_metrics:
    st.info(
        "Select at least one metric to display the trend."
    )
    st.stop()


# =========================================================
# PREPARE TREND DATA
# =========================================================
trend_df = ratios[
    ["year"]
    + [
        metric_map[m]
        for m in selected_metrics
    ]
].copy()


for metric in selected_metrics:

    column = metric_map[metric]

    trend_df[column] = pd.to_numeric(
        trend_df[column],
        errors="coerce",
    )


# =========================================================
# 10-YEAR LIMIT
# =========================================================
trend_df = trend_df.tail(10).copy()


# =========================================================
# TREND CHART
# =========================================================
st.subheader("📈 10-Year Trend")


fig = go.Figure()


for metric in selected_metrics:

    column = metric_map[metric]

    fig.add_trace(
        go.Scatter(
            x=trend_df["year"],
            y=trend_df[column],
            mode="lines+markers",
            name=metric,
            connectgaps=False,
        )
    )


fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Value",
    height=500,
    hovermode="x unified",
    margin=dict(
        l=20,
        r=20,
        t=50,
        b=20,
    ),
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


# =========================================================
# YOY CHANGE TABLE
# =========================================================
st.subheader("📊 Year-over-Year Change")


yoy_df = trend_df.copy()


for metric in selected_metrics:

    column = metric_map[metric]

    yoy_column = f"{metric} YoY %"

    yoy_df[yoy_column] = (
        yoy_df[column]
        .pct_change()
        .replace(
            [float("inf"), -float("inf")],
            pd.NA,
        )
        * 100
    )


# ---------------------------------------------------------
# BUILD DISPLAY TABLE
# ---------------------------------------------------------
display_df = pd.DataFrame()

display_df["Year"] = yoy_df["year"].astype(int)


for metric in selected_metrics:

    column = metric_map[metric]

    display_df[metric] = yoy_df[column].round(2)

    display_df[
        f"{metric} YoY %"
    ] = yoy_df[
        f"{metric} YoY %"
    ].round(2)


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# LATEST VALUES
# =========================================================
st.subheader("📌 Latest Available Values")


latest = trend_df.iloc[-1]


metric_columns = st.columns(
    len(selected_metrics)
)


for index, metric in enumerate(
    selected_metrics
):

    column = metric_map[metric]

    value = latest[column]

    if pd.isna(value):
        formatted = "N/A"
    else:
        formatted = f"{value:,.2f}"

    with metric_columns[index]:
        st.metric(
            metric,
            formatted,
        )


# =========================================================
# DATA COVERAGE
# =========================================================
st.subheader("🗂️ Data Coverage")


coverage_col1, coverage_col2, coverage_col3 = st.columns(3)


with coverage_col1:
    st.metric(
        "Years Available",
        len(ratios),
    )


with coverage_col2:
    st.metric(
        "First Year",
        int(ratios["year"].min()),
    )


with coverage_col3:
    st.metric(
        "Latest Year",
        int(ratios["year"].max()),
    )


if len(ratios) < 10:
    st.info(
        f"Only {len(ratios)} years of data are available "
        f"for {company_id}. The chart displays all available years."
    )


st.caption(
    "YoY percentages are calculated only where consecutive "
    "non-missing observations are available."
)