"""
Sprint 3 - Day 19 Peer Radar Charts

Generates 8-axis radar charts using peer percentile scores.

Axes:
1. ROE
2. ROCE
3. NPM
4. D/E
5. FCF
6. PAT CAGR 5Y
7. Revenue CAGR 5Y
8. EPS CAGR 5Y

Output:
    reports/radar_charts/<company_id>_radar.png
"""

from __future__ import annotations

import math
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "radar_charts"


RADAR_METRICS = [
    "ROE",
    "ROCE",
    "NPM",
    "D/E",
    "FCF",
    "PAT CAGR 5Y",
    "Revenue CAGR 5Y",
    "EPS CAGR 5Y",
]


def load_peer_percentiles() -> pd.DataFrame:
    """Load peer percentile data from SQLite."""

    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            company_id,
            peer_group_name,
            metric,
            percentile_rank
        FROM peer_percentiles
        WHERE metric IN (
            'ROE',
            'ROCE',
            'NPM',
            'D/E',
            'FCF',
            'PAT CAGR 5Y',
            'Revenue CAGR 5Y',
            'EPS CAGR 5Y'
        )
        ORDER BY peer_group_name, company_id, metric
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


def safe_filename(company_id: str) -> str:
    """Return a filesystem-safe company ID."""

    return "".join(
        character
        for character in str(company_id)
        if character.isalnum() or character in ("-", "_")
    )


def create_radar_chart(
    company_id: str,
    peer_group_name: str,
    data: pd.DataFrame,
) -> Path:
    """Create one radar chart for a company."""

    values_map = dict(
        zip(
            data["metric"],
            data["percentile_rank"],
        )
    )

    values = []

    for metric in RADAR_METRICS:
        value = values_map.get(metric)

        if pd.isna(value):
            value = 0.0

        values.append(float(value) * 100)

    # Close the radar polygon.
    angles = np.linspace(
        0,
        2 * math.pi,
        len(RADAR_METRICS),
        endpoint=False,
    ).tolist()

    values_closed = values + values[:1]
    angles_closed = angles + angles[:1]

    fig = plt.figure(figsize=(8, 8))

    ax = fig.add_subplot(
        111,
        polar=True,
    )

    ax.plot(
        angles_closed,
        values_closed,
        linewidth=2,
    )

    ax.fill(
        angles_closed,
        values_closed,
        alpha=0.20,
    )

    ax.set_xticks(angles)

    ax.set_xticklabels(
        RADAR_METRICS,
        fontsize=9,
    )

    ax.set_ylim(0, 100)

    ax.set_yticks(
        [20, 40, 60, 80, 100]
    )

    ax.set_yticklabels(
        ["20", "40", "60", "80", "100"],
        fontsize=8,
    )

    ax.set_title(
        f"{company_id} — Peer Percentile Profile\n"
        f"{peer_group_name}",
        pad=25,
        fontsize=13,
        fontweight="bold",
    )

    output_path = (
        OUTPUT_DIR
        / f"{safe_filename(company_id)}_radar.png"
    )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)

    return output_path


def generate_all_radar_charts(
    df: pd.DataFrame,
) -> list[Path]:
    """Generate radar charts for every company."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated_files = []

    for (
        peer_group_name,
        company_id,
    ), group in df.groupby(
        ["peer_group_name", "company_id"],
        sort=True,
    ):

        output_path = create_radar_chart(
            company_id=company_id,
            peer_group_name=peer_group_name,
            data=group,
        )

        generated_files.append(output_path)

    return generated_files


def validate_radar_data(
    df: pd.DataFrame,
) -> None:
    """Print Day 19 validation information."""

    print("\nVALIDATION")
    print("-" * 60)

    print(
        "Companies:",
        df["company_id"].nunique(),
    )

    print(
        "Peer groups:",
        df["peer_group_name"].nunique(),
    )

    print(
        "Metrics:",
        df["metric"].nunique(),
    )

    expected_rows = (
        df["company_id"].nunique()
        * len(RADAR_METRICS)
    )

    print(
        "Expected maximum rows:",
        expected_rows,
    )

    print(
        "Actual rows:",
        len(df),
    )

    print(
        "Non-null percentile values:",
        df["percentile_rank"].notna().sum(),
    )


def main() -> None:

    print("\nSPRINT 3 - DAY 19 PEER RADAR CHARTS\n")

    df = load_peer_percentiles()

    if df.empty:
        raise RuntimeError(
            "No peer percentile data found. "
            "Run Day 18 first."
        )

    print(
        "Peer percentile rows loaded:",
        len(df),
    )

    validate_radar_data(df)

    generated_files = generate_all_radar_charts(df)

    print(
        "\nRadar charts generated:",
        len(generated_files),
    )

    print(
        "Output directory:",
        OUTPUT_DIR,
    )

    print("\nSample files:")

    for path in generated_files[:10]:
        print(" ", path.name)

    print("\nDAY 19 RADAR CHARTS COMPLETE")


if __name__ == "__main__":
    main()