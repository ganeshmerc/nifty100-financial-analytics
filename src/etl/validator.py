"""
Sprint 1 - Data Quality Validator

DQ-01 to DQ-16.

CRITICAL:
    DQ-01 Primary-key uniqueness
    DQ-02 Company/year uniqueness
    DQ-03 Foreign-key integrity
    DQ-04 Balance-sheet balance

WARNING:
    DQ-05 OPM cross-check
    DQ-06 Positive sales
    DQ-07 Net cash consistency
    DQ-08 Tax-rate sanity
    DQ-09 Dividend payout cap
    DQ-10 URL validity
    DQ-11 EPS sign consistency
    DQ-12 BSE balance
    DQ-13 Historical coverage
    DQ-14 Missing financial data
    DQ-15 Ratio sanity
    DQ-16 Duplicate company records
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output"


@dataclass
class ValidationFailure:
    company_id: Optional[int]
    year: Optional[int]
    rule_id: str
    severity: str
    message: str


class DataQualityValidator:

    def __init__(self):
        self.failures = []

    def add_failure(
        self,
        rule_id,
        severity,
        message,
        company_id=None,
        year=None,
    ):
        self.failures.append(
            ValidationFailure(
                company_id=company_id,
                year=year,
                rule_id=rule_id,
                severity=severity,
                message=message,
            )
        )

    # ========================================================
    # DQ-01
    # Primary key uniqueness
    # ========================================================

    def check_pk_uniqueness(
        self,
        df,
        key_columns,
        rule_id="DQ-01",
    ):

        duplicates = df[
            df.duplicated(
                subset=key_columns,
                keep=False,
            )
        ]

        for _, row in duplicates.iterrows():

            self.add_failure(
                rule_id=rule_id,
                severity="CRITICAL",
                company_id=row.get("company_id"),
                year=row.get("year"),
                message=(
                    f"Duplicate key: "
                    f"{[row.get(c) for c in key_columns]}"
                ),
            )

    # ========================================================
    # DQ-02
    # Company + year uniqueness
    # ========================================================

    def check_company_year_uniqueness(self, df):

        if not {"company_id", "year"}.issubset(df.columns):
            return

        self.check_pk_uniqueness(
            df,
            ["company_id", "year"],
            "DQ-02",
        )

    # ========================================================
    # DQ-03
    # Foreign-key integrity
    # ========================================================

    def check_foreign_keys(
        self,
        child_df,
        parent_df,
        foreign_key="company_id",
    ):

        if foreign_key not in child_df.columns:
            return

        if foreign_key not in parent_df.columns:
            return

        valid_ids = set(
            parent_df[foreign_key].dropna()
        )

        invalid = child_df[
            ~child_df[foreign_key].isin(valid_ids)
        ]

        for _, row in invalid.iterrows():

            self.add_failure(
                rule_id="DQ-03",
                severity="CRITICAL",
                company_id=row.get("company_id"),
                year=row.get("year"),
                message=(
                    f"Invalid foreign key: "
                    f"{row.get(foreign_key)}"
                ),
            )

    # ========================================================
    # DQ-04
    # Balance-sheet balance
    # ========================================================

    def check_balance_sheet_balance(
        self,
        df,
        tolerance=0.01,
    ):

        required = {
            "total_assets",
            "total_liabilities",
        }

        if not required.issubset(df.columns):
            return

        for _, row in df.iterrows():

            assets = row["total_assets"]
            liabilities = row["total_liabilities"]

            if pd.isna(assets) or pd.isna(liabilities):
                continue

            if assets == 0:
                continue

            difference = (
                abs(assets - liabilities)
                / abs(assets)
            )

            if difference > tolerance:

                self.add_failure(
                    rule_id="DQ-04",
                    severity="CRITICAL",
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                    message=(
                        f"Balance mismatch: "
                        f"{difference:.2%}"
                    ),
                )

    # ========================================================
    # DQ-05
    # OPM cross-check
    # ========================================================

    def check_opm_crosscheck(
        self,
        df,
        tolerance=1.0,
    ):

        required = {
            "sales",
            "operating_profit",
            "opm_percentage",
        }

        if not required.issubset(df.columns):
            return

        for _, row in df.iterrows():

            sales = row["sales"]
            operating_profit = row["operating_profit"]
            source_opm = row["opm_percentage"]

            if pd.isna(sales) or sales == 0:
                continue

            if pd.isna(operating_profit) or pd.isna(source_opm):
                continue

            calculated = (
                operating_profit / sales
            ) * 100

            difference = abs(
                calculated - source_opm
            )

            if difference > tolerance:

                self.add_failure(
                    rule_id="DQ-05",
                    severity="WARNING",
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                    message=(
                        f"OPM mismatch: "
                        f"calculated={calculated:.2f}, "
                        f"source={source_opm:.2f}, "
                        f"difference={difference:.2f}"
                    ),
                )

    # ========================================================
    # DQ-06
    # Positive sales
    # ========================================================

    def check_positive_sales(self, df):

        if "sales" not in df.columns:
            return

        invalid = df[
            df["sales"].notna()
            & (df["sales"] <= 0)
        ]

        for _, row in invalid.iterrows():

            self.add_failure(
                rule_id="DQ-06",
                severity="WARNING",
                company_id=row.get("company_id"),
                year=row.get("year"),
                message=(
                    f"Sales must be positive: "
                    f"{row.get('sales')}"
                ),
            )

    # ========================================================
    # DQ-07
    # Net cash consistency
    # ========================================================

    def check_net_cash(
        self,
        df,
        tolerance=0.01,
    ):

        required = {
            "cash",
            "borrowings",
            "net_cash",
        }

        if not required.issubset(df.columns):
            return

        for _, row in df.iterrows():

            cash = row["cash"]
            borrowings = row["borrowings"]
            source_net_cash = row["net_cash"]

            if any(
                pd.isna(x)
                for x in [
                    cash,
                    borrowings,
                    source_net_cash,
                ]
            ):
                continue

            calculated = cash - borrowings

            if abs(calculated - source_net_cash) > tolerance:

                self.add_failure(
                    rule_id="DQ-07",
                    severity="WARNING",
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                    message=(
                        f"Net cash mismatch: "
                        f"calculated={calculated:.2f}, "
                        f"source={source_net_cash:.2f}"
                    ),
                )

    # ========================================================
    # DQ-08
    # Tax-rate sanity
    # ========================================================

    def check_tax_rate(
        self,
        df,
        minimum=-100,
        maximum=100,
    ):

        if "tax_rate" not in df.columns:
            return

        invalid = df[
            df["tax_rate"].notna()
            & (
                (df["tax_rate"] < minimum)
                | (df["tax_rate"] > maximum)
            )
        ]

        for _, row in invalid.iterrows():

            self.add_failure(
                rule_id="DQ-08",
                severity="WARNING",
                company_id=row.get("company_id"),
                year=row.get("year"),
                message=(
                    f"Tax rate outside expected range: "
                    f"{row.get('tax_rate')}"
                ),
            )

    # ========================================================
    # DQ-09
    # Dividend payout cap
    # ========================================================

    def check_dividend_payout(
        self,
        df,
        maximum=100,
    ):

        if "dividend_payout_ratio" not in df.columns:
            return

        invalid = df[
            df["dividend_payout_ratio"].notna()
            & (
                df["dividend_payout_ratio"]
                > maximum
            )
        ]

        for _, row in invalid.iterrows():

            self.add_failure(
                rule_id="DQ-09",
                severity="WARNING",
                company_id=row.get("company_id"),
                year=row.get("year"),
                message=(
                    "Dividend payout ratio "
                    f"exceeds {maximum}%: "
                    f"{row.get('dividend_payout_ratio')}"
                ),
            )

    # ========================================================
    # DQ-10
    # URL validation
    # ========================================================

    def check_urls(
        self,
        df,
        url_column="url",
    ):

        if url_column not in df.columns:
            return

        for _, row in df.iterrows():

            value = row.get(url_column)

            if pd.isna(value) or not str(value).strip():
                continue

            value = str(value).strip()

            try:
                parsed = urlparse(value)

                valid = (
                    parsed.scheme in {
                        "http",
                        "https",
                    }
                    and bool(parsed.netloc)
                )

            except Exception:
                valid = False

            if not valid:

                self.add_failure(
                    rule_id="DQ-10",
                    severity="WARNING",
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                    message=f"Invalid URL: {value}",
                )

    # ========================================================
    # DQ-11
    # EPS sign consistency
    # ========================================================

    def check_eps_sign(
        self,
        df,
    ):

        required = {
            "eps",
            "net_profit",
        }

        if not required.issubset(df.columns):
            return

        for _, row in df.iterrows():

            eps = row["eps"]
            net_profit = row["net_profit"]

            if pd.isna(eps) or pd.isna(net_profit):
                continue

            if (
                net_profit > 0
                and eps < 0
            ) or (
                net_profit < 0
                and eps > 0
            ):

                self.add_failure(
                    rule_id="DQ-11",
                    severity="WARNING",
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                    message=(
                        f"EPS sign inconsistent with "
                        f"net profit: EPS={eps}, "
                        f"PAT={net_profit}"
                    ),
                )

    # ========================================================
    # DQ-12
    # BSE balance
    # ========================================================

    def check_bse_balance(
        self,
        df,
        tolerance=0.01,
    ):

        required = {
            "bse_assets",
            "bse_liabilities",
        }

        if not required.issubset(df.columns):
            return

        for _, row in df.iterrows():

            assets = row["bse_assets"]
            liabilities = row["bse_liabilities"]

            if pd.isna(assets) or pd.isna(liabilities):
                continue

            if assets == 0:
                continue

            difference = (
                abs(assets - liabilities)
                / abs(assets)
            )

            if difference > tolerance:

                self.add_failure(
                    rule_id="DQ-12",
                    severity="WARNING",
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                    message=(
                        f"BSE balance mismatch: "
                        f"{difference:.2%}"
                    ),
                )

    # ========================================================
    # DQ-13
    # Historical coverage
    # ========================================================

    def check_year_coverage(
        self,
        df,
        minimum_years=1,
    ):

        required = {
            "company_id",
            "year",
        }

        if not required.issubset(df.columns):
            return

        coverage = (
            df.groupby("company_id")["year"]
            .nunique()
        )

        for company_id, count in coverage.items():

            if count < minimum_years:

                self.add_failure(
                    rule_id="DQ-13",
                    severity="WARNING",
                    company_id=company_id,
                    message=(
                        f"Only {count} year(s) "
                        "of historical data"
                    ),
                )

    # ========================================================
    # DQ-14
    # Missing financial data
    # ========================================================

    def check_missing_financial_data(
        self,
        df,
        required_columns,
    ):

        available = [
            column
            for column in required_columns
            if column in df.columns
        ]

        if not available:
            return

        for _, row in df.iterrows():

            missing = [
                column
                for column in available
                if pd.isna(row[column])
            ]

            if missing:

                self.add_failure(
                    rule_id="DQ-14",
                    severity="WARNING",
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                    message=(
                        "Missing financial fields: "
                        + ", ".join(missing)
                    ),
                )

    # ========================================================
    # DQ-15
    # Ratio sanity
    # ========================================================

    def check_ratio_sanity(
        self,
        df,
        ratio_columns,
    ):

        for column in ratio_columns:

            if column not in df.columns:
                continue

            for _, row in df.iterrows():

                value = row[column]

                if pd.isna(value):
                    continue

                if not pd.api.types.is_number(value):
                    continue

                if abs(value) > 10000:

                    self.add_failure(
                        rule_id="DQ-15",
                        severity="WARNING",
                        company_id=row.get("company_id"),
                        year=row.get("year"),
                        message=(
                            f"Unusually large ratio "
                            f"{column}={value}"
                        ),
                    )

    # ========================================================
    # DQ-16
    # Duplicate company records
    # ========================================================

    def check_duplicate_companies(
        self,
        df,
    ):

        if "company_id" not in df.columns:
            return

        duplicates = df[
            df.duplicated(
                subset=["company_id"],
                keep=False,
            )
        ]

        for _, row in duplicates.iterrows():

            self.add_failure(
                rule_id="DQ-16",
                severity="WARNING",
                company_id=row.get("company_id"),
                year=row.get("year"),
                message=(
                    "Duplicate company record"
                ),
            )

    # ========================================================
    # Run rules
    # ========================================================

    def run_all(
        self,
        df,
        companies_df=None,
    ):

        self.check_company_year_uniqueness(df)

        if "company_id" in df.columns:
            self.check_pk_uniqueness(
                df,
                ["company_id"],
            )

        if companies_df is not None:
            self.check_foreign_keys(
                df,
                companies_df,
            )

        self.check_balance_sheet_balance(df)

        self.check_opm_crosscheck(df)

        self.check_positive_sales(df)

        self.check_net_cash(df)

        self.check_tax_rate(df)

        self.check_dividend_payout(df)

        self.check_urls(df)

        self.check_eps_sign(df)

        self.check_bse_balance(df)

        self.check_year_coverage(df)

        self.check_missing_financial_data(
            df,
            [
                "sales",
                "operating_profit",
                "net_profit",
            ],
        )

        self.check_ratio_sanity(
            df,
            [
                "opm_percentage",
                "roe_percentage",
                "roce_percentage",
            ],
        )

        self.check_duplicate_companies(df)

        return self.failures

    # ========================================================
    # Export
    # ========================================================

    def export_failures(
        self,
        filename="validation_failures.csv",
    ):

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = OUTPUT_DIR / filename

        df = pd.DataFrame(
            [
                asdict(failure)
                for failure in self.failures
            ]
        )

        if df.empty:

            df = pd.DataFrame(
                columns=[
                    "company_id",
                    "year",
                    "rule_id",
                    "severity",
                    "message",
                ]
            )

        df.to_csv(
            output_path,
            index=False,
        )

        return output_path


def validate_database():

    print("=" * 60)
    print("NIFTY 100 - DATA QUALITY VALIDATOR")
    print("=" * 60)

    print()
    print("DQ-01 through DQ-16 validator loaded.")
    print("Ready for source data.")


if __name__ == "__main__":
    validate_database()