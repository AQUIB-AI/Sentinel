
"""
Sentinel - Unified Data Pipeline

Orchestrates:
1. Data ingestion
2. Data quality profiling
3. Quality report generation
4. Data cleaning
5. Output storage
6. Pipeline execution summary

Includes automatic retries and failure logging.
"""

import logging
import time
from pathlib import Path

from src.sentinel.ingestion.loader import load_workbook
from src.sentinel.quality.profiler import (
    profile_data,
    save_quality_report,
)
from src.sentinel.processing.cleaner import clean_data
from src.sentinel.storage.writer import save_pipeline_outputs
from src.sentinel.recovery.retry import run_with_retry


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"

LOGGER = logging.getLogger("sentinel.pipeline")

MAX_ATTEMPTS = 3
RETRY_DELAY = 2


def execute_stage(stage_name, operation):
    """
    Execute one pipeline stage with automatic retries.
    """

    LOGGER.info("Starting stage: %s", stage_name)

    try:
        result = run_with_retry(
            operation,
            max_attempts=MAX_ATTEMPTS,
            delay_seconds=RETRY_DELAY,
            backoff_multiplier=2,
        )

        LOGGER.info("Stage completed successfully: %s", stage_name)

        return result

    except Exception:
        LOGGER.exception(
            "Stage failed permanently: %s",
            stage_name,
        )
        raise


def run_pipeline():
    """Execute the complete Sentinel data pipeline."""

    start_time = time.perf_counter()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                REPORTS_DIR / "sentinel.log",
                encoding="utf-8",
            ),
        ],
        force=True,
    )

    LOGGER.info("========================================")
    LOGGER.info("SENTINEL PIPELINE STARTED")
    LOGGER.info("========================================")

    try:

        # Stage 1: Data ingestion
        LOGGER.info("STAGE 1: DATA INGESTION")

        dataframe = execute_stage(
            "Data Ingestion",
            load_workbook,
        )

        LOGGER.info(
            "Ingestion completed: %s records",
            f"{len(dataframe):,}",
        )

        # Stage 2: Data quality profiling
        LOGGER.info("STAGE 2: DATA QUALITY PROFILING")

        quality_report = execute_stage(
            "Data Quality Profiling",
            lambda: profile_data(dataframe),
        )

        # Stage 3: Save quality report
        LOGGER.info("STAGE 3: QUALITY REPORT GENERATION")

        execute_stage(
            "Quality Report Generation",
            lambda: save_quality_report(quality_report),
        )

        quality_score = quality_report["quality_score"]["overall"]

        LOGGER.info(
            "Data quality score: %.2f%%",
            quality_score,
        )

        # Stage 4: Data cleaning
        LOGGER.info("STAGE 4: DATA CLEANING")

        result = execute_stage(
            "Data Cleaning",
            lambda: clean_data(dataframe),
        )

        LOGGER.info(
            "Cleaned sales: %s",
            f"{len(result['cleaned']):,}",
        )

        LOGGER.info(
            "Cancellations: %s",
            f"{len(result['cancellations']):,}",
        )

        LOGGER.info(
            "Quarantined records: %s",
            f"{len(result['quarantine']):,}",
        )

        # Stage 5: Save pipeline outputs
        LOGGER.info("STAGE 5: DATA STORAGE")

        saved_files = execute_stage(
            "Data Storage",
            lambda: save_pipeline_outputs(result),
        )

        for name, path in saved_files.items():
            LOGGER.info("%s saved: %s", name, path)

        # Stage 6: Final execution summary
        execution_time = time.perf_counter() - start_time

        summary = {
            "status": "SUCCESS",
            "input_records": len(dataframe),
            "quality_score": quality_score,
            "cleaned_sales": len(result["cleaned"]),
            "cancellations": len(result["cancellations"]),
            "quarantined_records": len(result["quarantine"]),
            "execution_time_seconds": round(execution_time, 2),
            "max_retry_attempts": MAX_ATTEMPTS,
        }

        LOGGER.info("========================================")
        LOGGER.info("SENTINEL PIPELINE COMPLETED")
        LOGGER.info("========================================")

        for key, value in summary.items():
            LOGGER.info("%s: %s", key, value)

        return summary

    except Exception:
        LOGGER.exception(
            "SENTINEL PIPELINE FAILED"
        )
        raise


if __name__ == "__main__":
    run_pipeline()
