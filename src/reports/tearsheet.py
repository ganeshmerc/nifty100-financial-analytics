"""
Sprint 5 - Day 33
Company Tearsheet Generator

Creates 2-page PDF tearsheets for companies.

Page 1:
- Company / ticker header
- 6 KPI tiles
- 10-year Revenue and Net Profit chart
- ROE / ROCE trend

Page 2:
- Balance Sheet composition
- Cash Flow waterfall
- Pros
- Cons
- Capital allocation badge
"""

from pathlib import Path
import math
import sqlite3

import pandas as pd
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether,
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"

PROS_CONS_PATH = PROJECT_ROOT / "output" / "pros_cons_generated.csv"
CASHFLOW_INTELLIGENCE_PATH = (
    PROJECT_ROOT / "output" / "cashflow_intelligence.xlsx"
)

OUTPUT_DIR = PROJECT_ROOT / "reports" / "tearsheets"
CHART_DIR = PROJECT_ROOT / "reports" / "_tearsheet_charts"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


def table_exists(conn, table_name):
    result = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name=?
        """,
        (table_name,),
    ).fetchone()

    return result is not None


def read_table(conn, table_name):
    if not table_exists(conn, table_name):
        return pd.DataFrame()

    return pd.read_sql_query(
        f'SELECT * FROM "{table_name}"',
        conn,
    )


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default

        value = str(value).replace(",", "").replace("%", "").strip()

        if value == "":
            return default

        return float(value)

    except Exception:
        return default


def first_existing_column(df, candidates):
    for column in candidates:
        if column in df.columns:
            return column

    return None


def latest_row(df):
    if df.empty or "year" not in df.columns:
        return None

    temp = df.copy()

    temp["_year_num"] = pd.to_numeric(
        temp["year"],
        errors="coerce",
    )

    temp = temp.dropna(subset=["_year_num"])

    if temp.empty:
        return None

    return temp.sort_values("_year_num").iloc[-1]


def format_number(value):
    value = safe_float(value)

    if abs(value) >= 100000:
        return f"{value:,.0f}"

    if abs(value) >= 1000:
        return f"{value:,.0f}"

    return f"{value:,.2f}"


def format_pct(value):
    value = safe_float(value)
    return f"{value:.1f}%"


def clean_text(value):
    if value is None:
        return ""

    if pd.isna(value):
        return ""

    return str(value).strip()


# ============================================================
# CHART 1
# REVENUE + NET PROFIT
# ============================================================

def create_revenue_profit_chart(df, ticker):

    if df.empty or "year" not in df.columns:
        return None

    sales_col = first_existing_column(
        df,
        [
            "sales",
            "revenue",
            "total_revenue",
        ],
    )

    profit_col = first_existing_column(
        df,
        [
            "net_profit",
            "net_profit_cr",
            "profit",
        ],
    )

    if sales_col is None or profit_col is None:
        return None

    temp = df.copy()

    temp["_year_num"] = pd.to_numeric(
        temp["year"],
        errors="coerce",
    )

    temp[sales_col] = pd.to_numeric(
        temp[sales_col],
        errors="coerce",
    )

    temp[profit_col] = pd.to_numeric(
        temp[profit_col],
        errors="coerce",
    )

    temp = temp.dropna(
        subset=["_year_num", sales_col, profit_col]
    )

    if temp.empty:
        return None

    temp = temp.sort_values("_year_num").tail(10)

    fig, ax = plt.subplots(figsize=(7.2, 2.55))

    x = range(len(temp))

    ax.bar(
        [i - 0.18 for i in x],
        temp[sales_col],
        width=0.35,
        label="Revenue",
    )

    ax.bar(
        [i + 0.18 for i in x],
        temp[profit_col],
        width=0.35,
        label="Net Profit",
    )

    ax.set_xticks(list(x))
    ax.set_xticklabels(
        [str(int(y)) for y in temp["_year_num"]],
        rotation=45,
        ha="right",
        fontsize=7,
    )

    ax.set_title(
        f"{ticker} — Revenue & Net Profit",
        fontsize=9,
        fontweight="bold",
    )

    ax.grid(axis="y", alpha=0.2)
    ax.legend(fontsize=7)

    fig.tight_layout()

    path = CHART_DIR / f"{ticker}_revenue_profit.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return path


# ============================================================
# CHART 2
# ROE / ROCE
# ============================================================

def create_roe_roce_chart(df, ticker):

    if df.empty or "year" not in df.columns:
        return None

    roe_col = first_existing_column(
        df,
        [
            "return_on_equity_pct",
            "roe",
            "roe_pct",
        ],
    )

    roce_col = first_existing_column(
        df,
        [
            "return_on_capital_employed_pct",
            "roce",
            "roce_pct",
        ],
    )

    if roe_col is None and roce_col is None:
        return None

    temp = df.copy()

    temp["_year_num"] = pd.to_numeric(
        temp["year"],
        errors="coerce",
    )

    if roe_col:
        temp[roe_col] = pd.to_numeric(
            temp[roe_col],
            errors="coerce",
        )

    if roce_col:
        temp[roce_col] = pd.to_numeric(
            temp[roce_col],
            errors="coerce",
        )

    temp = temp.dropna(subset=["_year_num"])

    temp = temp.sort_values("_year_num").tail(10)

    fig, ax = plt.subplots(figsize=(7.2, 2.35))

    if roe_col:
        ax.plot(
            temp["_year_num"],
            temp[roe_col],
            marker="o",
            linewidth=1.5,
            label="ROE",
        )

    if roce_col:
        ax.plot(
            temp["_year_num"],
            temp[roce_col],
            marker="o",
            linewidth=1.5,
            label="ROCE",
        )

    ax.set_title(
        f"{ticker} — ROE / ROCE Trend",
        fontsize=9,
        fontweight="bold",
    )

    ax.set_ylabel("%", fontsize=8)

    ax.grid(alpha=0.2)
    ax.legend(fontsize=7)

    fig.tight_layout()

    path = CHART_DIR / f"{ticker}_roe_roce.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return path


# ============================================================
# CHART 3
# BALANCE SHEET COMPOSITION
# ============================================================

def create_balance_sheet_chart(df, ticker):

    if df.empty:
        return None

    latest = latest_row(df)

    if latest is None:
        return None

    asset_col = first_existing_column(
        df,
        [
            "total_assets",
            "assets",
        ],
    )

    debt_col = first_existing_column(
        df,
        [
            "total_debt",
            "total_debt_cr",
            "borrowings",
            "debt",
        ],
    )

    equity_col = first_existing_column(
        df,
        [
            "shareholders_equity",
            "total_equity",
            "equity",
            "net_worth",
        ],
    )

    cash_col = first_existing_column(
        df,
        [
            "cash",
            "cash_and_equivalents",
            "cash_balance",
        ],
    )

    if not any(
        [
            asset_col,
            debt_col,
            equity_col,
            cash_col,
        ]
    ):
        return None

    labels = []
    values = []

    candidates = [
        ("Assets", asset_col),
        ("Debt", debt_col),
        ("Equity", equity_col),
        ("Cash", cash_col),
    ]

    for label, column in candidates:

        if column is None:
            continue

        value = safe_float(latest[column])

        labels.append(label)
        values.append(value)

    if not values:
        return None

    fig, ax = plt.subplots(figsize=(7.2, 2.35))

    bottom = 0

    for label, value in zip(labels, values):

        ax.bar(
            ["Latest Year"],
            [value],
            bottom=[bottom],
            label=label,
        )

        bottom += value

    ax.set_title(
        f"{ticker} — Balance Sheet Composition",
        fontsize=9,
        fontweight="bold",
    )

    ax.legend(
        fontsize=7,
        loc="upper right",
    )

    ax.grid(axis="y", alpha=0.2)

    fig.tight_layout()

    path = CHART_DIR / f"{ticker}_balance_sheet.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return path


# ============================================================
# CHART 4
# CASH FLOW WATERFALL
# ============================================================

def create_cashflow_chart(df, ticker):

    if df.empty:
        return None

    latest = latest_row(df)

    if latest is None:
        return None

    cfo_col = first_existing_column(
        df,
        [
            "operating_activity",
            "cash_from_operations_cr",
            "cash_from_operations",
            "cfo",
        ],
    )

    cfi_col = first_existing_column(
        df,
        [
            "investing_activity",
            "cash_from_investing",
            "cfi",
        ],
    )

    cff_col = first_existing_column(
        df,
        [
            "financing_activity",
            "cash_from_financing",
            "cff",
        ],
    )

    if cfo_col is None and cfi_col is None and cff_col is None:
        return None

    labels = []
    values = []

    for label, column in [
        ("CFO", cfo_col),
        ("CFI", cfi_col),
        ("CFF", cff_col),
    ]:

        if column is None:
            continue

        labels.append(label)
        values.append(safe_float(latest[column]))

    if not values:
        return None

    fig, ax = plt.subplots(figsize=(7.2, 2.35))

    x = range(len(values))

    ax.bar(
        x,
        values,
        width=0.55,
    )

    ax.axhline(
        0,
        linewidth=0.8,
    )

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)

    ax.set_title(
        f"{ticker} — Cash Flow Overview",
        fontsize=9,
        fontweight="bold",
    )

    ax.grid(axis="y", alpha=0.2)

    fig.tight_layout()

    path = CHART_DIR / f"{ticker}_cashflow.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return path


# ============================================================
# PROS / CONS
# ============================================================

def get_pros_cons(company_id, pros_cons_df):

    if pros_cons_df.empty:
        return [], []

    temp = pros_cons_df[
        pros_cons_df["company_id"].astype(str)
        == str(company_id)
    ].copy()

    if temp.empty:
        return [], []

    pros = []
    cons = []

    for _, row in temp.iterrows():

        item_type = clean_text(
            row.get("type", "")
        ).lower()

        text = clean_text(
            row.get("text", "")
        )

        confidence = safe_float(
            row.get("confidence_pct", 0)
        )

        if not text:
            continue

        if confidence <= 60:
            continue

        if item_type == "pro":
            pros.append(text)

        elif item_type == "con":
            cons.append(text)

    return pros[:8], cons[:8]


# ============================================================
# KPI DATA
# ============================================================

def get_kpis(company_id, ratios_df, pnl_df):

    ratios = ratios_df[
        ratios_df["company_id"].astype(str)
        == str(company_id)
    ].copy()

    pnl = pnl_df[
        pnl_df["company_id"].astype(str)
        == str(company_id)
    ].copy()

    ratio_latest = latest_row(ratios)
    pnl_latest = latest_row(pnl)

    result = []

    def get_ratio(candidates):

        if ratio_latest is None:
            return 0

        column = first_existing_column(
            ratios,
            candidates,
        )

        if column is None:
            return 0

        return safe_float(
            ratio_latest[column]
        )

    def get_pnl(candidates):

        if pnl_latest is None:
            return 0

        column = first_existing_column(
            pnl,
            candidates,
        )

        if column is None:
            return 0

        return safe_float(
            pnl_latest[column]
        )

    result.append(
        ("Revenue", get_pnl(["sales", "revenue"]))
    )

    result.append(
        ("Net Profit", get_pnl(["net_profit"]))
    )

    result.append(
        ("ROE", get_ratio(
            [
                "return_on_equity_pct",
                "roe",
                "roe_pct",
            ]
        ))
    )

    result.append(
        ("ROCE", get_ratio(
            [
                "return_on_capital_employed_pct",
                "roce",
                "roce_pct",
            ]
        ))
    )

    result.append(
        ("Debt / Equity", get_ratio(
            [
                "debt_to_equity",
            ]
        ))
    )

    result.append(
        ("Interest Coverage", get_ratio(
            [
                "interest_coverage",
            ]
        ))
    )

    return result


# ============================================================
# PDF STYLES
# ============================================================

styles = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "TitleCustom",
    parent=styles["Title"],
    fontSize=18,
    leading=21,
    alignment=TA_LEFT,
    spaceAfter=4,
)

SUBTITLE_STYLE = ParagraphStyle(
    "SubtitleCustom",
    parent=styles["Normal"],
    fontSize=9,
    leading=11,
)

SECTION_STYLE = ParagraphStyle(
    "SectionCustom",
    parent=styles["Heading2"],
    fontSize=10,
    leading=12,
    spaceBefore=3,
    spaceAfter=4,
)

BODY_STYLE = ParagraphStyle(
    "BodyCustom",
    parent=styles["BodyText"],
    fontSize=7.5,
    leading=9.5,
)

SMALL_STYLE = ParagraphStyle(
    "SmallCustom",
    parent=styles["BodyText"],
    fontSize=6.5,
    leading=8,
)

PRO_STYLE = ParagraphStyle(
    "ProCustom",
    parent=BODY_STYLE,
)

CON_STYLE = ParagraphStyle(
    "ConCustom",
    parent=BODY_STYLE,
)


# ============================================================
# KPI TABLE
# ============================================================

def build_kpi_table(kpis):

    cells = []

    for label, value in kpis:

        if label in [
            "ROE",
            "ROCE",
        ]:
            value_text = format_pct(value)

        elif label == "Debt / Equity":
            value_text = f"{safe_float(value):.2f}"

        elif label == "Interest Coverage":
            value_text = f"{safe_float(value):.2f}x"

        else:
            value_text = format_number(value)

        cell = Paragraph(
            f"<b>{label}</b><br/><font size='13'>{value_text}</font>",
            BODY_STYLE,
        )

        cells.append(cell)

    data = [
        cells[:3],
        cells[3:6],
    ]

    table = Table(
        data,
        colWidths=[
            57 * mm,
            57 * mm,
            57 * mm,
        ],
        rowHeights=[
            18 * mm,
            18 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.lightgrey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    return table


# ============================================================
# PROS / CONS TABLE
# ============================================================

def build_pros_cons_table(pros, cons):

    max_rows = max(
        len(pros),
        len(cons),
        1,
    )

    data = [
        [
            Paragraph("<b>PROS</b>", BODY_STYLE),
            Paragraph("<b>CONS</b>", BODY_STYLE),
        ]
    ]

    for i in range(max_rows):

        pro = (
            f"• {pros[i]}"
            if i < len(pros)
            else ""
        )

        con = (
            f"• {cons[i]}"
            if i < len(cons)
            else ""
        )

        data.append(
            [
                Paragraph(pro, PRO_STYLE),
                Paragraph(con, CON_STYLE),
            ]
        )

    table = Table(
        data,
        colWidths=[
            87 * mm,
            87 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.lightgrey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    colors.lightgreen,
                ),
                (
                    "BACKGROUND",
                    (1, 0),
                    (1, 0),
                    colors.mistyrose,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ]
        )
    )

    return table


# ============================================================
# CAPITAL ALLOCATION BADGE
# ============================================================

def build_capital_badge(label):

    label = clean_text(label)

    if not label:
        label = "Not Available"

    table = Table(
        [
            [
                Paragraph(
                    f"<b>Capital Allocation</b><br/>{label}",
                    BODY_STYLE,
                )
            ]
        ],
        colWidths=[174 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    colors.grey,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.whitesmoke,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    return table


# ============================================================
# CREATE ONE TEARSHEET
# ============================================================

def create_tearsheet(
    company,
    pnl_df,
    ratios_df,
    bs_df,
    cf_df,
    pros_cons_df,
    intelligence_df,
):

    company_id = company["company_id"]
    company_name = clean_text(
        company.get("company_name", "")
    )or company_id

    ticker = clean_text(
        company.get("ticker", "")
    ) or company_id

    sector = clean_text(
        company.get("broad_sector", "")
    )

    pnl = pnl_df[
        pnl_df["company_id"].astype(str)
        == str(company_id)
    ].copy()

    ratios = ratios_df[
        ratios_df["company_id"].astype(str)
        == str(company_id)
    ].copy()

    bs = bs_df[
        bs_df["company_id"].astype(str)
        == str(company_id)
    ].copy()

    cf = cf_df[
        cf_df["company_id"].astype(str)
        == str(company_id)
    ].copy()

    if len(pnl) < 3:
        return False, "Less than 3 P&L years"

    output_path = OUTPUT_DIR / f"{ticker}_tearsheet.pdf"

    # --------------------------------------------------------
    # CHARTS
    # --------------------------------------------------------

    revenue_chart = create_revenue_profit_chart(
        pnl,
        ticker,
    )

    roe_chart = create_roe_roce_chart(
        ratios,
        ticker,
    )

    bs_chart = create_balance_sheet_chart(
        bs,
        ticker,
    )

    cf_chart = create_cashflow_chart(
        cf,
        ticker,
    )

    # --------------------------------------------------------
    # PROS / CONS
    # --------------------------------------------------------

    pros, cons = get_pros_cons(
        company_id,
        pros_cons_df,
    )

    # --------------------------------------------------------
    # INTELLIGENCE
    # --------------------------------------------------------

    intelligence = intelligence_df[
        intelligence_df["company_id"].astype(str)
        == str(company_id)
    ].copy()

    intelligence_latest = latest_row(
        intelligence
    )

    capital_allocation = ""

    if intelligence_latest is not None:

        column = first_existing_column(
            intelligence,
            [
                "capital_allocation_label",
                "capital_allocation",
            ],
        )

        if column:
            capital_allocation = clean_text(
                intelligence_latest[column]
            )

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"{company_name} Tearsheat",
    )

    story = []

    # ========================================================
    # PAGE 1
    # ========================================================

    story.append(
        Paragraph(
            company_name,
            TITLE_STYLE,
        )
    )

    story.append(
        Paragraph(
            f"<b>{ticker}</b> &nbsp; | &nbsp; {sector}",
            SUBTITLE_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    # KPI tiles

    kpis = get_kpis(
        company_id,
        ratios,
        pnl,
    )

    story.append(
        build_kpi_table(kpis)
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    # Revenue / profit chart

    story.append(
        Paragraph(
            "Financial Performance",
            SECTION_STYLE,
        )
    )

    if revenue_chart:
        story.append(
            Image(
                str(revenue_chart),
                width=174 * mm,
                height=61 * mm,
            )
        )

    story.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    # ROE / ROCE

    if roe_chart:

        story.append(
            Paragraph(
                "Return Trend",
                SECTION_STYLE,
            )
        )

        story.append(
            Image(
                str(roe_chart),
                width=174 * mm,
                height=56 * mm,
            )
        )

    story.append(
        PageBreak()
    )

    # ========================================================
    # PAGE 2
    # ========================================================

    story.append(
        Paragraph(
            f"{company_name} — Balance Sheet & Cash Flow Intelligence",
            SECTION_STYLE,
        )
    )

    # Balance Sheet

    if bs_chart:

        story.append(
            Image(
                str(bs_chart),
                width=174 * mm,
                height=54 * mm,
            )
        )

        story.append(
            Spacer(
                1,
                2 * mm,
            )
        )

    # Cash Flow

    if cf_chart:

        story.append(
            Image(
                str(cf_chart),
                width=174 * mm,
                height=54 * mm,
            )
        )

        story.append(
            Spacer(
                1,
                3 * mm,
            )
        )

    # Capital allocation

    story.append(
        build_capital_badge(
            capital_allocation
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    # Pros and cons

    story.append(
        Paragraph(
            "Pros & Cons",
            SECTION_STYLE,
        )
    )

    story.append(
        build_pros_cons_table(
            pros,
            cons,
        )
    )

    # --------------------------------------------------------
    # BUILD
    # --------------------------------------------------------

    doc.build(story)

    return True, ""


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("DAY 33 — COMPANY TEARSHEET GENERATOR")
    print("=" * 70)

    print()
    print("Project:", PROJECT_ROOT)
    print("Database:", DB_PATH)

    # --------------------------------------------------------
    # LOAD DATABASE
    # --------------------------------------------------------

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    conn = get_connection()

    companies = read_table(
        conn,
        "companies",
    )

    pnl_df = read_table(
        conn,
        "profitandloss",
    )

    if pnl_df.empty:
        pnl_df = read_table(
            conn,
            "profit_loss",
        )

    ratios_df = read_table(
        conn,
        "financial_ratios",
    )

    bs_df = read_table(
        conn,
        "balancesheet",
    )

    if bs_df.empty:
        bs_df = read_table(
            conn,
            "balance_sheet",
        )

    cf_df = read_table(
        conn,
        "cashflow",
    )

    conn.close()

    print()
    print("INPUT DATA")
    print("Companies:", len(companies))
    print("P&L rows:", len(pnl_df))
    print("Ratio rows:", len(ratios_df))
    print("Balance Sheet rows:", len(bs_df))
    print("Cash Flow rows:", len(cf_df))

    # --------------------------------------------------------
    # LOAD OUTPUT FILES
    # --------------------------------------------------------

    if PROS_CONS_PATH.exists():

        pros_cons_df = pd.read_csv(
            PROS_CONS_PATH
        )

    else:

        pros_cons_df = pd.DataFrame()

    if CASHFLOW_INTELLIGENCE_PATH.exists():

        intelligence_df = pd.read_excel(
            CASHFLOW_INTELLIGENCE_PATH
        )

    else:

        intelligence_df = pd.DataFrame()

    # --------------------------------------------------------
    # VALIDATE COMPANY COLUMNS
    # --------------------------------------------------------

    if companies.empty:
        raise RuntimeError(
            "companies table is empty."
        )

    if "company_id" not in companies.columns:
        raise RuntimeError(
            "companies table does not contain company_id."
        )

    # --------------------------------------------------------
    # GENERATE TEARSHEETS
    # --------------------------------------------------------

    generated = 0
    skipped = []

    print()
    print("GENERATING TEARSHEETS...")
    print()

    for _, company in companies.iterrows():

        company_id = clean_text(
            company["company_id"]
        )

        ticker = clean_text(
            company.get(
                "ticker",
                company_id,
            )
        )

        try:

            success, reason = create_tearsheet(
                company=company,
                pnl_df=pnl_df,
                ratios_df=ratios_df,
                bs_df=bs_df,
                cf_df=cf_df,
                pros_cons_df=pros_cons_df,
                intelligence_df=intelligence_df,
            )

            if success:

                generated += 1

                print(
                    f"[OK] {ticker}"
                )

            else:

                skipped.append(
                    {
                        "company_id": company_id,
                        "ticker": ticker,
                        "reason": reason,
                    }
                )

                print(
                    f"[SKIP] {ticker} - {reason}"
                )

        except Exception as exc:

            skipped.append(
                {
                    "company_id": company_id,
                    "ticker": ticker,
                    "reason": str(exc),
                }
            )

            print(
                f"[ERROR] {ticker} - {exc}"
            )

    # --------------------------------------------------------
    # SKIPPED REPORT
    # --------------------------------------------------------

    skipped_path = (
        PROJECT_ROOT
        / "output"
        / "skipped_tearsheets.csv"
    )

    pd.DataFrame(
        skipped
    ).to_csv(
        skipped_path,
        index=False,
    )

    # --------------------------------------------------------
    # FINAL VALIDATION
    # --------------------------------------------------------

    pdfs = list(
        OUTPUT_DIR.glob(
            "*_tearsheet.pdf"
        )
    )

    print()
    print("=" * 70)
    print("DAY 33 VALIDATION")
    print("=" * 70)

    print(
        "Companies in database:",
        len(companies),
    )

    print(
        "Tearsheets generated:",
        generated,
    )

    print(
        "PDF files found:",
        len(pdfs),
    )

    print(
        "Skipped:",
        len(skipped),
    )

    print()
    print("OUTPUT DIRECTORY:")
    print(OUTPUT_DIR)

    if skipped:
        print()
        print("SKIPPED / ERROR COMPANIES:")

        for item in skipped:
            print(
                f"{item['ticker']}: "
                f"{item['reason']}"
            )

    print()
    print("DAY 33 TEARSHEET GENERATION COMPLETE")


if __name__ == "__main__":
    main()