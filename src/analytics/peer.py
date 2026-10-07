"""
Sprint 3 - Day 18 Peer Percentile Engine

Calculates PERCENT_RANK within each peer group for 10 metrics.

Metrics:
1. ROE
2. ROCE
3. NPM
4. D/E (inverse percentile)
5. FCF
6. PAT CAGR 5Y
7. Revenue CAGR 5Y
8. EPS CAGR 5Y
9. Interest Coverage
10. Asset Turnover

Source:
    data/source/peer_groups.xlsx

Output:
    SQLite table: peer_percentiles
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"
PEER_GROUPS_PATH = PROJECT_ROOT / "data" / "source" / "peer_groups.xlsx"


METRIC_MAPPING = {
    "ROE": "return_on_equity_pct",
    "ROCE": "return_on_capital_employed_pct",
    "NPM": "net_profit_margin_pct",
    "D/E": "debt_to_equity",
    "FCF": "free_cash_flow_cr",
    "PAT CAGR 5Y": "pat_cagr_5yr",
    "Revenue CAGR 5Y": "revenue_cagr_5yr",
    "EPS CAGR 5Y": "eps_cagr_5yr",
    "Interest Coverage": "interest_coverage",
    "Asset Turnover": "asset_turnover",
}


def load_peer_groups() -> pd.DataFrame:
    """Load peer-group membership from the Excel source."""

    if not PEER_GROUPS_PATH.exists():
        raise FileNotFoundError(
            f"Peer-group file not found: {PEER_GROUPS_PATH}"
        )

    df = pd.read_excel(PEER_GROUPS_PATH)

    required_columns = {
        "id",
        "peer_group_name",
        "company_id",
        "is_benchmark",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing peer-group columns: {sorted(missing)}"
        )

    df = df[
        [
            "id",
            "peer_group_name",
            "company_id",
            "is_benchmark",
        ]
    ].copy()

    df["company_id"] = df["company_id"].astype(str).str.strip()
    df["peer_group_name"] = (
        df["peer_group_name"].astype(str).str.strip()
    )

    return df


def load_latest_financial_ratios() -> pd.DataFrame:
    """Load the latest financial-ratio record for every company."""

    conn = sqlite3.connect(DB_PATH)

    query = """
        WITH latest AS (
            SELECT
                company_id,
                MAX(year) AS year
            FROM financial_ratios
            GROUP BY company_id
        )
        SELECT
            fr.company_id,
            fr.year,
            fr.return_on_equity_pct,
            fr.return_on_capital_employed_pct,
            fr.net_profit_margin_pct,
            fr.debt_to_equity,
            fr.free_cash_flow_cr,
            fr.pat_cagr_5yr,
            fr.revenue_cagr_5yr,
            fr.eps_cagr_5yr,
            fr.interest_coverage,
            fr.asset_turnover
        FROM financial_ratios fr
        INNER JOIN latest l
            ON fr.company_id = l.company_id
            AND fr.year = l.year
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


def calculate_percentile(series: pd.Series) -> pd.Series:
    """
    Calculate percentile rank equivalent to PERCENT_RANK.

    Formula:
        (rank - 1) / (n - 1)

    Returns values between 0 and 1.
    """

    numeric = pd.to_numeric(series, errors="coerce")

    valid = numeric.notna()

    result = pd.Series(float("nan"), index=series.index)

    count = valid.sum()

    if count == 0:
        return result

    if count == 1:
        result.loc[valid] = 1.0
        return result

    ranks = numeric.loc[valid].rank(
        method="min",
        ascending=True,
    )

    result.loc[valid] = (ranks - 1) / (count - 1)

    return result


def calculate_peer_percentiles(
    peer_groups: pd.DataFrame,
    financial_ratios: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate all 10 peer percentile metrics."""

    merged = peer_groups.merge(
        financial_ratios,
        on="company_id",
        how="left",
    )

    rows = []

    for peer_group_name, group in merged.groupby(
        "peer_group_name",
        sort=True,
    ):
        for metric_name, source_column in METRIC_MAPPING.items():

            values = group[source_column]

            percentile = calculate_percentile(values)

            # D/E is better when lower, so invert percentile.
            if metric_name == "D/E":
                percentile = 1 - percentile

            for idx in group.index:

                value = group.loc[idx, source_column]
                pct = percentile.loc[idx]

                rows.append(
                    {
                        "company_id": group.loc[idx, "company_id"],
                        "peer_group_name": peer_group_name,
                        "metric": metric_name,
                        "value": (
                            None
                            if pd.isna(value)
                            else float(value)
                        ),
                        "percentile_rank": (
                            None
                            if pd.isna(pct)
                            else float(pct)
                        ),
                        "year": (
                            None
                            if pd.isna(group.loc[idx, "year"])
                            else int(group.loc[idx, "year"])
                        ),
                    }
                )

    return pd.DataFrame(rows)


def create_output_table(conn: sqlite3.Connection) -> None:
    """Create the peer_percentiles table."""

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS peer_percentiles (
            company_id TEXT NOT NULL,
            peer_group_name TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL,
            percentile_rank REAL,
            year INTEGER,
            PRIMARY KEY (
                company_id,
                peer_group_name,
                metric
            )
        )
        """
    )

    conn.commit()


def save_percentiles(df: pd.DataFrame) -> int:
    """Replace existing peer percentile results."""

    conn = sqlite3.connect(DB_PATH)

    create_output_table(conn)

    conn.execute("DELETE FROM peer_percentiles")

    rows = 0

    for row in df.itertuples(index=False):

        conn.execute(
            """
            INSERT INTO peer_percentiles (
                company_id,
                peer_group_name,
                metric,
                value,
                percentile_rank,
                year
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                row.company_id,
                row.peer_group_name,
                row.metric,
                row.value,
                row.percentile_rank,
                row.year,
            ),
        )

        rows += 1

    conn.commit()
    conn.close()

    return rows


def validate_results(
    peer_groups: pd.DataFrame,
    percentiles: pd.DataFrame,
) -> None:
    """Print basic Day 18 validation checks."""

    print("\nVALIDATION")
    print("-" * 60)

    print(
        "Peer groups:",
        peer_groups["peer_group_name"].nunique(),
    )

    print(
        "Companies in peer groups:",
        peer_groups["company_id"].nunique(),
    )

    print(
        "Metrics:",
        percentiles["metric"].nunique(),
    )

    print(
        "Expected percentile rows:",
        len(peer_groups)
        * len(METRIC_MAPPING),
    )

    print(
        "Actual percentile rows:",
        len(percentiles),
    )

    non_null = percentiles[
        percentiles["percentile_rank"].notna()
    ]

    print(
        "Non-null percentiles:",
        len(non_null),
    )

    print(
        "Percentiles below 0:",
        (non_null["percentile_rank"] < 0).sum(),
    )

    print(
        "Percentiles above 1:",
        (non_null["percentile_rank"] > 1).sum(),
    )

    print(
        "D/E records:",
        (percentiles["metric"] == "D/E").sum(),
    )

    print("\nPeer-group distribution:")

    print(
        peer_groups.groupby("peer_group_name")
        .size()
        .sort_values(ascending=False)
        .to_string()
    )


def main() -> None:

    print("\nSPRINT 3 - DAY 18 PEER PERCENTILE ENGINE\n")

    peer_groups = load_peer_groups()

    print(
        "Peer-group rows loaded:",
        len(peer_groups),
    )

    print(
        "Peer groups found:",
        peer_groups["peer_group_name"].nunique(),
    )

    financial_ratios = load_latest_financial_ratios()

    print(
        "Latest financial-ratio companies:",
        financial_ratios["company_id"].nunique(),
    )

    percentiles = calculate_peer_percentiles(
        peer_groups,
        financial_ratios,
    )

    print(
        "Percentile rows generated:",
        len(percentiles),
    )

    updated = save_percentiles(percentiles)

    print(
        "Database rows saved:",
        updated,
    )

    validate_results(
        peer_groups,
        percentiles,
    )

    print("\nSample results:")
    print(
        percentiles.head(20).to_string(index=False)
    )

    print("\nDAY 18 PEER PERCENTILE ENGINE COMPLETE")


if __name__ == "__main__":
    main()