"""
Sprint 5 - Day 32
Capital Allocation Intelligence

Tasks:
1. Verify capital_allocation.csv completeness.
2. Create year-over-year pattern_changes.csv.
3. Add latest capital-allocation pattern to cashflow_intelligence.xlsx.
4. Print latest-year pattern distribution.
"""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CAPITAL_ALLOCATION_FILE = (
    PROJECT_ROOT / "output" / "capital_allocation.csv"
)

CASHFLOW_INTELLIGENCE_FILE = (
    PROJECT_ROOT / "output" / "cashflow_intelligence.xlsx"
)

PATTERN_CHANGES_FILE = (
    PROJECT_ROOT / "output" / "pattern_changes.csv"
)


REQUIRED_COLUMNS = [
    "company_id",
    "year",
    "cfo_sign",
    "cfi_sign",
    "cff_sign",
    "pattern_label",
]


def load_capital_allocation():
    """Load and validate capital allocation data."""

    df = pd.read_csv(CAPITAL_ALLOCATION_FILE)

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    df = df[REQUIRED_COLUMNS].copy()

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    if df["year"].isna().any():
        raise ValueError("Invalid year values found.")

    df["year"] = df["year"].astype(int)

    return df


def verify_completeness(df):
    """Verify no duplicate company-year records."""

    duplicates = (
        df.groupby(["company_id", "year"])
        .size()
        .reset_index(name="count")
    )

    duplicates = duplicates[duplicates["count"] > 1]

    if not duplicates.empty:
        raise ValueError(
            "Duplicate company-year records found:\n"
            + duplicates.to_string(index=False)
        )

    return True


def create_pattern_changes(df):
    """
    Compare each company's capital allocation pattern
    with the previous available year.

    A row is created only when a company has a previous
    available year.
    """

    df = df.sort_values(
        ["company_id", "year"]
    ).copy()

    df["previous_year"] = (
        df.groupby("company_id")["year"]
        .shift(1)
    )

    df["previous_pattern"] = (
        df.groupby("company_id")["pattern_label"]
        .shift(1)
    )

    changes = df[
        df["previous_pattern"].notna()
    ].copy()

    changes["pattern_changed"] = (
        changes["pattern_label"]
        != changes["previous_pattern"]
    )

    changes = changes[
        [
            "company_id",
            "previous_year",
            "year",
            "previous_pattern",
            "pattern_label",
            "pattern_changed",
        ]
    ]

    changes = changes.rename(
        columns={
            "previous_year": "from_year",
            "year": "to_year",
            "previous_pattern": "from_pattern",
            "pattern_label": "to_pattern",
        }
    )

    return changes


def get_latest_patterns(df):
    """Return each company's latest available pattern."""

    latest = (
        df.sort_values(["company_id", "year"])
        .groupby("company_id", as_index=False)
        .tail(1)
        .copy()
    )

    latest = latest[
        [
            "company_id",
            "year",
            "pattern_label",
        ]
    ]

    return latest


def update_cashflow_intelligence(latest_patterns):
    """
    Add latest capital allocation pattern to
    cashflow_intelligence.xlsx.
    """

    intelligence = pd.read_excel(
        CASHFLOW_INTELLIGENCE_FILE
    )

    # Remove the old label if the script is run again.
    if "capital_allocation_label" in intelligence.columns:
        intelligence = intelligence.drop(
            columns=["capital_allocation_label"]
        )

    intelligence = intelligence.merge(
        latest_patterns[
            [
                "company_id",
                "pattern_label",
            ]
        ],
        on="company_id",
        how="left",
    )

    intelligence = intelligence.rename(
        columns={
            "pattern_label": "capital_allocation_label"
        }
    )

    intelligence.to_excel(
        CASHFLOW_INTELLIGENCE_FILE,
        index=False,
    )

    return intelligence


def main():

    print("=" * 70)
    print("DAY 32 — CAPITAL ALLOCATION INTELLIGENCE")
    print("=" * 70)

    df = load_capital_allocation()

    print()
    print("INPUT")
    print(f"Capital allocation rows: {len(df)}")
    print(f"Companies: {df['company_id'].nunique()}")
    print(
        f"Company-years: "
        f"{df[['company_id', 'year']].drop_duplicates().shape[0]}"
    )

    # --------------------------------------------------
    # 1. Completeness validation
    # --------------------------------------------------

    verify_completeness(df)

    print()
    print("COMPLETENESS")
    print("PASS: Required columns present.")
    print("PASS: No duplicate company-year records.")

    # --------------------------------------------------
    # 2. Year-over-year pattern changes
    # --------------------------------------------------

    pattern_changes = create_pattern_changes(df)

    pattern_changes.to_csv(
        PATTERN_CHANGES_FILE,
        index=False,
    )

    print()
    print("PATTERN CHANGES")
    print(
        f"Year-over-year comparisons: "
        f"{len(pattern_changes)}"
    )

    print(
        f"Pattern changes: "
        f"{pattern_changes['pattern_changed'].sum()}"
    )

    print(
        f"Unchanged patterns: "
        f"{(~pattern_changes['pattern_changed']).sum()}"
    )

    # --------------------------------------------------
    # 3. Latest pattern for each company
    # --------------------------------------------------

    latest_patterns = get_latest_patterns(df)

    print()
    print("LATEST YEAR PATTERNS")

    print(
        latest_patterns["pattern_label"]
        .value_counts()
        .to_string()
    )

    # --------------------------------------------------
    # 4. Update cashflow intelligence
    # --------------------------------------------------

    intelligence = update_cashflow_intelligence(
        latest_patterns
    )

    print()
    print("CASHFLOW INTELLIGENCE")

    print(
        f"Rows in cashflow intelligence: "
        f"{len(intelligence)}"
    )

    missing_patterns = intelligence[
        intelligence["capital_allocation_label"].isna()
    ]

    if missing_patterns.empty:
        print(
            "PASS: Every generated cash-flow company "
            "has a capital allocation pattern."
        )
    else:
        print(
            "WARNING: Companies missing capital "
            "allocation pattern:"
        )
        print(
            missing_patterns[
                ["company_id"]
            ].to_string(index=False)
        )

    # --------------------------------------------------
    # 5. Final output
    # --------------------------------------------------

    print()
    print("OUTPUT")
    print(
        f"Pattern changes: "
        f"{PATTERN_CHANGES_FILE}"
    )

    print(
        f"Updated intelligence: "
        f"{CASHFLOW_INTELLIGENCE_FILE}"
    )

    print()
    print("DAY 32 CAPITAL ALLOCATION COMPLETE")


if __name__ == "__main__":
    main()