import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import (
    get_companies,
    get_latest_ratios,
)


st.set_page_config(
    page_title="Capital Allocation | Nifty 100 Analytics",
    page_icon="💰",
    layout="wide",
)


# =========================================================
# HEADER
# =========================================================
st.title("💰 Capital Allocation")
st.caption(
    "Classify Nifty 100 companies by their capital-allocation characteristics."
)


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


companies = companies.copy()
ratios = ratios.copy()


# =========================================================
# PREPARE RATIOS
# =========================================================
ratios["year"] = pd.to_numeric(
    ratios["year"],
    errors="coerce",
)

ratios = ratios.sort_values("year")


latest = (
    ratios
    .drop_duplicates(
        "company_id",
        keep="last",
    )
    .copy()
)


# =========================================================
# MERGE COMPANY DATA
# =========================================================
df = companies.merge(
    latest,
    on="company_id",
    how="left",
)


# =========================================================
# NUMERIC COLUMNS
# =========================================================
numeric_columns = [
    "return_on_equity_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "capex_cr",
    "cash_from_operations_cr",
    "fcf_conversion_rate_pct",
    "dividend_payout_ratio_pct",
    "composite_quality_score",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
]


for column in numeric_columns:

    if column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )


# =========================================================
# CAPITAL ALLOCATION CLASSIFICATION
# =========================================================
def classify_company(row):

    roe = row.get(
        "return_on_equity_pct",
        None,
    )

    debt = row.get(
        "debt_to_equity",
        None,
    )

    fcf = row.get(
        "free_cash_flow_cr",
        None,
    )

    capex = row.get(
        "capex_cr",
        None,
    )

    cfo = row.get(
        "cash_from_operations_cr",
        None,
    )

    payout = row.get(
        "dividend_payout_ratio_pct",
        None,
    )

    quality = row.get(
        "composite_quality_score",
        None,
    )

    growth = row.get(
        "revenue_cagr_5yr",
        None,
    )


    # Convert safely
    values = [
        roe,
        debt,
        fcf,
        capex,
        cfo,
        payout,
        quality,
        growth,
    ]

    values = [
        pd.to_numeric(
            value,
            errors="coerce",
        )
        for value in values
    ]

    (
        roe,
        debt,
        fcf,
        capex,
        cfo,
        payout,
        quality,
        growth,
    ) = values


    # -----------------------------------------------------
    # 1. Cash Generators
    # -----------------------------------------------------
    if (
        pd.notna(fcf)
        and fcf > 0
        and pd.notna(roe)
        and roe >= 15
    ):
        return "Cash Generator"


    # -----------------------------------------------------
    # 2. Growth Investors
    # -----------------------------------------------------
    if (
        pd.notna(growth)
        and growth >= 15
        and pd.notna(capex)
        and capex > 0
    ):
        return "Growth Investor"


    # -----------------------------------------------------
    # 3. Dividend Payers
    # -----------------------------------------------------
    if (
        pd.notna(payout)
        and payout >= 40
    ):
        return "Dividend Payer"


    # -----------------------------------------------------
    # 4. Debt-Funded Growth
    # -----------------------------------------------------
    if (
        pd.notna(debt)
        and debt >= 1.5
        and pd.notna(growth)
        and growth >= 10
    ):
        return "Debt-Funded Growth"


    # -----------------------------------------------------
    # 5. Conservative Compounders
    # -----------------------------------------------------
    if (
        pd.notna(debt)
        and debt <= 0.5
        and pd.notna(roe)
        and roe >= 12
        and pd.notna(growth)
        and growth >= 8
    ):
        return "Conservative Compounder"


    # -----------------------------------------------------
    # 6. Reinvestment Heavy
    # -----------------------------------------------------
    if (
        pd.notna(capex)
        and pd.notna(cfo)
        and cfo > 0
        and capex > cfo * 0.5
    ):
        return "Reinvestment Heavy"


    # -----------------------------------------------------
    # 7. Weak Capital Efficiency
    # -----------------------------------------------------
    if (
        pd.notna(roe)
        and roe < 8
    ):
        return "Weak Capital Efficiency"


    # -----------------------------------------------------
    # 8. Balanced Allocation
    # -----------------------------------------------------
    return "Balanced Allocation"


df["Capital Pattern"] = df.apply(
    classify_company,
    axis=1,
)


# =========================================================
# PATTERN ORDER
# =========================================================
pattern_order = [
    "Cash Generator",
    "Growth Investor",
    "Dividend Payer",
    "Debt-Funded Growth",
    "Conservative Compounder",
    "Reinvestment Heavy",
    "Weak Capital Efficiency",
    "Balanced Allocation",
]


# =========================================================
# PATTERN COUNTS
# =========================================================
pattern_counts = (
    df["Capital Pattern"]
    .value_counts()
    .reindex(
        pattern_order,
        fill_value=0,
    )
    .reset_index()
)


pattern_counts.columns = [
    "Capital Pattern",
    "Companies",
]


# =========================================================
# OVERVIEW
# =========================================================
st.subheader("📊 Allocation Pattern Overview")


k1, k2, k3, k4 = st.columns(4)


with k1:
    st.metric(
        "Total Companies",
        len(df),
    )


with k2:
    st.metric(
        "Patterns",
        df["Capital Pattern"].nunique(),
    )


with k3:

    largest_pattern = (
        pattern_counts
        .sort_values(
            "Companies",
            ascending=False,
        )
        .iloc[0]
    )

    st.metric(
        "Largest Pattern",
        largest_pattern["Capital Pattern"],
    )


with k4:

    st.metric(
        "Largest Group Size",
        int(largest_pattern["Companies"]),
    )


# =========================================================
# TREEMAP
# =========================================================
st.subheader("🗺️ Capital Allocation Treemap")


treemap_df = df[
    [
        "Capital Pattern",
        "company_id",
        "company_name",
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
    ]
].copy()


treemap_df["Company"] = (
    treemap_df["company_name"]
    .fillna(
        treemap_df["company_id"]
    )
)


# Treemap requires a positive value.
treemap_df["Size"] = 1


fig = px.treemap(
    treemap_df,
    path=[
        "Capital Pattern",
        "Company",
    ],
    values="Size",
    color="return_on_equity_pct",
    hover_data={
        "company_id": True,
        "return_on_equity_pct": ":.2f",
        "debt_to_equity": ":.2f",
        "free_cash_flow_cr": ":.2f",
        "Size": False,
    },
)


fig.update_layout(
    height=700,
    margin=dict(
        l=10,
        r=10,
        t=30,
        b=10,
    ),
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


# =========================================================
# PATTERN COUNTS TABLE
# =========================================================
st.subheader("📋 Pattern Distribution")


distribution = pattern_counts.copy()


distribution["Percentage"] = (
    distribution["Companies"]
    / len(df)
    * 100
)


distribution["Percentage"] = (
    distribution["Percentage"]
    .round(1)
)


st.dataframe(
    distribution,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# SELECT PATTERN
# =========================================================
st.subheader("🔎 Explore a Capital Pattern")


selected_pattern = st.selectbox(
    "Select pattern",
    pattern_order,
)


pattern_df = df[
    df["Capital Pattern"]
    == selected_pattern
].copy()


st.write(
    f"**{len(pattern_df)} companies** classified as "
    f"**{selected_pattern}**."
)


# =========================================================
# COMPANY LIST
# =========================================================
display_columns = [
    "company_id",
    "company_name",
    "broad_sector",
    "return_on_equity_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "capex_cr",
    "cash_from_operations_cr",
    "dividend_payout_ratio_pct",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "composite_quality_score",
]


available_columns = [
    column
    for column in display_columns
    if column in pattern_df.columns
]


company_table = pattern_df[
    available_columns
].copy()


rename_map = {
    "company_id": "Ticker",
    "company_name": "Company",
    "broad_sector": "Sector",
    "return_on_equity_pct": "ROE",
    "debt_to_equity": "Debt / Equity",
    "free_cash_flow_cr": "FCF",
    "capex_cr": "Capex",
    "cash_from_operations_cr": "CFO",
    "dividend_payout_ratio_pct": "Dividend Payout %",
    "revenue_cagr_5yr": "Revenue CAGR 5Y",
    "pat_cagr_5yr": "PAT CAGR 5Y",
    "composite_quality_score": "Quality Score",
}


company_table = company_table.rename(
    columns=rename_map
)


numeric_display_columns = (
    company_table
    .select_dtypes(
        include="number"
    )
    .columns
)


company_table[numeric_display_columns] = (
    company_table[numeric_display_columns]
    .round(2)
)


st.dataframe(
    company_table,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# DATA NOTE
# =========================================================
st.caption(
    "Capital-allocation patterns are analytical classifications "
    "based on the available financial-ratio data. They are not "
    "investment recommendations."
)