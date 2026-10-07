"""
Sprint 2 - Ratio Edge Case Cross-Check

Compares calculated ROE / ROCE from financial_ratios
against source values from the companies table.

Anomalies:
    Difference > 5 percentage points

Output:
    output/ratio_edge_cases.log
"""

import sqlite3
import os


DB_PATH = "db/nifty100.db"
OUTPUT_PATH = "output/ratio_edge_cases.log"


def safe_float(value):
    """Convert value to float safely."""
    if value is None:
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def categorize_difference(
    calculated,
    source,
    company_id,
    metric,
):
    """
    Categorize a large difference between calculated
    and source financial ratios.

    The classification is heuristic and should be
    reviewed manually.
    """

    if calculated is None or source is None:
        return "Data source issue"

    # Very large difference can indicate source/version
    # mismatch rather than a simple rounding difference.
    difference = abs(calculated - source)

    if difference > 20:
        return "Version difference"

    # Financial companies and source-specific formulas
    # can legitimately produce different values.
    if metric == "ROCE":
        return "Formula discrepancy"

    if metric == "ROE":
        return "Formula discrepancy"

    return "Data source issue"


def main():

    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            r.company_id,
            r.year,

            r.return_on_equity_pct AS calculated_roe,
            r.return_on_capital_employed_pct AS calculated_roce,

            c.roe_percentage AS source_roe,
            c.roce_percentage AS source_roce

        FROM financial_ratios r

        LEFT JOIN companies c
            ON r.company_id = c.company_id

        ORDER BY
            r.company_id,
            r.year
    """

    rows = conn.execute(query).fetchall()

    columns = [
        "company_id",
        "year",
        "calculated_roe",
        "calculated_roce",
        "source_roe",
        "source_roce",
    ]

    conn.close()

    os.makedirs("output", exist_ok=True)

    anomalies = []

    for row in rows:

        data = dict(zip(columns, row))

        company_id = data["company_id"]
        year = data["year"]

        calculated_roe = safe_float(data["calculated_roe"])
        calculated_roce = safe_float(data["calculated_roce"])

        source_roe = safe_float(data["source_roe"])
        source_roce = safe_float(data["source_roce"])

        # --------------------------------------------------
        # ROE comparison
        # --------------------------------------------------

        if calculated_roe is not None and source_roe is not None:

            roe_difference = abs(calculated_roe - source_roe)

            if roe_difference > 5:

                category = categorize_difference(
                    calculated_roe,
                    source_roe,
                    company_id,
                    "ROE",
                )

                anomalies.append(
                    {
                        "company_id": company_id,
                        "year": year,
                        "metric": "ROE",
                        "calculated": calculated_roe,
                        "source": source_roe,
                        "difference": roe_difference,
                        "category": category,
                    }
                )

        # --------------------------------------------------
        # ROCE comparison
        # --------------------------------------------------

        if calculated_roce is not None and source_roce is not None:

            roce_difference = abs(calculated_roce - source_roce)

            if roce_difference > 5:

                category = categorize_difference(
                    calculated_roce,
                    source_roce,
                    company_id,
                    "ROCE",
                )

                anomalies.append(
                    {
                        "company_id": company_id,
                        "year": year,
                        "metric": "ROCE",
                        "calculated": calculated_roce,
                        "source": source_roce,
                        "difference": roce_difference,
                        "category": category,
                    }
                )

    # ------------------------------------------------------
    # Write log
    # ------------------------------------------------------

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:

        f.write("=" * 80 + "\n")
        f.write("SPRINT 2 - RATIO EDGE CASE LOG\n")
        f.write("=" * 80 + "\n\n")

        f.write(
            "Comparison threshold: absolute difference > 5 percentage points\n\n"
        )

        f.write(
            f"Total ratio rows checked: {len(rows)}\n"
        )

        f.write(
            f"Total anomalies found: {len(anomalies)}\n\n"
        )

        if not anomalies:

            f.write("NO ANOMALIES FOUND.\n")

        else:

            for i, anomaly in enumerate(anomalies, start=1):

                f.write("-" * 80 + "\n")
                f.write(f"Anomaly #{i}\n")
                f.write("-" * 80 + "\n")

                f.write(
                    f"Company: {anomaly['company_id']}\n"
                )

                f.write(
                    f"Year: {anomaly['year']}\n"
                )

                f.write(
                    f"Metric: {anomaly['metric']}\n"
                )

                f.write(
                    f"Calculated value: "
                    f"{anomaly['calculated']:.4f}\n"
                )

                f.write(
                    f"Source value: "
                    f"{anomaly['source']:.4f}\n"
                )

                f.write(
                    f"Absolute difference: "
                    f"{anomaly['difference']:.4f}\n"
                )

                f.write(
                    f"Category: {anomaly['category']}\n"
                )

                f.write(
                    "Review status: DOCUMENTATION REQUIRED\n\n"
                )

        # --------------------------------------------------
        # Summary
        # --------------------------------------------------

        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write("ANOMALY SUMMARY\n")
        f.write("=" * 80 + "\n")

        category_counts = {}

        for anomaly in anomalies:

            category = anomaly["category"]

            category_counts[category] = (
                category_counts.get(category, 0) + 1
            )

        if category_counts:

            for category, count in sorted(
                category_counts.items()
            ):

                f.write(
                    f"{category}: {count}\n"
                )

        else:

            f.write("No anomalies.\n")

    print("=" * 60)
    print("RATIO EDGE CASE CROSS-CHECK COMPLETE")
    print("=" * 60)
    print(f"Rows checked: {len(rows)}")
    print(f"Anomalies found: {len(anomalies)}")
    print(f"Saved to: {os.path.abspath(OUTPUT_PATH)}")

    if anomalies:

        print()
        print("Breakdown:")

        for category, count in sorted(
            category_counts.items()
        ):

            print(f"{category}: {count}")


if __name__ == "__main__":
    main()