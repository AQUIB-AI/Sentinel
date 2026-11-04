
"""
SENTINEL - DATA OBSERVABILITY DASHBOARD

Features:
1. Business performance analytics
2. Data quality monitoring
3. Monthly revenue trends
4. Product and country analytics
5. Customer analytics
6. Cancellation monitoring
7. Pipeline execution summary
8. Self-healing and retry monitoring
"""

import sys
import json
from pathlib import Path

import pandas as pd
import streamlit as st


# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT))

from src.sentinel.storage.analytics import (
    get_sales_summary,
    get_monthly_revenue,
    get_top_products,
    get_country_revenue,
    get_top_customers,
    get_cancellation_summary,
    get_quality_counts,
)


DATABASE_PATH = PROJECT_ROOT / "data" / "sentinel.db"

QUALITY_REPORT_PATH = (
    PROJECT_ROOT / "reports" / "quality_report.json"
)

CLEANING_REPORT_PATH = (
    PROJECT_ROOT / "reports" / "cleaning_summary.json"
)

LOG_PATH = PROJECT_ROOT / "reports" / "sentinel.log"


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Sentinel | Data Observability",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown(
    """
    <style>
    .main {
        background-color: #0E1117;
    }

    .block-container {
        padding-top: 2rem;
    }

    [data-testid="stMetric"] {
        background-color: #1B2431;
        border: 1px solid #303B4B;
        padding: 18px;
        border-radius: 12px;
    }

    h1, h2, h3 {
        color: #F1F5F9;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def load_json_report(path):

    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return {}


def format_currency(value):
    return f"£{value:,.2f}"


def load_recovery_logs(path):

    """
    Read Sentinel logs and identify retry,
    recovery and permanent failure events.
    """

    if not path.exists():
        return {
            "available": False,
            "retry_events": [],
            "recovery_events": [],
            "failure_events": [],
            "recent_events": [],
        }

    try:
        content = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

    except OSError:
        return {
            "available": False,
            "retry_events": [],
            "recovery_events": [],
            "failure_events": [],
            "recent_events": [],
        }

    lines = content.splitlines()

    retry_events = [
        line for line in lines
        if "Retrying in" in line
    ]

    recovery_events = [
        line for line in lines
        if "Operation recovered successfully" in line
    ]

    failure_events = [
        line for line in lines
        if (
            "Stage failed permanently" in line
            or "Operation failed after all" in line
        )
    ]

    recent_events = [
        line for line in lines
        if any(
            keyword in line
            for keyword in [
                "Executing operation",
                "Operation failed on attempt",
                "Retrying in",
                "Operation recovered successfully",
                "Stage failed permanently",
                "Operation failed after all",
            ]
        )
    ]

    return {
        "available": True,
        "retry_events": retry_events,
        "recovery_events": recovery_events,
        "failure_events": failure_events,
        "recent_events": recent_events[-20:],
    }


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("🛡️ SENTINEL")

st.sidebar.caption("Data Observability Platform")

st.sidebar.divider()

if not DATABASE_PATH.exists():

    st.error(
        "Sentinel database not found. "
        "Run the database engine first."
    )

    st.stop()


if st.sidebar.button(
    "🔄 Refresh Dashboard",
    use_container_width=True,
):

    st.cache_data.clear()
    st.rerun()


# --------------------------------------------------
# LOAD ANALYTICS
# --------------------------------------------------

@st.cache_data(ttl=60)
def load_dashboard_data():

    return {
        "summary": get_sales_summary(),
        "monthly": get_monthly_revenue(),
        "products": get_top_products(10),
        "countries": get_country_revenue(),
        "customers": get_top_customers(10),
        "cancellations": get_cancellation_summary(),
        "quality": get_quality_counts(),
    }


try:

    data = load_dashboard_data()

except Exception as error:

    st.error(f"Unable to load analytics: {error}")
    st.stop()


summary = data["summary"].iloc[0]

cancellation = data["cancellations"].iloc[0]

quality_report = load_json_report(
    QUALITY_REPORT_PATH
)

cleaning_report = load_json_report(
    CLEANING_REPORT_PATH
)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🛡️ Sentinel Data Observability")

st.caption(
    "Real-time-style monitoring and business analytics "
    "powered by Python, SQL, SQLite and Streamlit."
)

st.divider()


# --------------------------------------------------
# BUSINESS PERFORMANCE
# --------------------------------------------------

st.subheader("Business Performance")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Revenue",
    format_currency(summary["total_revenue"] or 0),
)

col2.metric(
    "Total Orders",
    f"{int(summary['total_orders']):,}",
)

col3.metric(
    "Units Sold",
    f"{int(summary['total_units']):,}",
)

col4.metric(
    "Unique Customers",
    f"{int(summary['unique_customers']):,}",
)


# --------------------------------------------------
# DATA QUALITY MONITORING
# --------------------------------------------------

st.divider()

st.subheader("Data Quality Monitoring")

score = quality_report.get(
    "quality_score", {}
).get("overall", 0)

components = quality_report.get(
    "quality_score", {}
).get("components", {})


quality_col1, quality_col2, quality_col3, quality_col4 = (
    st.columns(4)
)

quality_col1.metric(
    "Overall Quality Score",
    f"{score:.2f}%",
)

quality_col2.metric(
    "Cleaned Sales",
    f"{int(data['quality'].iloc[0]['records']):,}",
)

quality_col3.metric(
    "Cancellation Lines",
    f"{int(cancellation['cancellation_lines']):,}",
)

quarantine_rows = data["quality"].loc[
    data["quality"]["category"] == "Quarantined Records",
    "records",
]

quarantine_count = (
    int(quarantine_rows.iloc[0])
    if not quarantine_rows.empty
    else 0
)

quality_col4.metric(
    "Quarantined Records",
    f"{quarantine_count:,}",
)


if components:

    st.write("Quality score breakdown")

    component_df = pd.DataFrame(
        {
            "Quality Dimension": list(components.keys()),
            "Score": list(components.values()),
        }
    )

    st.bar_chart(
        component_df.set_index("Quality Dimension")
    )


# --------------------------------------------------
# REVENUE TRENDS
# --------------------------------------------------

st.divider()

st.subheader("Monthly Revenue Trends")

monthly = data["monthly"].copy()

if not monthly.empty:

    monthly["month"] = pd.to_datetime(
        monthly["month"]
    )

    monthly = monthly.set_index("month")

    st.line_chart(
        monthly[["revenue"]],
        x_label="Month",
        y_label="Revenue (£)",
    )

else:

    st.info("No monthly revenue data available.")


# --------------------------------------------------
# PRODUCT AND COUNTRY ANALYTICS
# --------------------------------------------------

st.divider()

left, right = st.columns(2)


with left:

    st.subheader("Top 10 Products")

    products = data["products"].copy()

    if not products.empty:

        products["product_label"] = (
            products["StockCode"].astype(str)
            + " - "
            + products["product_name"].fillna("Unknown")
        )

        st.bar_chart(
            products.set_index("product_label")[
                ["units_sold"]
            ]
        )

        st.dataframe(
            products,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info("No product data available.")


with right:

    st.subheader("Top 10 Countries by Revenue")

    countries = data["countries"].head(10).copy()

    if not countries.empty:

        st.bar_chart(
            countries.set_index("Country")[["revenue"]]
        )

        st.dataframe(
            countries,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info("No country data available.")


# --------------------------------------------------
# CUSTOMER ANALYTICS
# --------------------------------------------------

st.divider()

st.subheader("Top 10 Customers")

customers = data["customers"].copy()

if not customers.empty:

    st.dataframe(
        customers,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info("No customer data available.")


# --------------------------------------------------
# CANCELLATION ANALYTICS
# --------------------------------------------------

st.divider()

st.subheader("Cancellation Monitoring")

cancel_col1, cancel_col2, cancel_col3 = st.columns(3)

cancel_col1.metric(
    "Cancelled Invoices",
    f"{int(cancellation['cancelled_invoices']):,}",
)

cancel_col2.metric(
    "Cancelled Units",
    f"{int(cancellation['cancelled_units']):,}",
)

cancel_col3.metric(
    "Cancellation Value",
    format_currency(
        cancellation["cancellation_value"] or 0
    ),
)


# --------------------------------------------------
# SELF-HEALING MONITORING
# --------------------------------------------------

st.divider()

st.subheader("🛡️ Self-Healing Pipeline Monitoring")

recovery_data = load_recovery_logs(LOG_PATH)

if recovery_data["available"]:

    retry_count = len(
        recovery_data["retry_events"]
    )

    recovery_count = len(
        recovery_data["recovery_events"]
    )

    failure_count = len(
        recovery_data["failure_events"]
    )

    monitor_col1, monitor_col2, monitor_col3 = (
        st.columns(3)
    )

    monitor_col1.metric(
        "Retry Events",
        f"{retry_count:,}",
    )

    monitor_col2.metric(
        "Recovered Operations",
        f"{recovery_count:,}",
    )

    monitor_col3.metric(
        "Permanent Failures",
        f"{failure_count:,}",
    )

    if failure_count > 0:

        st.error(
            "Permanent pipeline failures were detected. "
            "Review the logs below."
        )

    elif recovery_count > 0:

        st.success(
            "Sentinel successfully recovered from "
            "temporary pipeline failures."
        )

    elif retry_count > 0:

        st.warning(
            "Retry activity detected. "
            "No successful recovery event is recorded yet."
        )

    else:

        st.info(
            "No retry or recovery events recorded "
            "in the current log."
        )

    with st.expander("View recent recovery logs"):

        if recovery_data["recent_events"]:

            st.code(
                "\n".join(
                    recovery_data["recent_events"]
                ),
                language="text",
            )

        else:

            st.write(
                "No retry or recovery events found."
            )

else:

    st.warning(
        "Pipeline log not found or unavailable. "
        "Run Sentinel first."
    )


# --------------------------------------------------
# PIPELINE EXECUTION SUMMARY
# --------------------------------------------------

st.divider()

st.subheader("Pipeline Execution Summary")

if cleaning_report:

    summary_col1, summary_col2, summary_col3 = (
        st.columns(3)
    )

    summary_col1.metric(
        "Input Records",
        f"{cleaning_report.get('total_input_records', 0):,}",
    )

    summary_col2.metric(
        "Duplicates Removed",
        f"{cleaning_report.get('duplicates_removed', 0):,}",
    )

    summary_col3.metric(
        "Unique Records",
        f"{cleaning_report.get('unique_records', 0):,}",
    )

else:

    st.info("Cleaning summary not found.")


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Sentinel | Built with Python, Pandas, SQL, SQLite, "
    "Apache Airflow and Streamlit."
)

st.caption(
    "Dataset: UCI Online Retail II | "
    "Historical transaction analytics."
)
