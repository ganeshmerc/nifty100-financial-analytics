import streamlit as st
import pandas as pd

from src.dashboard.utils.db import (
    get_companies,
    get_reports,
)


st.set_page_config(
    page_title="Annual Reports | Nifty 100 Analytics",
    page_icon="📄",
    layout="wide",
)


# =========================================================
# HEADER
# =========================================================
st.title("📄 Annual Reports")
st.caption(
    "Access available annual reports and company documents."
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
    companies["company_name"]
    .fillna("")
    .astype(str)
    + " ("
    + companies["company_id"]
    .fillna("")
    .astype(str)
    + ")"
)

companies = companies.sort_values("company_name")


# =========================================================
# COMPANY SELECTOR
# =========================================================
selected_display = st.selectbox(
    "🔎 Select Company",
    companies["display_name"].tolist(),
)

selected_row = companies[
    companies["display_name"] == selected_display
].iloc[0]

company_id = str(selected_row["company_id"])

company_name = str(
    selected_row.get(
        "company_name",
        company_id,
    )
)


# =========================================================
# COMPANY HEADER
# =========================================================
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Company",
        company_name,
    )

with col2:
    st.metric(
        "Ticker",
        company_id,
    )

with col3:
    sector = selected_row.get(
        "broad_sector",
        "N/A",
    )

    if pd.isna(sector) or str(sector).strip() == "":
        sector = "N/A"

    st.metric(
        "Sector",
        str(sector),
    )


# =========================================================
# LOAD REPORTS
# =========================================================
try:

    reports = get_reports(company_id)

except Exception as exc:

    st.error(
        "Unable to load report information."
    )

    st.caption(
        f"Details: {exc}"
    )

    st.stop()


if reports is None or reports.empty:

    st.error(
        f"🔴 Report unavailable for {company_name}."
    )

    st.info(
        "No annual-report document was found in the available dataset."
    )

    st.stop()


reports = reports.copy()


# =========================================================
# NORMALIZE REPORT COLUMNS
# =========================================================

if "company_id" not in reports.columns:
    reports["company_id"] = company_id


if "document_type" not in reports.columns:
    reports["document_type"] = "Annual Report"


if "document_url" not in reports.columns:
    reports["document_url"] = None


# IMPORTANT:
# The report loader stores the actual report year
# in the report_year column.

if "report_year" not in reports.columns:
    reports["report_year"] = pd.NA


reports["document_url"] = (
    reports["document_url"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# =========================================================
# VALID REPORT URL CHECK
# =========================================================
def valid_url(url):

    if not url:
        return False

    url_lower = str(url).lower().strip()

    return (
        url_lower.startswith("http://")
        or url_lower.startswith("https://")
    )


reports["URL Available"] = (
    reports["document_url"]
    .apply(valid_url)
)


# =========================================================
# REPORT YEAR
# =========================================================
# Use report_year directly from the database.
#
# If report_year is missing, fall back to extracting
# a year from document_type or URL.

reports["Report Year"] = reports["report_year"]


# Convert blank values to NA
reports["Report Year"] = (
    reports["Report Year"]
    .replace(
        [
            "",
            "None",
            "nan",
            "NaN",
            "null",
        ],
        pd.NA,
    )
)


# Try document_type as fallback
missing_year = reports["Report Year"].isna()

if missing_year.any():

    extracted_type_year = (
        reports.loc[
            missing_year,
            "document_type",
        ]
        .astype(str)
        .str.extract(
            r"(20\d{2})",
            expand=False,
        )
    )

    reports.loc[
        missing_year,
        "Report Year",
    ] = extracted_type_year


# Try URL as final fallback
missing_year = reports["Report Year"].isna()

if missing_year.any():

    extracted_url_year = (
        reports.loc[
            missing_year,
            "document_url",
        ]
        .astype(str)
        .str.extract(
            r"(20\d{2})",
            expand=False,
        )
    )

    reports.loc[
        missing_year,
        "Report Year",
    ] = extracted_url_year


# Convert valid years to integer-like strings
def format_year(value):

    if pd.isna(value):
        return pd.NA

    try:
        year = int(float(value))

        if 1900 <= year <= 2100:
            return str(year)

    except Exception:
        pass

    return str(value).strip()


reports["Report Year"] = (
    reports["Report Year"]
    .apply(format_year)
)


# =========================================================
# SORT REPORTS
# =========================================================
# Newest report first.

reports["_sort_year"] = pd.to_numeric(
    reports["Report Year"],
    errors="coerce",
)

reports = reports.sort_values(
    by=["_sort_year", "document_type"],
    ascending=[False, True],
    na_position="last",
).reset_index(drop=True)


# =========================================================
# REPORT SUMMARY
# =========================================================
st.subheader("📊 Report Availability")

r1, r2, r3 = st.columns(3)

with r1:

    st.metric(
        "Documents",
        len(reports),
    )


with r2:

    st.metric(
        "Valid Report Links",
        int(
            reports["URL Available"].sum()
        ),
    )


with r3:

    years = (
        reports["Report Year"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    years = years[
        years != ""
    ].unique()

    st.metric(
        "Years Available",
        len(years),
    )


# =========================================================
# REPORT LIST
# =========================================================
st.subheader("📚 Available Reports")


for _, row in reports.iterrows():

    document_type = str(
        row.get(
            "document_type",
            "Annual Report",
        )
    )

    if (
        document_type.lower()
        in [
            "none",
            "nan",
            "null",
            "",
        ]
    ):
        document_type = "Annual Report"


    report_year = row.get(
        "Report Year",
        pd.NA,
    )


    url = str(
        row.get(
            "document_url",
            "",
        )
    ).strip()


    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------
    if (
        pd.notna(report_year)
        and str(report_year).strip()
        not in ["", "None", "nan", "NaN"]
    ):

        title = (
            f"{document_type} — "
            f"{str(report_year).strip()}"
        )

    else:

        title = document_type


    # -----------------------------------------------------
    # REPORT CARD
    # -----------------------------------------------------
    with st.container():

        left, middle, right = st.columns(
            [2, 2, 1]
        )


        with left:

            st.markdown(
                f"### 📄 {title}"
            )


        with middle:

            if valid_url(url):

                st.markdown(
                    f"[Open BSE Report]({url})"
                )

            else:

                st.error(
                    "🔴 Report unavailable"
                )


        with right:

            if valid_url(url):

                st.link_button(
                    "Open PDF",
                    url,
                )

            else:

                st.write("N/A")


        st.divider()


# =========================================================
# DATA TABLE
# =========================================================
st.subheader("📋 Report Details")


table = reports[
    [
        "company_id",
        "document_type",
        "Report Year",
        "document_url",
        "URL Available",
    ]
].copy()


table = table.rename(
    columns={
        "company_id": "Ticker",
        "document_type": "Document Type",
        "Report Year": "Report Year",
        "document_url": "Report URL",
        "URL Available": "URL Available",
    }
)


# Display missing values cleanly
table["Document Type"] = (
    table["Document Type"]
    .replace(
        [
            "None",
            "nan",
            "NaN",
            "null",
        ],
        pd.NA,
    )
    .fillna("N/A")
)


table["Report Year"] = (
    table["Report Year"]
    .fillna("N/A")
)


table["Report URL"] = (
    table["Report URL"]
    .replace(
        [
            "",
            "None",
            "nan",
            "NaN",
            "null",
        ],
        "N/A",
    )
)


st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# NOTE
# =========================================================
st.info(
    "Report links are displayed from the documents available "
    "in the project database. A missing or invalid URL is "
    "shown as Report unavailable rather than causing an error."
)