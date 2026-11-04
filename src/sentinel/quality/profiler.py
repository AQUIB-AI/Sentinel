
"""
Sentinel - Data Quality Profiler

Responsibilities:
1. Measure data completeness.
2. Detect duplicate transactions.
3. Validate the expected schema.
4. Identify business-rule violations.
5. Distinguish cancellations from suspicious transactions.
6. Calculate an overall data quality score.

This module never modifies the input DataFrame.
"""

import json
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# 1. Project configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

REPORT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "quality_report.json"
)

REQUIRED_COLUMNS = [
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer ID",
    "Country",
]

# Fields that must be present for a usable transaction.
CRITICAL_COLUMNS = [
    "Invoice",
    "StockCode",
    "InvoiceDate",
    "Country",
]

# Quality score weights.
QUALITY_WEIGHTS = {
    "completeness": 0.40,
    "uniqueness": 0.20,
    "validity": 0.30,
    "schema": 0.10,
}


# --------------------------------------------------
# 2. Schema validation
# --------------------------------------------------

def validate_schema(dataframe: pd.DataFrame) -> dict:
    """
    Check whether all expected business columns exist.
    """

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    unexpected_columns = [
        column
        for column in dataframe.columns
        if column not in REQUIRED_COLUMNS
        and column not in [
            "source_row",
            "source_sheet",
            "source_file",
        ]
    ]

    return {
        "valid": len(missing_columns) == 0,
        "required_columns": REQUIRED_COLUMNS,
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
    }


# --------------------------------------------------
# 3. Completeness profiling
# --------------------------------------------------

def profile_completeness(
    dataframe: pd.DataFrame
) -> dict:
    """
    Calculate missing values and their percentages.
    """

    missing_counts = dataframe.isnull().sum()

    total_cells = (
        len(dataframe) * len(dataframe.columns)
    )

    total_missing = int(missing_counts.sum())

    if total_cells == 0:
        completeness_score = 100.0
    else:
        completeness_score = (
            1 - total_missing / total_cells
        ) * 100

    column_report = {}

    for column in dataframe.columns:

        missing_count = int(
            missing_counts[column]
        )

        missing_percentage = (
            missing_count / len(dataframe) * 100
            if len(dataframe) > 0
            else 0.0
        )

        column_report[column] = {
            "missing_count": missing_count,
            "missing_percentage": round(
                missing_percentage,
                2
            ),
        }

    return {
        "total_missing_values": total_missing,
        "total_cells": int(total_cells),
        "completeness_score": round(
            completeness_score,
            2
        ),
        "columns": column_report,
    }


# --------------------------------------------------
# 4. Duplicate detection
# --------------------------------------------------

def profile_duplicates(
    dataframe: pd.DataFrame
) -> dict:
    """
    Identify exact duplicate business records.

    Source metadata is excluded because it is
    pipeline metadata, not part of the original
    business transaction.
    """

    available_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column in dataframe.columns
    ]

    if not available_columns:
        raise ValueError(
            "No business columns available for "
            "duplicate detection."
        )

    duplicate_mask = dataframe.duplicated(
        subset=available_columns,
        keep="first"
    )

    duplicate_count = int(
        duplicate_mask.sum()
    )

    total_rows = len(dataframe)

    duplicate_percentage = (
        duplicate_count / total_rows * 100
        if total_rows > 0
        else 0.0
    )

    uniqueness_score = (
        100 - duplicate_percentage
    )

    return {
        "duplicate_count": duplicate_count,
        "duplicate_percentage": round(
            duplicate_percentage,
            2
        ),
        "unique_record_count": (
            total_rows - duplicate_count
        ),
        "uniqueness_score": round(
            uniqueness_score,
            2
        ),
    }


# --------------------------------------------------
# 5. Business-rule validation
# --------------------------------------------------

def profile_business_rules(
    dataframe: pd.DataFrame
) -> dict:
    """
    Identify suspicious transactions.

    Negative quantities on invoices beginning
    with C are classified as likely cancellations.
    """

    required = [
        "Invoice",
        "Quantity",
        "InvoiceDate",
        "Price",
        "Customer ID",
        "Description",
        "StockCode",
        "Country",
    ]

    missing_columns = [
        column
        for column in required
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Cannot validate business rules. "
            f"Missing columns: {missing_columns}"
        )

    invoice = dataframe["Invoice"].astype("string")

    # Negative quantities.
    negative_quantity_mask = (
        dataframe["Quantity"] < 0
    )

    # C-prefixed invoices commonly represent
    # cancellations in this dataset.
    cancellation_mask = (
        invoice.str.startswith("C", na=False)
        & negative_quantity_mask
    )

    # Negative quantities without cancellation prefix.
    suspicious_quantity_mask = (
        negative_quantity_mask
        & ~cancellation_mask
    )

    # Price checks.
    negative_price_mask = (
        dataframe["Price"] < 0
    )

    zero_price_mask = (
        dataframe["Price"] == 0
    )

    # Date checks.
    invalid_date_mask = (
        pd.to_datetime(
            dataframe["InvoiceDate"],
            errors="coerce"
        ).isna()
    )

    # Critical missing fields.
    missing_critical_mask = (
        dataframe[CRITICAL_COLUMNS]
        .isnull()
        .any(axis=1)
    )

    # Missing descriptive fields.
    missing_customer_mask = (
        dataframe["Customer ID"].isnull()
    )

    missing_description_mask = (
        dataframe["Description"].isnull()
    )

    # Combine hard validity failures without
    # double-counting rows that have multiple issues.
    invalid_record_mask = (
        missing_critical_mask
        | invalid_date_mask
        | negative_price_mask
        | suspicious_quantity_mask
    )

    invalid_record_count = int(
        invalid_record_mask.sum()
    )

    total_rows = len(dataframe)

    validity_score = (
        100 * (
            1 - invalid_record_count / total_rows
        )
        if total_rows > 0
        else 100.0
    )

    return {
        "negative_quantity_count": int(
            negative_quantity_mask.sum()
        ),

        "likely_cancellation_count": int(
            cancellation_mask.sum()
        ),

        "suspicious_negative_quantity_count": int(
            suspicious_quantity_mask.sum()
        ),

        "negative_price_count": int(
            negative_price_mask.sum()
        ),

        "zero_price_count": int(
            zero_price_mask.sum()
        ),

        "invalid_date_count": int(
            invalid_date_mask.sum()
        ),

        "missing_critical_record_count": int(
            missing_critical_mask.sum()
        ),

        "missing_customer_id_count": int(
            missing_customer_mask.sum()
        ),

        "missing_description_count": int(
            missing_description_mask.sum()
        ),

        "invalid_record_count": invalid_record_count,

        "validity_score": round(
            validity_score,
            2
        ),
    }


# --------------------------------------------------
# 6. Overall data quality score
# --------------------------------------------------

def calculate_quality_score(
    completeness_score: float,
    uniqueness_score: float,
    validity_score: float,
    schema_score: float,
) -> float:
    """
    Calculate a weighted data quality score.

    All component scores range from 0 to 100.
    """

    score = (
        completeness_score
        * QUALITY_WEIGHTS["completeness"]

        + uniqueness_score
        * QUALITY_WEIGHTS["uniqueness"]

        + validity_score
        * QUALITY_WEIGHTS["validity"]

        + schema_score
        * QUALITY_WEIGHTS["schema"]
    )

    return round(score, 2)


# --------------------------------------------------
# 7. Complete quality profiling
# --------------------------------------------------

def profile_data(
    dataframe: pd.DataFrame
) -> dict:
    """
    Execute all quality checks and return a report.

    The original DataFrame remains unchanged.
    """

    if dataframe.empty:
        raise ValueError(
            "Cannot profile an empty DataFrame."
        )

    schema_report = validate_schema(
        dataframe
    )

    if not schema_report["valid"]:
        raise ValueError(
            "Schema validation failed: "
            f"{schema_report['missing_columns']}"
        )

    completeness_report = profile_completeness(
        dataframe
    )

    duplicate_report = profile_duplicates(
        dataframe
    )

    business_report = profile_business_rules(
        dataframe
    )

    schema_score = (
        100.0 if schema_report["valid"] else 0.0
    )

    overall_score = calculate_quality_score(
        completeness_report["completeness_score"],
        duplicate_report["uniqueness_score"],
        business_report["validity_score"],
        schema_score,
    )

    return {
        "dataset": {
            "total_rows": len(dataframe),
            "total_columns": len(dataframe.columns),
        },

        "schema": schema_report,

        "completeness": completeness_report,

        "duplicates": duplicate_report,

        "business_rules": business_report,

        "quality_score": {
            "overall": overall_score,
            "components": {
                "completeness": (
                    completeness_report[
                        "completeness_score"
                    ]
                ),
                "uniqueness": (
                    duplicate_report[
                        "uniqueness_score"
                    ]
                ),
                "validity": (
                    business_report[
                        "validity_score"
                    ]
                ),
                "schema": schema_score,
            },
            "weights": QUALITY_WEIGHTS,
        },
    }


# --------------------------------------------------
# 8. Save quality report
# --------------------------------------------------

def save_quality_report(
    report: dict,
    output_path: Path = REPORT_PATH
) -> None:
    """
    Save the quality report as JSON.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4
        )


# --------------------------------------------------
# 9. Human-readable summary
# --------------------------------------------------

def print_quality_summary(report: dict) -> None:
    """Display the quality report in Terminal."""

    print("\n====================================")
    print(" SENTINEL DATA QUALITY REPORT")
    print("====================================")

    print(
        f"Total records: "
        f"{report['dataset']['total_rows']:,}"
    )

    print(
        f"Total columns: "
        f"{report['dataset']['total_columns']}"
    )

    print("\nQUALITY COMPONENTS")

    for name, score in (
        report["quality_score"]["components"].items()
    ):
        print(f"{name.title()}: {score:.2f}/100")

    print(
        f"\nOVERALL QUALITY SCORE: "
        f"{report['quality_score']['overall']}/100"
    )

    print("\nCOMPLETENESS")
    print(
        "Missing values:",
        report["completeness"]["total_missing_values"]
    )

    print("\nDUPLICATES")
    print(
        "Duplicate records:",
        report["duplicates"]["duplicate_count"]
    )

    print("\nBUSINESS RULES")

    for key, value in (
        report["business_rules"].items()
    ):
        if key.endswith("_count"):
            print(f"{key}: {value:,}")

    print("\nSchema valid:", report["schema"]["valid"])


# --------------------------------------------------
# 10. Execute independently
# --------------------------------------------------

if __name__ == "__main__":

    from src.sentinel.ingestion.loader import load_workbook

    print("Loading source dataset...")

    data = load_workbook()

    print("\nStarting quality profiling...")

    quality_report = profile_data(data)

    save_quality_report(quality_report)

    print_quality_summary(quality_report)

    print(
        f"\nReport saved to: {REPORT_PATH}"
    )
