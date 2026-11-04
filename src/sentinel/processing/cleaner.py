
"""
Sentinel - Data Cleaning and Transformation Engine

Responsibilities:
1. Validate input schema.
2. Normalize text fields.
3. Remove duplicate business records.
4. Identify legitimate cancellations.
5. Quarantine invalid transactions.
6. Preserve incomplete but usable records with quality flags.
7. Calculate transaction values.
"""

from pathlib import Path
import pandas as pd


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

CRITICAL_COLUMNS = [
    "Invoice",
    "StockCode",
    "InvoiceDate",
    "Country",
]


def clean_data(dataframe: pd.DataFrame) -> dict:
    """
    Clean a transaction DataFrame without modifying the original.

    Returns:
        Dictionary containing:
        - cleaned: valid sales transactions
        - cancellations: identified cancellation transactions
        - quarantine: invalid transactions
        - summary: processing statistics
    """

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if dataframe.empty:
        raise ValueError("Input DataFrame is empty.")

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    original = dataframe.copy(deep=True)
    total_input = len(original)

    # Step 1: Normalize text fields.
    text_columns = [
        "Invoice",
        "StockCode",
        "Description",
        "Customer ID",
        "Country",
    ]

    for column in text_columns:
        original[column] = original[column].astype("string").str.strip()

        original[column] = original[column].replace("", pd.NA)

    # Step 2: Convert numeric fields safely.
    original["Quantity"] = pd.to_numeric(
        original["Quantity"], errors="coerce"
    )

    original["Price"] = pd.to_numeric(
        original["Price"], errors="coerce"
    )

    # Step 3: Convert invoice dates.
    original["InvoiceDate"] = pd.to_datetime(
        original["InvoiceDate"], errors="coerce"
    )

    # Step 4: Remove duplicate business records.
    # Source metadata is deliberately excluded.
    deduplicated = original.drop_duplicates(
        subset=REQUIRED_COLUMNS,
        keep="first",
    ).copy()

    duplicates_removed = total_input - len(deduplicated)

    # Step 5: Identify cancellation transactions.
    is_cancellation = (
        deduplicated["Invoice"].str.startswith("C", na=False)
        & deduplicated["Quantity"].lt(0)
    )

    cancellations = deduplicated.loc[is_cancellation].copy()

    remaining = deduplicated.loc[~is_cancellation].copy()

    # Step 6: Identify invalid records.
    missing_critical = remaining[CRITICAL_COLUMNS].isna().any(axis=1)

    invalid_quantity = remaining["Quantity"].isna()

    invalid_price = (
        remaining["Price"].isna()
        | remaining["Price"].lt(0)
    )

    invalid_date = remaining["InvoiceDate"].isna()

    suspicious_negative_quantity = remaining["Quantity"].lt(0)

    quarantine_mask = (
        missing_critical
        | invalid_quantity
        | invalid_price
        | invalid_date
        | suspicious_negative_quantity
    )

    quarantine = remaining.loc[quarantine_mask].copy()

    # Add a reason for each quarantined record.
    def get_quarantine_reason(row):
        reasons = []

        if any(pd.isna(row[column]) for column in CRITICAL_COLUMNS):
            reasons.append("Missing critical field")

        if pd.isna(row["Quantity"]):
            reasons.append("Invalid quantity")

        elif row["Quantity"] < 0:
            reasons.append("Suspicious negative quantity")

        if pd.isna(row["Price"]):
            reasons.append("Invalid price")

        elif row["Price"] < 0:
            reasons.append("Negative price")

        if pd.isna(row["InvoiceDate"]):
            reasons.append("Invalid invoice date")

        return "; ".join(reasons)

    if not quarantine.empty:
        quarantine["quarantine_reason"] = quarantine.apply(
            get_quarantine_reason, axis=1
        )

    # Step 7: Keep valid sales transactions.
    cleaned = remaining.loc[~quarantine_mask].copy()

    # Step 8: Add useful quality flags.
    cleaned["missing_customer_id"] = (
        cleaned["Customer ID"].isna()
    )

    cleaned["missing_description"] = (
        cleaned["Description"].isna()
    )

    cleaned["requires_price_review"] = (
        cleaned["Price"] == 0
    )

    # Step 9: Calculate transaction value.
    cleaned["total_amount"] = (
        cleaned["Quantity"] * cleaned["Price"]
    )

    # Step 10: Add transaction classification.
    cleaned["transaction_type"] = "sale"

    summary = {
        "total_input_records": total_input,
        "duplicates_removed": duplicates_removed,
        "unique_records": len(deduplicated),
        "cancellation_records": len(cancellations),
        "quarantined_records": len(quarantine),
        "cleaned_sales_records": len(cleaned),
        "missing_customer_id_flags": int(
            cleaned["missing_customer_id"].sum()
        ),
        "missing_description_flags": int(
            cleaned["missing_description"].sum()
        ),
        "zero_price_review_flags": int(
            cleaned["requires_price_review"].sum()
        ),
    }

    return {
        "cleaned": cleaned.reset_index(drop=True),
        "cancellations": cancellations.reset_index(drop=True),
        "quarantine": quarantine.reset_index(drop=True),
        "summary": summary,
    }


def main():
    from src.sentinel.ingestion.loader import load_workbook

    print("Loading source dataset...")
    dataframe = load_workbook()

    print("Starting Sentinel cleaning engine...")
    result = clean_data(dataframe)

    print("\n====================================")
    print(" SENTINEL CLEANING SUMMARY")
    print("====================================")

    for key, value in result["summary"].items():
        print(f"{key.replace('_', ' ').title()}: {value:,}")

    print("\nCleaned data preview:")
    print(result["cleaned"].head())

    print("\nCancellation preview:")
    print(result["cancellations"].head())

    print("\nQuarantine preview:")
    print(result["quarantine"].head())


if __name__ == "__main__":
    main()
