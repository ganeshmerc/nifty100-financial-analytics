import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.utils.db import (
    get_companies,
    get_peer_group_names,
    get_peers,
    get_ratios,
)


st.set_page_config(
    page_title="Peer Comparison | Nifty 100 Analytics",
    page_icon="👥",
    layout="wide",
)


st.title("👥 Peer Comparison")
st.caption("Compare companies against their industry peer group.")


# =========================================================
# LOAD DATA
# =========================================================
companies = get_companies()
peer_groups = get_peer_group_names()


if companies.empty:
    st.error("Company data is not available.")
    st.stop()

if not peer_groups:
    st.error("Peer group data is not available.")
    st.stop()


# =========================================================
# PEER GROUP SELECTOR
# =========================================================
selected_group = st.selectbox(
    "🏷️ Select Peer Group",
    peer_groups,
)


peers = get_peers(selected_group)


if peers.empty:
    st.warning(
        f"No companies found for the {selected_group} peer group."
    )
    st.stop()


peers = peers.copy()


# =========================================================
# COMPANY SELECTOR
# =========================================================
peer_display = []

for _, row in peers.iterrows():
    company_id = str(row.get("company_id", ""))

    company_name = row.get(
        "company_name",
        company_id,
    )

    peer_display.append(
        f"{company_name} ({company_id})"
    )


selected_display = st.selectbox(
    "🔎 Select Company",
    peer_display,
)


selected_index = peer_display.index(
    selected_display
)

selected_company = peers.iloc[selected_index]

selected_company_id = str(
    selected_company["company_id"]
)


# =========================================================
# GROUP INFORMATION
# =========================================================
st.markdown("---")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "Peer Group",
        selected_group,
    )

with c2:
    st.metric(
        "Companies",
        len(peers),
    )

with c3:
    benchmark_count = int(
        peers["is_benchmark"]
        .fillna(False)
        .astype(bool)
        .sum()
    )

    st.metric(
        "Benchmark Companies",
        benchmark_count,
    )


# =========================================================
# LOAD RATIOS FOR ALL PEERS
# =========================================================
peer_ratio_frames = []

for company_id in peers["company_id"].dropna().unique():

    company_ratios = get_ratios(
        str(company_id)
    )

    if company_ratios.empty:
        continue

    company_ratios = company_ratios.copy()

    company_ratios["company_id"] = str(
        company_id
    )

    peer_ratio_frames.append(
        company_ratios
    )


if not peer_ratio_frames:
    st.warning(
        "Financial ratio data is not available for this peer group."
    )
    st.stop()


all_ratios = pd.concat(
    peer_ratio_frames,
    ignore_index=True,
)


# =========================================================
# LATEST YEAR PER COMPANY
# =========================================================
all_ratios["year"] = pd.to_numeric(
    all_ratios["year"],
    errors="coerce",
)


all_ratios = all_ratios.sort_values(
    ["company_id", "year"]
)


latest_ratios = (
    all_ratios
    .drop_duplicates(
        "company_id",
        keep="last",
    )
    .copy()
)


# =========================================================
# COMPANY + RATIO DATA
# =========================================================
comparison = peers.merge(
    latest_ratios,
    on="company_id",
    how="left",
)


# =========================================================
# METRIC DEFINITIONS
# =========================================================
metric_columns = {
    "ROE": "return_on_equity_pct",
    "ROCE": "return_on_capital_employed_pct",
    "Net Profit Margin": "net_profit_margin_pct",
    "Operating Margin": "operating_profit_margin_pct",
    "Revenue CAGR 5Y": "revenue_cagr_5yr",
    "PAT CAGR 5Y": "pat_cagr_5yr",
    "Debt / Equity": "debt_to_equity",
    "Interest Coverage": "interest_coverage",
}


# =========================================================
# SELECTED COMPANY DATA
# =========================================================
selected_data = comparison[
    comparison["company_id"].astype(str)
    == selected_company_id
]


if selected_data.empty:
    st.warning(
        "Financial data for the selected company is unavailable."
    )
else:

    selected_data = selected_data.iloc[0]

    # -----------------------------------------------------
    # RADAR CHART
    # -----------------------------------------------------
    st.subheader("📡 Company vs Peer Group")

    radar_labels = []
    company_values = []
    group_values = []

    for label, column in metric_columns.items():

        if column not in comparison.columns:
            continue

        values = pd.to_numeric(
            comparison[column],
            errors="coerce",
        )

        company_value = pd.to_numeric(
            pd.Series(
                [selected_data.get(column)]
            ),
            errors="coerce",
        ).iloc[0]

        group_average = values.mean()

        if pd.isna(company_value):
            continue

        if pd.isna(group_average):
            continue

        radar_labels.append(label)
        company_values.append(float(company_value))
        group_values.append(float(group_average))


    if radar_labels:

        radar_labels_closed = (
            radar_labels + [radar_labels[0]]
        )

        company_values_closed = (
            company_values
            + [company_values[0]]
        )

        group_values_closed = (
            group_values
            + [group_values[0]]
        )

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=company_values_closed,
                theta=radar_labels_closed,
                fill="toself",
                name=selected_company_id,
            )
        )

        fig.add_trace(
            go.Scatterpolar(
                r=group_values_closed,
                theta=radar_labels_closed,
                fill="toself",
                name="Peer Average",
            )
        )

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                )
            ),
            height=600,
            margin=dict(
                l=30,
                r=30,
                t=50,
                b=30,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    else:
        st.info(
            "Not enough metrics are available to create the radar chart."
        )


# =========================================================
# KPI COMPARISON
# =========================================================
st.subheader("📊 KPI Comparison")

kpi_rows = []

for label, column in metric_columns.items():

    if column not in comparison.columns:
        continue

    values = pd.to_numeric(
        comparison[column],
        errors="coerce",
    )

    selected_value = pd.to_numeric(
        pd.Series(
            comparison.loc[
                comparison["company_id"].astype(str)
                == selected_company_id,
                column,
            ]
        ),
        errors="coerce",
    )

    selected_value = (
        selected_value.iloc[0]
        if not selected_value.empty
        else None
    )

    group_average = values.mean()

    kpi_rows.append(
        {
            "Metric": label,
            "Selected Company": selected_value,
            "Peer Average": group_average,
        }
    )


kpi_table = pd.DataFrame(kpi_rows)


if not kpi_table.empty:

    numeric_cols = [
        "Selected Company",
        "Peer Average",
    ]

    kpi_table[numeric_cols] = (
        kpi_table[numeric_cols]
        .round(2)
    )

    st.dataframe(
        kpi_table,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# ALL PEER COMPANIES
# =========================================================
st.subheader("🏢 Peer Group Companies")


display_columns = [
    "company_id",
    "company_name",
    "is_benchmark",
    "year",
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "debt_to_equity",
    "interest_coverage",
]


available_columns = [
    column
    for column in display_columns
    if column in comparison.columns
]


peer_table = comparison[
    available_columns
].copy()


rename_map = {
    "company_id": "Ticker",
    "company_name": "Company",
    "is_benchmark": "Benchmark",
    "year": "Year",
    "return_on_equity_pct": "ROE",
    "return_on_capital_employed_pct": "ROCE",
    "net_profit_margin_pct": "Net Profit Margin",
    "operating_profit_margin_pct": "Operating Margin",
    "revenue_cagr_5yr": "Revenue CAGR 5Y",
    "pat_cagr_5yr": "PAT CAGR 5Y",
    "debt_to_equity": "Debt / Equity",
    "interest_coverage": "Interest Coverage",
}


peer_table = peer_table.rename(
    columns=rename_map
)


numeric_columns = peer_table.select_dtypes(
    include="number"
).columns


peer_table[numeric_columns] = (
    peer_table[numeric_columns]
    .round(2)
)


st.dataframe(
    peer_table,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# BENCHMARK
# =========================================================
benchmarks = peers[
    peers["is_benchmark"]
    .fillna(False)
    .astype(bool)
]


if not benchmarks.empty:

    st.subheader("🏆 Benchmark")

    for _, benchmark in benchmarks.iterrows():

        st.success(
            f"Benchmark: {benchmark.get('company_name', 'N/A')} "
            f"({benchmark.get('company_id', 'N/A')})"
        )


# =========================================================
# NOTE
# =========================================================
st.info(
    "Peer comparison uses the authoritative peer-group definitions "
    "from data/source/peer_groups.xlsx and the latest available "
    "financial ratios for each company."
)