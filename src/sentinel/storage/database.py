
"""
Sentinel - SQLite Database Engine

Responsibilities:
1. Load processed CSV datasets.
2. Create a SQLite database.
3. Store sales, cancellations and quarantine records.
4. Create indexes for faster SQL queries.
5. Verify database record counts.
"""

import sqlite3
from pathlib import Path

import pandas as pd


# Project directory
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
QUARANTINE_DIR = DATA_DIR / "quarantine"

# Database location
DATABASE_PATH = DATA_DIR / "sentinel.db"


# CSV files and their corresponding SQL tables
DATASETS = {
    "sales_transactions": (
        PROCESSED_DIR / "cleaned_sales.csv"
    ),
    "cancellation_transactions": (
        PROCESSED_DIR / "cancellations.csv"
    ),
    "quarantined_records": (
        QUARANTINE_DIR / "quarantined_records.csv"
    ),
}


# Identifiers must remain strings, not numeric values.
TEXT_COLUMNS = [
    "Invoice",
    "StockCode",
    "Customer ID",
]


def load_dataset(file_path: Path) -> pd.DataFrame:
    """Read a CSV dataset while preserving identifiers."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    dataframe = pd.read_csv(
        file_path,
        dtype={
            column: "string"
            for column in TEXT_COLUMNS
        },
        low_memory=False,
    )

    return dataframe


def create_indexes(connection: sqlite3.Connection):
    """Create database indexes for faster queries."""

    indexes = [
        """
        CREATE INDEX IF NOT EXISTS idx_sales_invoice
        ON sales_transactions (Invoice)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_sales_customer
        ON sales_transactions ("Customer ID")
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_sales_stock
        ON sales_transactions (StockCode)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_sales_date
        ON sales_transactions (InvoiceDate)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_cancellation_invoice
        ON cancellation_transactions (Invoice)
        """,
    ]

    for statement in indexes:
        connection.execute(statement)


def load_database() -> dict:
    """Load all Sentinel datasets into SQLite."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("\n====================================")
    print(" SENTINEL DATABASE ENGINE")
    print("====================================")

    # Load and validate all CSV files first.
    datasets = {}

    for table_name, file_path in DATASETS.items():

        print(f"\nReading: {file_path.name}")

        datasets[table_name] = load_dataset(file_path)

        print(
            f"Records loaded: "
            f"{len(datasets[table_name]):,}"
        )

    # Connect to SQLite.
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        results = {}

        # Insert datasets into their SQL tables.
        for table_name, dataframe in datasets.items():

            print(f"\nCreating SQL table: {table_name}")

            dataframe.to_sql(
                name=table_name,
                con=connection,
                if_exists="replace",
                index=False,
            )

            results[table_name] = len(dataframe)

            print(
                f"Inserted {len(dataframe):,} records"
            )

        # Create indexes.
        print("\nCreating database indexes...")

        create_indexes(connection)

        connection.commit()

        # Verify database contents.
        print("\n====================================")
        print(" DATABASE VERIFICATION")
        print("====================================")

        for table_name in DATASETS:

            count = connection.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
            ).fetchone()[0]

            print(f"{table_name}: {count:,}")

            if count != results[table_name]:
                raise RuntimeError(
                    f"Record count mismatch in {table_name}"
                )

        print(f"\nDatabase saved at: {DATABASE_PATH}")

        print("\nDatabase loading completed successfully.")

        return results

    finally:
        connection.close()


if __name__ == "__main__":
    load_database()
