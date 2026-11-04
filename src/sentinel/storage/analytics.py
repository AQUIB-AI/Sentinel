
"""
Sentinel - SQL Analytics Interface

Provides reusable SQL analytics for the dashboard.
"""

import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATABASE_PATH = PROJECT_ROOT / "data" / "sentinel.db"


def execute_query(query: str) -> pd.DataFrame:
    """Execute a read-only analytics query."""

    if not DATABASE_PATH.exists():
        raise FileNotFoundError("Sentinel database not found.")

    with sqlite3.connect(DATABASE_PATH) as connection:
        return pd.read_sql_query(query, connection)


def get_sales_summary():
    return execute_query("""
        SELECT
            COUNT(DISTINCT Invoice) AS total_orders,
            COUNT(*) AS total_transactions,
            SUM(Quantity) AS total_units,
            ROUND(SUM(total_amount), 2) AS total_revenue,
            COUNT(DISTINCT "Customer ID") AS unique_customers
        FROM sales_transactions
    """)


def get_monthly_revenue():
    return execute_query("""
        SELECT
            strftime('%Y-%m', InvoiceDate) AS month,
            ROUND(SUM(total_amount), 2) AS revenue
        FROM sales_transactions
        GROUP BY month
        ORDER BY month
    """)


def get_top_products(limit=10):
    if not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("Limit must be an integer between 1 and 100.")

    return execute_query(f"""
        SELECT
            StockCode,
            MAX(Description) AS product_name,
            SUM(Quantity) AS units_sold,
            ROUND(SUM(total_amount), 2) AS revenue
        FROM sales_transactions
        GROUP BY StockCode
        ORDER BY units_sold DESC
        LIMIT {limit}
    """)


def get_country_revenue():
    return execute_query("""
        SELECT
            Country,
            ROUND(SUM(total_amount), 2) AS revenue
        FROM sales_transactions
        GROUP BY Country
        ORDER BY revenue DESC
    """)


def get_top_customers(limit=10):
    if not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("Limit must be an integer between 1 and 100.")

    return execute_query(f"""
        SELECT
            "Customer ID" AS customer_id,
            COUNT(DISTINCT Invoice) AS orders,
            ROUND(SUM(total_amount), 2) AS spending
        FROM sales_transactions
        WHERE "Customer ID" IS NOT NULL
        GROUP BY "Customer ID"
        ORDER BY spending DESC
        LIMIT {limit}
    """)


def get_cancellation_summary():
    return execute_query("""
        SELECT
            COUNT(*) AS cancellation_lines,
            COUNT(DISTINCT Invoice) AS cancelled_invoices,
            SUM(ABS(Quantity)) AS cancelled_units,
            ROUND(SUM(ABS(Quantity * Price)), 2)
                AS cancellation_value
        FROM cancellation_transactions
    """)


def get_quality_counts():
    return execute_query("""
        SELECT 'Cleaned Sales' AS category, COUNT(*) AS records
        FROM sales_transactions

        UNION ALL

        SELECT 'Cancellations', COUNT(*)
        FROM cancellation_transactions

        UNION ALL

        SELECT 'Quarantined Records', COUNT(*)
        FROM quarantined_records
    """)
