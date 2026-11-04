"""
Sentinel - Apache Airflow DAG
Orchestrates the existing Sentinel data pipeline.
"""

from datetime import datetime
from pathlib import Path
import subprocess

from airflow.sdk import dag, task


PROJECT_DIR = Path.home() / "Desktop" / "Sentinel"
SENTINEL_PYTHON = PROJECT_DIR / "venv" / "bin" / "python"


@dag(
    dag_id="sentinel_data_pipeline",
    description="Automated Sentinel data quality and cleaning pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["sentinel", "data-engineering", "quality"],
)
def sentinel_data_pipeline():

    @task
    def run_sentinel_pipeline():
        subprocess.run(
            [
                str(SENTINEL_PYTHON),
                "-m",
                "src.sentinel.pipeline",
            ],
            cwd=str(PROJECT_DIR),
            check=True,
        )

    run_sentinel_pipeline()


sentinel_data_pipeline()
