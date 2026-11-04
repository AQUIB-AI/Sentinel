
-- ============================================================
-- SENTINEL: BUSINESS INTELLIGENCE & SQL ANALYTICS
-- Database: data/sentinel.db
-- ============================================================


-- REPORT 1: OVERALL SALES PERFORMANCE
-- Total revenue, orders, quantities and customers.

SELECT
    COUNT(DISTINCT Invoice) AS total_orders,
    COUNT(*) AS total_transactions,
    SUM(Quantity) AS total_units_sold,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    COUNT(DISTINCT "Customer ID") AS unique_customers,
    ROUND(AVG(total_amount), 2) AS average_line_value

FROM sales_transactions;


-- ============================================================
-- REPORT 2: MONTHLY REVENUE ANALYSIS
-- Identify monthly revenue and sales trends.

SELECT
    strftime('%Y-%m', InvoiceDate) AS sales_month,
    COUNT(DISTINCT Invoice) AS total_orders,
    SUM(Quantity) AS units_sold,
    ROUND(SUM(total_amount), 2) AS monthly_revenue

FROM sales_transactions

GROUP BY strftime('%Y-%m', InvoiceDate)

ORDER BY sales_month;


-- ============================================================
-- REPORT 3: TOP 10 BEST-SELLING PRODUCTS
-- Rank products by quantity sold and revenue.

SELECT
    StockCode,
    MAX(Description) AS product_name,
    SUM(Quantity) AS units_sold,
    COUNT(DISTINCT Invoice) AS total_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue

FROM sales_transactions

GROUP BY StockCode

ORDER BY units_sold DESC

LIMIT 10;


-- ============================================================
-- REPORT 4: COUNTRY-WISE REVENUE
-- Identify the strongest geographic markets.

SELECT
    Country,
    COUNT(DISTINCT Invoice) AS total_orders,
    COUNT(DISTINCT "Customer ID") AS unique_customers,
    SUM(Quantity) AS units_sold,
    ROUND(SUM(total_amount), 2) AS total_revenue

FROM sales_transactions

GROUP BY Country

ORDER BY total_revenue DESC

LIMIT 10;


-- ============================================================
-- REPORT 5: TOP 10 CUSTOMERS
-- Identify customers based on total spending.

SELECT
    "Customer ID" AS customer_id,
    COUNT(DISTINCT Invoice) AS total_orders,
    SUM(Quantity) AS total_units_purchased,
    ROUND(SUM(total_amount), 2) AS customer_revenue

FROM sales_transactions

WHERE "Customer ID" IS NOT NULL

GROUP BY "Customer ID"

ORDER BY customer_revenue DESC

LIMIT 10;


-- ============================================================
-- REPORT 6: CANCELLATION ANALYSIS
-- Understand cancellation volume and financial impact.

SELECT
    COUNT(*) AS cancellation_lines,
    COUNT(DISTINCT Invoice) AS cancelled_invoices,
    SUM(ABS(Quantity)) AS cancelled_units,
    ROUND(
        SUM(ABS(Quantity * Price)), 2
    ) AS cancellation_value

FROM cancellation_transactions;


-- ============================================================
-- REPORT 7: MONTHLY CANCELLATION TRENDS

SELECT
    strftime('%Y-%m', InvoiceDate) AS cancellation_month,
    COUNT(DISTINCT Invoice) AS cancelled_invoices,
    SUM(ABS(Quantity)) AS cancelled_units,
    ROUND(
        SUM(ABS(Quantity * Price)), 2
    ) AS cancellation_value

FROM cancellation_transactions

GROUP BY strftime('%Y-%m', InvoiceDate)

ORDER BY cancellation_month;


-- ============================================================
-- REPORT 8: DATA QUALITY SUMMARY
-- Quantify the records separated by Sentinel.

SELECT
    'Cleaned Sales' AS record_category,
    COUNT(*) AS record_count
FROM sales_transactions

UNION ALL

SELECT
    'Cancellations',
    COUNT(*)
FROM cancellation_transactions

UNION ALL

SELECT
    'Quarantined Records',
    COUNT(*)
FROM quarantined_records;


-- ============================================================
-- END OF SENTINEL ANALYTICS
-- ============================================================
