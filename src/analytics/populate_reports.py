from pathlib import Path
import sqlite3
import re
import time
import html
import requests
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"


# ============================================================
# BSE CONFIG
# ============================================================

BSE_SEARCH_URL = (
    "https://api.bseindia.com/"
    "BseIndiaAPI/api/PeerSmartSearch/w"
)

BSE_ANNOUNCEMENT_URL = (
    "https://api.bseindia.com/"
    "BseIndiaAPI/api/AnnSubCategoryGetData/w"
)

BSE_ATTACHMENT_BASE = (
    "https://www.bseindia.com/"
    "xml-data/corpfiling/AttachHis/"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/142.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bseindia.com/corporates/ann.html",
    "Accept": "application/json, text/plain, */*",
}


# ============================================================
# HELPERS
# ============================================================

def normalize_name(value):
    """Normalize company names for matching."""

    if value is None:
        return ""

    value = str(value).upper()

    # Common company suffixes
    value = re.sub(
        r"\b(LIMITED|LTD|LTD\.|PRIVATE|PVT|PUBLIC|PLC)\b",
        " ",
        value,
    )

    # Remove punctuation
    value = re.sub(r"[^A-Z0-9]+", " ", value)

    # Normalize spaces
    value = re.sub(r"\s+", " ", value).strip()

    return value


def get_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


# ============================================================
# BSE SCRIP CODE
# ============================================================

def get_bse_scrip_code(session, company_name, ticker=None):
    """
    Resolve BSE scrip code using company name.

    We deliberately do NOT take the first result because
    tickers such as ABB can match multiple companies.
    """

    search_terms = []

    if company_name:
        search_terms.append(company_name)

    if ticker:
        search_terms.append(ticker)

    project_name = normalize_name(company_name)

    for search_text in search_terms:

        try:
            response = session.get(
                BSE_SEARCH_URL,
                params={
                    "Type": "SS",
                    "text": search_text,
                },
                timeout=(10, 30),
            )

            if response.status_code != 200:
                continue

            text = html.unescape(response.text)

            # Extract:
            # liclick('500488','ABBOTT INDIA LTD')
            matches = re.findall(
                r"liclick\('(\d+)','([^']+)'\)",
                text,
                flags=re.IGNORECASE,
            )

            if not matches:
                continue

            # First try exact normalized company-name match
            for code, bse_name in matches:

                if normalize_name(bse_name) == project_name:
                    return code, bse_name

            # Then try containment
            for code, bse_name in matches:

                bse_norm = normalize_name(bse_name)

                if (
                    project_name in bse_norm
                    or bse_norm in project_name
                ):
                    return code, bse_name

        except requests.RequestException:
            continue

    return None, None


# ============================================================
# ANNUAL REPORT DETECTION
# ============================================================

def is_annual_report(subject):
    """Check whether an announcement appears to be an annual report."""

    if not subject:
        return False

    text = str(subject).lower()

    keywords = [
        "annual report",
        "reg. 34 (1) annual report",
        "reg 34 (1) annual report",
        "integrated annual report",
        "annual report.",
        "annual report -",
        "annual report 20",
    ]

    return any(keyword in text for keyword in keywords)


def extract_report_year(row):
    """
    Try to determine report year from announcement text/date.
    """

    subject = str(row.get("NEWSSUB") or "")
    date_value = str(row.get("NEWS_DT") or "")

    text = f"{subject} {date_value}"

    # Prefer explicit year such as 2025
    years = re.findall(r"\b20(2[0-9])\b", text)

    if years:
        return int("20" + years[-1])

    # Filing date fallback
    try:
        date = pd.to_datetime(date_value)

        # Annual report filed during FY ending previous March
        return int(date.year)

    except Exception:
        return None


# ============================================================
# FIND ANNUAL REPORTS
# ============================================================

def find_annual_reports(session, bse_code):

    all_reports = []

    # Search several windows.
    # Smaller windows reduce BSE API timeout risk.
    windows = [
        ("2025-05-01", "2025-10-31"),
        ("2024-05-01", "2024-10-31"),
        ("2023-05-01", "2023-10-31"),
    ]

    for start_date, end_date in windows:

        params = {
            "pageno": "1",
            "strCat": "-1",
            "subcategory": "-1",
            "strPrevDate": start_date.replace("-", ""),
            "strToDate": end_date.replace("-", ""),
            "strSearch": "p",
            "strscrip": str(bse_code),
            "strType": "C",
        }

        try:

            response = session.get(
                BSE_ANNOUNCEMENT_URL,
                params=params,
                timeout=(10, 45),
            )

            if response.status_code != 200:
                continue

            try:
                data = response.json()
            except ValueError:
                continue

            rows = data.get("Table", [])

            for row in rows:

                subject = row.get("NEWSSUB", "")

                if not is_annual_report(subject):
                    continue

                attachment = row.get("ATTACHMENTNAME")

                if not attachment:
                    continue

                report_year = extract_report_year(row)

                pdf_url = BSE_ATTACHMENT_BASE + str(
                    attachment
                ).strip()

                all_reports.append(
                    {
                        "report_year": report_year,
                        "report_date": row.get("NEWS_DT"),
                        "document_type": "Annual Report",
                        "document_url": pdf_url,
                        "subject": subject,
                        "attachment": attachment,
                    }
                )

        except requests.RequestException:
            continue

        time.sleep(0.3)

    # Remove duplicate URLs
    unique = {}

    for report in all_reports:
        unique[report["document_url"]] = report

    return list(unique.values())


# ============================================================
# VALIDATE PDF
# ============================================================

def validate_pdf(session, url):

    try:

        response = session.get(
            url,
            timeout=(10, 30),
            stream=True,
        )

        if response.status_code != 200:
            return False

        content_type = (
            response.headers.get("Content-Type") or ""
        ).lower()

        first_bytes = next(
            response.iter_content(chunk_size=5),
            b"",
        )

        return (
            b"%PDF-" in first_bytes
            or "application/pdf" in content_type
        )

    except requests.RequestException:
        return False


# ============================================================
# DATABASE MIGRATION
# ============================================================

def ensure_report_year_column(connection):

    columns = pd.read_sql_query(
        "PRAGMA table_info(documents)",
        connection,
    )

    names = columns["name"].tolist()

    if "report_year" not in names:

        connection.execute(
            "ALTER TABLE documents "
            "ADD COLUMN report_year INTEGER"
        )

        connection.commit()


# ============================================================
# SAVE REPORT
# ============================================================

def save_report(
    connection,
    company_id,
    report,
):

    # Remove an identical existing row first
    connection.execute(
        """
        DELETE FROM documents
        WHERE company_id = ?
          AND document_url = ?
        """,
        (
            company_id,
            report["document_url"],
        ),
    )

    connection.execute(
        """
        INSERT INTO documents
        (
            company_id,
            document_type,
            document_url,
            report_year
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            company_id,
            report["document_type"],
            report["document_url"],
            report["report_year"],
        ),
    )

    connection.commit()


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("NIFTY 100 BSE ANNUAL REPORT LOADER")
    print("=" * 70)

    print(f"Database: {DB_PATH}")

    if not DB_PATH.exists():

        print("ERROR: Database not found.")
        return

    connection = sqlite3.connect(DB_PATH)

    ensure_report_year_column(connection)

    companies = pd.read_sql_query(
        """
        SELECT
            company_id,
            company_name,
            ticker
        FROM companies
        ORDER BY company_id
        """,
        connection,
    )

    print(f"Companies found: {len(companies)}")
    print()

    session = get_session()

    successful_companies = 0
    reports_saved = 0
    no_bse_code = 0
    no_reports = 0
    invalid_reports = 0

    for index, row in companies.iterrows():

        company_id = row["company_id"]
        company_name = row["company_name"]
        ticker = row["ticker"]

        print(
            f"[{index + 1:02d}/{len(companies)}] "
            f"{company_id} | {company_name}"
        )

        # ----------------------------------------------------
        # Resolve BSE code
        # ----------------------------------------------------

        bse_code, bse_name = get_bse_scrip_code(
            session,
            company_name,
            ticker,
        )

        if not bse_code:

            print("   BSE code: NOT FOUND")
            no_bse_code += 1
            continue

        print(
            f"   BSE: {bse_code} | {bse_name}"
        )

        # ----------------------------------------------------
        # Find reports
        # ----------------------------------------------------

        reports = find_annual_reports(
            session,
            bse_code,
        )

        if not reports:

            print("   Annual reports: NONE FOUND")
            no_reports += 1
            continue

        company_saved = False

        # Newest first
        reports.sort(
            key=lambda x: (
                x["report_year"] or 0,
                x["report_date"] or "",
            ),
            reverse=True,
        )

        # Keep latest 3 reports
        reports = reports[:3]

        for report in reports:

            print(
                f"   Checking {report['report_year']} "
                f"| {report['document_url']}"
            )

            if not validate_pdf(
                session,
                report["document_url"],
            ):

                print("      PDF: INVALID")
                invalid_reports += 1
                continue

            save_report(
                connection,
                company_id,
                report,
            )

            print("      PDF: VALID ✓")

            reports_saved += 1
            company_saved = True

        if company_saved:
            successful_companies += 1

        time.sleep(0.5)

    connection.close()

    print()
    print("=" * 70)
    print("REPORT LOADER COMPLETE")
    print("=" * 70)

    print(f"Companies:              {len(companies)}")
    print(f"Companies with reports: {successful_companies}")
    print(f"Reports saved:          {reports_saved}")
    print(f"BSE codes not found:    {no_bse_code}")
    print(f"No reports found:       {no_reports}")
    print(f"Invalid PDFs:            {invalid_reports}")
    print()
    print(f"Database updated: {DB_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()