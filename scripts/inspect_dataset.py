
"""
Sentinel - Dataset Inspection Utility

Purpose:
Inspect the original UCI Online Retail II Excel workbook
before performing any data cleaning or transformation.
"""

from pathlib import Path

import pandas as pd


# --------------------------------------------------
# 1. Define project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "online_retail_II.xlsx"
)


# --------------------------------------------------
# 2. Validate input file
# --------------------------------------------------

def validate_dataset_file():
    """Check whether the source Excel file exists."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}\n"
            "Place online_retail_II.xlsx inside data/raw/"
        )

    print(f"Dataset found: {DATA_PATH}")
    print(
        f"File size: "
        f"{DATA_PATH.stat().st_size / (1024 * 1024):.2f} MB"
    )


# --------------------------------------------------
# 3. Inspect each Excel sheet
# --------------------------------------------------

def inspect_dataset():
    """Inspect workbook sheets and their data quality."""

    validate_dataset_file()

    print("\n====================================")
    print(" SENTINEL DATASET INSPECTION")
    print("====================================")

    # Open the workbook and identify its sheets.
    workbook = pd.ExcelFile(
        DATA_PATH,
        engine="openpyxl"
    )

    print("\nAvailable sheets:")

    for sheet in workbook.sheet_names:
        print(f"- {sheet}")

    # Inspect each sheet separately.
    for sheet_name in workbook.sheet_names:

        print("\n" + "=" * 50)
        print(f"SHEET: {sheet_name}")
        print("=" * 50)

        df = pd.read_excel(
            workbook,
            sheet_name=sheet_name
        )

        # Basic dataset dimensions.
        print("\n1. Dataset dimensions")
        print(f"Rows: {len(df):,}")
        print(f"Columns: {len(df.columns)}")

        # Column information.
        print("\n2. Column names")
        print(df.columns.tolist())

        # Data types.
        print("\n3. Data types")
        print(df.dtypes)

        # Preview.
        print("\n4. First five records")
        print(df.head())

        # Missing values.
        print("\n5. Missing values")

        missing_counts = df.isnull().sum()

        missing_report = pd.DataFrame({
            "missing_count": missing_counts,
            "missing_percentage": (
                missing_counts / len(df) * 100
            ).round(2)
        })

        print(
            missing_report.sort_values(
                by="missing_count",
                ascending=False
            )
        )

        # Duplicate records.
        print("\n6. Exact duplicate records")
        print(f"Duplicates: {df.duplicated().sum():,}")

        # Numeric statistics.
        print("\n7. Numeric column statistics")
        print(df.describe().to_string())

        # Business-rule checks.
        print("\n8. Potential business-rule violations")

        for column in df.select_dtypes(
            include="number"
        ).columns:

            negative_count = (df[column] < 0).sum()

            zero_count = (df[column] == 0).sum()

            print(
                f"{column}: "
                f"negative={negative_count:,}, "
                f"zero={zero_count:,}"
            )

        # Approximate DataFrame memory usage.
        memory_mb = (
            df.memory_usage(deep=True).sum()
            / (1024 * 1024)
        )

        print(
            f"\n9. DataFrame memory usage: "
            f"{memory_mb:.2f} MB"
        )

        # Release this sheet before reading the next one.
        del df

    workbook.close()

    print("\n====================================")
    print(" INSPECTION COMPLETED")
    print("====================================")


# --------------------------------------------------
# 4. Execute inspection
# --------------------------------------------------

if __name__ == "__main__":
    inspect_dataset()
