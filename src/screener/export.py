import sys
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.formatting.rule import CellIsRule
from openpyxl.utils import get_column_letter


# ------------------------------------------------------------
# PROJECT PATH
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_PATH = OUTPUT_DIR / "screener_output.xlsx"

# Make src importable when running this file directly.
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from screener.engine import load_config, run_preset


# ------------------------------------------------------------
# PRESET ORDER
# ------------------------------------------------------------

PRESET_ORDER = [
    "quality_compounder",
    "value_pick",
    "growth_accelerator",
    "dividend_champion",
    "debt_free_blue_chip",
    "turnaround_watch",
]


# ------------------------------------------------------------
# DISPLAY COLUMNS
# ------------------------------------------------------------

# Exactly 20 KPI columns as required by Sprint 3.
KPI_COLUMNS = [
    ("ROE", "return_on_equity_pct"),
    ("ROCE", "return_on_capital_employed_pct"),
    ("NPM", "net_profit_margin_pct"),
    ("D/E", "debt_to_equity"),
    ("Interest Coverage", "interest_coverage"),
    ("Asset Turnover", "asset_turnover"),
    ("FCF", "free_cash_flow_cr"),
    ("CFO", "cash_from_operations_cr"),
    ("Revenue CAGR 5Y", "revenue_cagr_5yr"),
    ("PAT CAGR 5Y", "pat_cagr_5yr"),
    ("EPS CAGR 5Y", "eps_cagr_5yr"),
    ("OPM", "operating_profit_margin_pct"),
    ("P/E", "pe_ratio"),
    ("P/B", "pb_ratio"),
    ("Dividend Yield", "dividend_yield_pct"),
    ("Market Cap", "market_cap_crore"),
    ("Net Profit", "net_profit"),
    ("Sales", "sales"),
    ("Dividend Payout", "dividend_payout_ratio_pct"),
    ("Composite Score", "composite_quality_score"),
]


# ------------------------------------------------------------
# PRESET DISPLAY NAMES
# ------------------------------------------------------------

def get_display_name(config, preset_name):
    return config["presets"][preset_name].get(
        "display_name",
        preset_name.replace("_", " ").title(),
    )


# ------------------------------------------------------------
# FILTER COLUMN MAPPING
# ------------------------------------------------------------

FILTER_TO_COLUMN = {
    "roe_min": "return_on_equity_pct",
    "roce_min": "return_on_capital_employed_pct",
    "free_cash_flow_min": "free_cash_flow_cr",
    "revenue_cagr_5yr_min": "revenue_cagr_5yr",
    "revenue_cagr_3yr_min": "revenue_cagr_3yr",
    "pat_cagr_5yr_min": "pat_cagr_5yr",
    "eps_cagr_5yr_min": "eps_cagr_5yr",
    "operating_profit_margin_min": "operating_profit_margin_pct",
    "interest_coverage_min": "interest_coverage",
    "net_profit_min": "net_profit",
    "asset_turnover_min": "asset_turnover",
    "sales_min": "sales",
    "dividend_payout_max": "dividend_payout_ratio_pct",
    "pe_max": "pe_ratio",
    "pb_max": "pb_ratio",
    "dividend_yield_min": "dividend_yield_pct",
    "market_cap_min": "market_cap_crore",
    "debt_to_equity_max": "debt_to_equity",
    "debt_to_equity_equals": "debt_to_equity",
}


# ------------------------------------------------------------
# PRESET CONDITION CHECK
# ------------------------------------------------------------

def condition_mask(df, filter_name, filter_value):
    """
    Return a boolean Series showing which rows meet
    a configured preset condition.
    """

    # D/E maximum:
    # Financial-sector companies are exempt from this
    # specific condition according to Sprint 3 requirements.
    if filter_name == "debt_to_equity_max":

        financials = (
            df["broad_sector"]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq("Financials")
        )

        numeric_pass = (
            df["debt_to_equity"].notna()
            & (df["debt_to_equity"] < filter_value)
        )

        return financials | numeric_pass

    # D/E equals
    if filter_name == "debt_to_equity_equals":
        return (
            df["debt_to_equity"].notna()
            & (df["debt_to_equity"] == filter_value)
        )

    # ICR minimum:
    # Debt Free = effectively infinite ICR.
    if filter_name == "interest_coverage_min":

        debt_free = (
            df["icr_label"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("debt free")
        )

        numeric_pass = (
            df["interest_coverage"].notna()
            & (df["interest_coverage"] > filter_value)
        )

        return debt_free | numeric_pass

    # D/E declining is evaluated using the engine.
    # For export colouring, rows surviving the preset
    # are considered passing.
    if filter_name == "debt_to_equity_declining":
        return pd.Series(True, index=df.index)

    # Standard filters.
    column = FILTER_TO_COLUMN.get(filter_name)

    if column is None or column not in df.columns:
        return pd.Series(True, index=df.index)

    if filter_name.endswith("_min"):
        return df[column].notna() & (df[column] > filter_value)

    if filter_name.endswith("_max"):
        return df[column].notna() & (df[column] < filter_value)

    return df[column].notna() & (df[column] == filter_value)


# ------------------------------------------------------------
# BUILD EXPORT DATAFRAME
# ------------------------------------------------------------

def build_export_dataframe(result):
    """
    Select the required 20 KPI columns plus identifiers.
    """

    output = pd.DataFrame()

    output["Company ID"] = result["company_id"]
    output["Company Name"] = result["company_name"]
    output["Year"] = result["year"]

    for display_name, source_column in KPI_COLUMNS:
        if source_column in result.columns:
            output[display_name] = result[source_column]
        else:
            output[display_name] = pd.NA

    return output


# ------------------------------------------------------------
# EXCEL FORMATTING
# ------------------------------------------------------------

def format_sheet(ws, preset_name, result, config):
    """
    Apply Sprint 3 formatting:
    - Header formatting
    - Green/red KPI cells based on preset filters
    - Composite score number format
    - Frozen header
    - Auto-width
    """

    # Header
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    # Header height
    ws.row_dimensions[1].height = 30

    # Build mapping from export column name to Excel column.
    export_column_numbers = {}

    for col_index, cell in enumerate(ws[1], start=1):
        export_column_numbers[cell.value] = col_index

    # --------------------------------------------------------
    # Conditional formatting
    # --------------------------------------------------------

    preset_filters = config["presets"][preset_name].get("filters", {})

    # Use formula/conditional formatting for threshold columns.
    # Green = passes threshold
    # Red = fails threshold
    #
    # Because financial-sector D/E rows are exempt, D/E is
    # handled separately below.

    for filter_name, filter_value in preset_filters.items():

        if filter_name == "debt_to_equity_declining":
            continue

        source_column = FILTER_TO_COLUMN.get(filter_name)

        if source_column is None:
            continue

        display_name = None

        for name, source in KPI_COLUMNS:
            if source == source_column:
                display_name = name
                break

        if display_name is None:
            continue

        if display_name not in export_column_numbers:
            continue

        col_num = export_column_numbers[display_name]
        col_letter = get_column_letter(col_num)

        start_row = 2
        end_row = ws.max_row

        if end_row < start_row:
            continue

        cell_range = f"{col_letter}{start_row}:{col_letter}{end_row}"

        # Green fill
        green_fill = PatternFill(
            fill_type="solid",
            fgColor="C6EFCE",
        )

        # Red fill
        red_fill = PatternFill(
            fill_type="solid",
            fgColor="FFC7CE",
        )

        # Strict minimum
        if filter_name.endswith("_min"):
            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(
                    operator="greaterThan",
                    formula=[str(filter_value)],
                    fill=green_fill,
                ),
            )

            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(
                    operator="lessThanOrEqual",
                    formula=[str(filter_value)],
                    fill=red_fill,
                ),
            )

        # Strict maximum
        elif filter_name.endswith("_max"):
            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(
                    operator="lessThan",
                    formula=[str(filter_value)],
                    fill=green_fill,
                ),
            )

            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(
                    operator="greaterThanOrEqual",
                    formula=[str(filter_value)],
                    fill=red_fill,
                ),
            )

        # Equality
        elif filter_name.endswith("_equals"):
            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(
                    operator="equal",
                    formula=[str(filter_value)],
                    fill=green_fill,
                ),
            )

            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(
                    operator="notEqual",
                    formula=[str(filter_value)],
                    fill=red_fill,
                ),
            )

    # --------------------------------------------------------
    # Number formats
    # --------------------------------------------------------

    percentage_columns = {
        "ROE",
        "ROCE",
        "NPM",
        "Revenue CAGR 5Y",
        "PAT CAGR 5Y",
        "EPS CAGR 5Y",
        "OPM",
        "Dividend Yield",
        "Dividend Payout",
        "Composite Score",
    }

    for column_name, column_num in export_column_numbers.items():

        column_letter = get_column_letter(column_num)

        for row in range(2, ws.max_row + 1):

            cell = ws.cell(
                row=row,
                column=column_num,
            )

            if column_name in percentage_columns:
                cell.number_format = "0.00"

            elif column_name in {
                "Market Cap",
                "Net Profit",
                "Sales",
                "FCF",
                "CFO",
            }:
                cell.number_format = "#,##0.00"

            elif column_name in {
                "P/E",
                "P/B",
                "D/E",
                "Interest Coverage",
                "Asset Turnover",
            }:
                cell.number_format = "0.00"

    # --------------------------------------------------------
    # Column widths
    # --------------------------------------------------------

    for column_cells in ws.columns:

        max_length = 0
        column_letter = get_column_letter(
            column_cells[0].column
        )

        for cell in column_cells:
            value = "" if cell.value is None else str(cell.value)

            if len(value) > max_length:
                max_length = len(value)

        ws.column_dimensions[column_letter].width = min(
            max(max_length + 2, 12),
            32,
        )


# ------------------------------------------------------------
# EXPORT
# ------------------------------------------------------------

def export_screener():

    print("=" * 70)
    print("SPRINT 3 - SCREENER OUTPUT EXCEL")
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    config = load_config()

    # --------------------------------------------------------
    # Generate workbook
    # --------------------------------------------------------

    with pd.ExcelWriter(
        OUTPUT_PATH,
        engine="openpyxl",
    ) as writer:

        for preset_name in PRESET_ORDER:

            print(f"\nProcessing: {preset_name}")

            result = run_preset(preset_name)

            print(
                f"Companies matched: {len(result)}"
            )

            export_df = build_export_dataframe(
                result
            )

            sheet_name = get_display_name(
                config,
                preset_name,
            )[:31]

            export_df.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False,
            )

    # --------------------------------------------------------
    # Apply formatting
    # --------------------------------------------------------

    workbook = load_workbook(
        OUTPUT_PATH
    )

    for preset_name in PRESET_ORDER:

        sheet_name = get_display_name(
            config,
            preset_name,
        )[:31]

        ws = workbook[sheet_name]

        result = run_preset(
            preset_name
        )

        format_sheet(
            ws,
            preset_name,
            result,
            config,
        )

    workbook.save(
        OUTPUT_PATH
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    workbook = load_workbook(
        OUTPUT_PATH,
        read_only=True,
    )

    expected_sheets = [
        get_display_name(
            config,
            name,
        )[:31]
        for name in PRESET_ORDER
    ]

    actual_sheets = workbook.sheetnames

    print("\nVALIDATION")
    print("-" * 60)

    print(
        "Expected sheets:",
        len(expected_sheets),
    )

    print(
        "Actual sheets:",
        len(actual_sheets),
    )

    print("\nSheet names:")

    for sheet in actual_sheets:
        print(
            " ",
            sheet,
        )

    # Sheet validation
    assert len(actual_sheets) == 6, (
        f"Expected 6 sheets, found {len(actual_sheets)}"
    )

    assert actual_sheets == expected_sheets, (
        "Screener sheet names/order do not match "
        "expected presets."
    )

    # Row-count validation
    print("\nPreset company counts:")

    for preset_name in PRESET_ORDER:

        result = run_preset(
            preset_name
        )

        count = len(result)

        print(
            f"  {preset_name}: {count}"
        )

        # Reference range only.
        # Do not modify preset thresholds just to
        # force the result count into this range.
        if not 5 <= count <= 50:
            print(
                f"NOTE: {preset_name} returned {count} companies; "
                "outside the 5-50 reference range."
            )

    workbook.close()

    print("\nOutput:")
    print(
        OUTPUT_PATH
    )

    print(
        "\nDAY 20/17 SCREENER EXCEL EXPORT COMPLETE"
    )
    print("=" * 70)


if __name__ == "__main__":
    export_screener()