from pathlib import Path
import re
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "source" / "analysis.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "output"

PARSED_FILE = OUTPUT_DIR / "analysis_parsed.csv"
FAILURES_FILE = OUTPUT_DIR / "parse_failures.csv"


METRIC_COLUMNS = {
    "compounded_sales_growth": "revenue_cagr",
    "compounded_profit_growth": "pat_cagr",
    "stock_price_cagr": "stock_price_cagr",
    "roe": "roe",
}


# Examples supported:
# 10 Years: 21%
# 5 Years: 24%
# 3 Years: 17%
# 1 Year: -2%
#
# TTM / Last Year are intentionally not assigned a numeric period.
PERIOD_VALUE_PATTERN = re.compile(
    r"^\s*(\d+)\s*Years?\s*:?\s*(-?[\d.]+)\s*%\s*$",
    re.IGNORECASE,
)


def parse_period_value(value):
    """
    Parse values such as:
        10 Years: 21%
        5 Years: 24%
        3 Years: 17%
        1 Year: -2%

    Returns:
        (period_years, value_pct)
        or (None, None) when the value is not a numeric-period format.
    """
    if pd.isna(value):
        return None, None

    text = str(value).strip()

    match = PERIOD_VALUE_PATTERN.match(text)

    if not match:
        return None, None

    period_years = int(match.group(1))
    value_pct = float(match.group(2))

    return period_years, value_pct


def load_analysis():
    """
    Load analysis.xlsx.

    The workbook contains a title row, so the actual column headers
    are on Excel row 2.
    """
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    df = pd.read_excel(INPUT_FILE, header=1)

    required_columns = [
        "id",
        "company_id",
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe",
    ]

    missing = [c for c in required_columns if c not in df.columns]

    if missing:
        raise ValueError(
            f"Missing required columns in analysis.xlsx: {missing}"
        )

    return df[required_columns].copy()


def parse_analysis(df):
    parsed_rows = []
    failure_rows = []

    for _, row in df.iterrows():
        company_id = str(row["company_id"]).strip()

        for source_column, metric_type in METRIC_COLUMNS.items():
            raw_value = row[source_column]

            period_years, value_pct = parse_period_value(raw_value)

            if period_years is not None:
                parsed_rows.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric_type,
                        "period_years": period_years,
                        "value_pct": value_pct,
                    }
                )
            else:
                failure_rows.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric_type,
                        "raw_value": raw_value,
                        "reason": "Does not match numeric period pattern",
                    }
                )

    parsed = pd.DataFrame(
        parsed_rows,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
        ],
    )

    failures = pd.DataFrame(
        failure_rows,
        columns=[
            "company_id",
            "metric_type",
            "raw_value",
            "reason",
        ],
    )

    return parsed, failures


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("DAY 29 — NLP ANALYSIS TEXT PARSER")
    print("=" * 60)

    df = load_analysis()

    print(f"Input file: {INPUT_FILE}")
    print(f"Input rows: {len(df)}")
    print(f"Input companies: {df['company_id'].nunique()}")

    parsed, failures = parse_analysis(df)

    parsed.to_csv(PARSED_FILE, index=False)
    failures.to_csv(FAILURES_FILE, index=False)

    print()
    print(f"Parsed rows: {len(parsed)}")
    print(f"Parse failures: {len(failures)}")
    print(f"Parsed output: {PARSED_FILE}")
    print(f"Failure output: {FAILURES_FILE}")

    if not parsed.empty:
        print()
        print("Parsed metric counts:")
        print(parsed["metric_type"].value_counts().to_string())

        print()
        print("Period counts:")
        print(parsed["period_years"].value_counts().sort_index().to_string())

    if not failures.empty:
        print()
        print("Failure examples:")
        print(failures.head(10).to_string(index=False))

    print()
    print("DAY 29 PARSER COMPLETE")


if __name__ == "__main__":
    main()