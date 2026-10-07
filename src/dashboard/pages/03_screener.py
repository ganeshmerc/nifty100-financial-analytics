import streamlit as st
import pandas as pd

from src.dashboard.utils.db import get_companies, get_latest_ratios


st.set_page_config(
    page_title="Screener | Nifty 100 Analytics",
    page_icon="🔎",
    layout="wide",
)


st.title("🔎 Stock Screener")
st.caption("Filter Nifty 100 companies using fundamental financial metrics.")


# =========================================================
# LOAD DATA
# =========================================================
companies = get_companies()
ratios = get_latest_ratios()

if companies.empty:
    st.error("Company data is not available.")
    st.stop()

if ratios.empty:
    st.error("Financial ratio data is not available.")
    st.stop()


# =========================================================
# PREPARE DATA
# =========================================================
companies = companies.copy()
ratios = ratios.copy()

ratios["company_id"] = ratios["company_id"].astype(str)

# Keep the latest available year for each company
ratios["year"] = pd.to_numeric(
    ratios["year"],
    errors="coerce",
)

ratios = ratios.sort_values("year")

latest = (
    ratios
    .drop_duplicates("company_id", keep="last")
    .copy()
)

df = companies.merge(
    latest,
    on="company_id",
    how="left",
    suffixes=("", "_ratio"),
)


# =========================================================
# NORMALIZE COLUMN NAMES
# =========================================================
column_map = {
    "return_on_equity_pct": "ROE",
    "debt_to_equity": "Debt / Equity",
    "free_cash_flow_cr": "FCF",
    "revenue_cagr_5yr": "Revenue CAGR 5Y",
    "pat_cagr_5yr": "PAT CAGR 5Y",
    "operating_profit_margin_pct": "OPM",
    "interest_coverage": "ICR",
    "composite_quality_score": "Composite Score",
}

for source, target in column_map.items():
    if source in df.columns:
        df[target] = pd.to_numeric(
            df[source],
            errors="coerce",
        )


# =========================================================
# SIDEBAR FILTERS
# =========================================================
st.sidebar.header("🎛️ Screener Filters")


# ---------------------------------------------------------
# PRESETS
# ---------------------------------------------------------
st.sidebar.subheader("Presets")

preset = st.sidebar.selectbox(
    "Choose preset",
    [
        "Custom",
        "Quality Compounder",
        "Value Pick",
        "Growth Accelerator",
        "Dividend Champion",
        "Debt-Free Blue Chip",
        "Turnaround Watch",
    ],
)


# Default values
default_roe = 0.0
default_de = 10.0
default_fcf = -100000.0
default_revenue_cagr = -100.0
default_pat_cagr = -100.0
default_opm = -100.0
default_pe = 100.0
default_pb = 100.0
default_dividend = 0.0
default_icr = 0.0


# =========================================================
# PRESET VALUES
# =========================================================
presets = {
    "Quality Compounder": {
        "roe": 15.0,
        "de": 1.0,
        "fcf": 0.0,
        "revenue_cagr": 10.0,
        "pat_cagr": 10.0,
        "opm": 15.0,
        "pe": 50.0,
        "pb": 10.0,
        "dividend": 0.0,
        "icr": 3.0,
    },
    "Value Pick": {
        "roe": 0.0,
        "de": 3.0,
        "fcf": 0.0,
        "revenue_cagr": -100.0,
        "pat_cagr": -100.0,
        "opm": -100.0,
        "pe": 20.0,
        "pb": 3.0,
        "dividend": 1.0,
        "icr": 0.0,
    },
    "Growth Accelerator": {
        "roe": 12.0,
        "de": 2.0,
        "fcf": 0.0,
        "revenue_cagr": 15.0,
        "pat_cagr": 15.0,
        "opm": 10.0,
        "pe": 100.0,
        "pb": 20.0,
        "dividend": 0.0,
        "icr": 2.0,
    },
    "Dividend Champion": {
        "roe": 10.0,
        "de": 3.0,
        "fcf": 0.0,
        "revenue_cagr": -100.0,
        "pat_cagr": -100.0,
        "opm": -100.0,
        "pe": 100.0,
        "pb": 20.0,
        "dividend": 3.0,
        "icr": 0.0,
    },
    "Debt-Free Blue Chip": {
        "roe": 10.0,
        "de": 0.0,
        "fcf": 0.0,
        "revenue_cagr": -100.0,
        "pat_cagr": -100.0,
        "opm": -100.0,
        "pe": 100.0,
        "pb": 20.0,
        "dividend": 0.0,
        "icr": 0.0,
    },
    "Turnaround Watch": {
        "roe": 0.0,
        "de": 5.0,
        "fcf": -100000.0,
        "revenue_cagr": 0.0,
        "pat_cagr": 0.0,
        "opm": 0.0,
        "pe": 100.0,
        "pb": 20.0,
        "dividend": 0.0,
        "icr": 1.0,
    },
}


if preset in presets:
    values = presets[preset]

    default_roe = values["roe"]
    default_de = values["de"]
    default_fcf = values["fcf"]
    default_revenue_cagr = values["revenue_cagr"]
    default_pat_cagr = values["pat_cagr"]
    default_opm = values["opm"]
    default_pe = values["pe"]
    default_pb = values["pb"]
    default_dividend = values["dividend"]
    default_icr = values["icr"]


# =========================================================
# FILTER SLIDERS
# =========================================================
roe_min = st.sidebar.slider(
    "ROE minimum (%)",
    min_value=0.0,
    max_value=100.0,
    value=float(default_roe),
    step=1.0,
)

de_max = st.sidebar.slider(
    "Debt / Equity maximum",
    min_value=0.0,
    max_value=10.0,
    value=float(default_de),
    step=0.1,
)

fcf_min = st.sidebar.slider(
    "FCF minimum (₹ Cr)",
    min_value=-100000.0,
    max_value=100000.0,
    value=float(default_fcf),
    step=100.0,
)

revenue_cagr_min = st.sidebar.slider(
    "Revenue CAGR 5Y minimum (%)",
    min_value=-100.0,
    max_value=100.0,
    value=float(default_revenue_cagr),
    step=1.0,
)

pat_cagr_min = st.sidebar.slider(
    "PAT CAGR 5Y minimum (%)",
    min_value=-100.0,
    max_value=100.0,
    value=float(default_pat_cagr),
    step=1.0,
)

opm_min = st.sidebar.slider(
    "OPM minimum (%)",
    min_value=-100.0,
    max_value=100.0,
    value=float(default_opm),
    step=1.0,
)

pe_max = st.sidebar.slider(
    "P/E maximum",
    min_value=0.0,
    max_value=200.0,
    value=float(default_pe),
    step=1.0,
)

pb_max = st.sidebar.slider(
    "P/B maximum",
    min_value=0.0,
    max_value=50.0,
    value=float(default_pb),
    step=0.5,
)

dividend_min = st.sidebar.slider(
    "Dividend Yield minimum (%)",
    min_value=0.0,
    max_value=20.0,
    value=float(default_dividend),
    step=0.5,
)

icr_min = st.sidebar.slider(
    "Interest Coverage minimum",
    min_value=0.0,
    max_value=50.0,
    value=float(default_icr),
    step=0.5,
)


# =========================================================
# APPLY FILTERS
# =========================================================
filtered = df.copy()


def apply_min(data, column, value):
    if column in data.columns:
        return data[
            data[column].isna()
            | (data[column] >= value)
        ]
    return data


def apply_max(data, column, value):
    if column in data.columns:
        return data[
            data[column].isna()
            | (data[column] <= value)
        ]
    return data


filtered = apply_min(
    filtered,
    "ROE",
    roe_min,
)

filtered = apply_max(
    filtered,
    "Debt / Equity",
    de_max,
)

filtered = apply_min(
    filtered,
    "FCF",
    fcf_min,
)

filtered = apply_min(
    filtered,
    "Revenue CAGR 5Y",
    revenue_cagr_min,
)

filtered = apply_min(
    filtered,
    "PAT CAGR 5Y",
    pat_cagr_min,
)

filtered = apply_min(
    filtered,
    "OPM",
    opm_min,
)


# P/E and P/B may not exist in financial_ratios.
# Keep these filters harmless when those fields are unavailable.
if "pe_ratio" in filtered.columns:
    filtered = apply_max(
        filtered,
        "pe_ratio",
        pe_max,
    )

if "price_to_earnings" in filtered.columns:
    filtered = apply_max(
        filtered,
        "price_to_earnings",
        pe_max,
    )

if "pb_ratio" in filtered.columns:
    filtered = apply_max(
        filtered,
        "pb_ratio",
        pb_max,
    )

if "price_to_book" in filtered.columns:
    filtered = apply_max(
        filtered,
        "price_to_book",
        pb_max,
    )

if "dividend_yield_pct" in filtered.columns:
    filtered = apply_min(
        filtered,
        "dividend_yield_pct",
        dividend_min,
    )

filtered = apply_min(
    filtered,
    "ICR",
    icr_min,
)


# =========================================================
# RESULT HEADER
# =========================================================
st.markdown("---")

h1, h2, h3 = st.columns(3)

with h1:
    st.metric(
        "Companies Matching",
        len(filtered),
    )

with h2:
    st.metric(
        "Total Companies",
        len(df),
    )

with h3:
    percentage = (
        len(filtered) / len(df) * 100
        if len(df) > 0
        else 0
    )

    st.metric(
        "Match %",
        f"{percentage:.1f}%",
    )


# =========================================================
# RESULT TABLE
# =========================================================
st.subheader("📋 Screener Results")


display_columns = [
    "company_id",
    "company_name",
    "broad_sector",
    "Composite Score",
    "ROE",
    "Debt / Equity",
    "FCF",
    "Revenue CAGR 5Y",
    "PAT CAGR 5Y",
    "OPM",
    "ICR",
]


available_columns = [
    col
    for col in display_columns
    if col in filtered.columns
]

result_table = filtered[available_columns].copy()

if "Composite Score" in result_table.columns:
    result_table = result_table.sort_values(
        "Composite Score",
        ascending=False,
        na_position="last",
    )


# Round numeric columns
numeric_columns = result_table.select_dtypes(
    include="number"
).columns

result_table[numeric_columns] = result_table[
    numeric_columns
].round(2)


if result_table.empty:
    st.warning(
        "No companies match the selected filters."
    )
else:
    st.dataframe(
        result_table,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# CSV EXPORT
# =========================================================
st.subheader("📥 Export")

csv_data = result_table.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="⬇️ Download Screener Results CSV",
    data=csv_data,
    file_name="screener_results.csv",
    mime="text/csv",
)


# =========================================================
# ACTIVE FILTER SUMMARY
# =========================================================
with st.expander("🔧 Active Filters"):
    filter_summary = pd.DataFrame(
        {
            "Filter": [
                "ROE minimum",
                "Debt / Equity maximum",
                "FCF minimum",
                "Revenue CAGR 5Y minimum",
                "PAT CAGR 5Y minimum",
                "OPM minimum",
                "P/E maximum",
                "P/B maximum",
                "Dividend Yield minimum",
                "ICR minimum",
            ],
            "Value": [
                roe_min,
                de_max,
                fcf_min,
                revenue_cagr_min,
                pat_cagr_min,
                opm_min,
                pe_max,
                pb_max,
                dividend_min,
                icr_min,
            ],
        }
    )

    st.dataframe(
        filter_summary,
        use_container_width=True,
        hide_index=True,
    )


st.caption(
    "Missing financial values are retained so incomplete company records do not cause the dashboard to crash."
)