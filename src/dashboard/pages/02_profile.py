import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_pros_cons,
    resolve_company_id,
)


st.set_page_config(
    page_title="Company Profile | Nifty 100 Analytics",
    page_icon="🏢",
    layout="wide",
)


# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------
st.title("🏢 Company Profile")
st.caption("Explore financial performance, profitability, strengths and risks.")


# ---------------------------------------------------------
# LOAD COMPANIES
# ---------------------------------------------------------
companies = get_companies()

if companies.empty:
    st.error("No company data found.")
    st.stop()


companies = companies.copy()

companies["display_name"] = (
    companies["company_name"].fillna("").astype(str)
    + " ("
    + companies["company_id"].fillna("").astype(str)
    + ")"
)

companies = companies.sort_values("company_name")


# ---------------------------------------------------------
# COMPANY SEARCH
# ---------------------------------------------------------
search_options = companies["display_name"].tolist()

selected_display = st.selectbox(
    "🔎 Search company",
    search_options,
    index=0,
)

selected_row = companies[
    companies["display_name"] == selected_display
].iloc[0]

company_id = selected_row["company_id"]


# ---------------------------------------------------------
# COMPANY INFORMATION
# ---------------------------------------------------------
ratios = get_ratios(company_id)
pl = get_pl(company_id)

if ratios.empty:
    st.warning(
        f"Financial data is not available for {company_id}."
    )
    st.stop()


latest_year = int(ratios["year"].max())

latest_ratio = ratios[
    ratios["year"] == latest_year
].iloc[0]


# ---------------------------------------------------------
# COMPANY CARD
# ---------------------------------------------------------
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 🏢 Company")
    st.write(selected_row.get("company_name", "N/A"))

with col2:
    st.markdown("### 📊 Sector")
    st.write(selected_row.get("broad_sector", "N/A"))

with col3:
    st.markdown("### 🏷️ NSE Symbol")
    st.write(company_id)

with col4:
    st.markdown("### 📅 Latest Year")
    st.write(latest_year)


# ---------------------------------------------------------
# KPI HELPER
# ---------------------------------------------------------
def safe_value(row, column):
    if column not in row.index:
        return None

    value = row[column]

    if pd.isna(value):
        return None

    return value


def format_number(value, decimals=2):
    if value is None or pd.isna(value):
        return "N/A"

    return f"{value:,.{decimals}f}"


def format_percent(value):
    if value is None or pd.isna(value):
        return "N/A"

    return f"{value:.2f}%"


# ---------------------------------------------------------
# KPI TILES
# ---------------------------------------------------------
st.subheader("📌 Key Financial Metrics")

k1, k2, k3, k4, k5, k6 = st.columns(6)

roe = safe_value(latest_ratio, "return_on_equity_pct")
roce = safe_value(latest_ratio, "return_on_capital_employed_pct")
de = safe_value(latest_ratio, "debt_to_equity")
npm = safe_value(latest_ratio, "net_profit_margin_pct")
fcf = safe_value(latest_ratio, "free_cash_flow_cr")
score = safe_value(latest_ratio, "composite_quality_score")

with k1:
    st.metric("ROE", format_percent(roe))

with k2:
    st.metric("ROCE", format_percent(roce))

with k3:
    st.metric("Debt / Equity", format_number(de))

with k4:
    st.metric("Net Profit Margin", format_percent(npm))

with k5:
    st.metric("Free Cash Flow", format_number(fcf))

with k6:
    st.metric("Quality Score", format_number(score))


# ---------------------------------------------------------
# ABOUT
# ---------------------------------------------------------
st.subheader("ℹ️ About the Company")

about_text = (
    selected_row.get("company_name", "This company")
    + " is part of the "
    + str(selected_row.get("broad_sector", "N/A"))
    + " sector."
)

st.info(about_text)


# ---------------------------------------------------------
# FINANCIAL PERFORMANCE
# ---------------------------------------------------------
st.subheader("📈 10-Year Revenue & Net Profit")

if pl.empty:
    st.info("Profit & Loss data is not available.")
else:
    chart_df = pl.copy()

    chart_df["year"] = pd.to_numeric(
        chart_df["year"],
        errors="coerce"
    )

    chart_df["sales"] = pd.to_numeric(
        chart_df["sales"],
        errors="coerce"
    )

    chart_df["net_profit"] = pd.to_numeric(
        chart_df["net_profit"],
        errors="coerce"
    )

    chart_df = chart_df.dropna(
        subset=["year"]
    ).sort_values("year")

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=chart_df["year"],
            y=chart_df["sales"],
            name="Revenue / Sales",
        )
    )

    fig.add_trace(
        go.Bar(
            x=chart_df["year"],
            y=chart_df["net_profit"],
            name="Net Profit",
        )
    )

    fig.update_layout(
        barmode="group",
        xaxis_title="Year",
        yaxis_title="Amount",
        height=450,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ---------------------------------------------------------
# ROE / ROCE TREND
# ---------------------------------------------------------
st.subheader("📊 ROE & ROCE Trend")

trend_df = ratios.copy()

trend_df["year"] = pd.to_numeric(
    trend_df["year"],
    errors="coerce"
)

trend_df = trend_df.sort_values("year")

fig2 = go.Figure()

if "return_on_equity_pct" in trend_df.columns:
    fig2.add_trace(
        go.Scatter(
            x=trend_df["year"],
            y=trend_df["return_on_equity_pct"],
            mode="lines+markers",
            name="ROE",
        )
    )

if "return_on_capital_employed_pct" in trend_df.columns:
    fig2.add_trace(
        go.Scatter(
            x=trend_df["year"],
            y=trend_df["return_on_capital_employed_pct"],
            mode="lines+markers",
            name="ROCE",
        )
    )

fig2.update_layout(
    xaxis_title="Year",
    yaxis_title="Percentage",
    height=420,
    margin=dict(l=20, r=20, t=50, b=20),
)

st.plotly_chart(
    fig2,
    use_container_width=True,
)


# ---------------------------------------------------------
# PROS & CONS
# ---------------------------------------------------------
st.subheader("⚖️ Pros & Cons")

pros_cons = get_pros_cons(company_id)

if pros_cons.empty:
    st.info("Pros and cons information is not available.")
else:
    pros = pros_cons[
        pros_cons["item_type"]
        .astype(str)
        .str.lower()
        .isin(["pro", "pros", "positive"])
    ]

    cons = pros_cons[
        pros_cons["item_type"]
        .astype(str)
        .str.lower()
        .isin(["con", "cons", "negative"])
    ]

    pcol, ccol = st.columns(2)

    with pcol:
        st.markdown("### ✅ Strengths")

        if pros.empty:
            st.write("N/A")
        else:
            for _, row in pros.iterrows():
                st.success(
                    str(row.get("description", "N/A"))
                )

    with ccol:
        st.markdown("### ⚠️ Risks / Concerns")

        if cons.empty:
            st.write("N/A")
        else:
            for _, row in cons.iterrows():
                st.warning(
                    str(row.get("description", "N/A"))
                )


# ---------------------------------------------------------
# DATA COVERAGE
# ---------------------------------------------------------
st.subheader("🗂️ Data Coverage")

coverage_cols = st.columns(3)

with coverage_cols[0]:
    st.metric(
        "Available Ratio Years",
        len(ratios),
    )

with coverage_cols[1]:
    st.metric(
        "Available P&L Years",
        len(pl),
    )

with coverage_cols[2]:
    st.metric(
        "Data Range",
        (
            f"{int(ratios['year'].min())}–"
            f"{int(ratios['year'].max())}"
            if not ratios.empty
            else "N/A"
        ),
    )

st.caption(
    "N/A means the underlying dataset does not contain a usable value."
)