
import pandas as pd
import pytest

from src.sentinel import pipeline


@pytest.fixture
def mock_pipeline(monkeypatch, tmp_path):
    """Replace real processing with controlled test data."""

    dataframe = pd.DataFrame({
        "Invoice": ["500001"],
        "Quantity": [2],
        "Price": [10.0],
    })

    result = {
        "cleaned": dataframe,
        "cancellations": pd.DataFrame(),
        "quarantine": pd.DataFrame(),
        "summary": {
            "total_input_records": 1,
            "cleaned_sales_records": 1,
        },
    }

    quality_report = {
        "quality_score": {
            "overall": 98.42
        }
    }

    monkeypatch.setattr(
        pipeline, "REPORTS_DIR", tmp_path / "reports"
    )

    monkeypatch.setattr(
        pipeline, "load_workbook", lambda: dataframe
    )

    monkeypatch.setattr(
        pipeline, "profile_data", lambda df: quality_report
    )

    monkeypatch.setattr(
        pipeline, "save_quality_report", lambda report: None
    )

    monkeypatch.setattr(
        pipeline, "clean_data", lambda df: result
    )

    monkeypatch.setattr(
        pipeline,
        "save_pipeline_outputs",
        lambda output: {
            "cleaned": "cleaned_sales.csv",
            "summary": "cleaning_summary.json",
        },
    )


def test_pipeline_completes_successfully(mock_pipeline):
    summary = pipeline.run_pipeline()

    assert summary["status"] == "SUCCESS"


def test_pipeline_returns_correct_record_counts(mock_pipeline):
    summary = pipeline.run_pipeline()

    assert summary["input_records"] == 1
    assert summary["cleaned_sales"] == 1
    assert summary["cancellations"] == 0
    assert summary["quarantined_records"] == 0


def test_pipeline_returns_quality_score(mock_pipeline):
    summary = pipeline.run_pipeline()

    assert summary["quality_score"] == 98.42


def test_pipeline_returns_execution_time(mock_pipeline):
    summary = pipeline.run_pipeline()

    assert summary["execution_time_seconds"] >= 0


def test_pipeline_stops_when_ingestion_fails(
    mock_pipeline, monkeypatch
):
    def fail_ingestion():
        raise FileNotFoundError("Dataset not found")

    monkeypatch.setattr(
        pipeline, "load_workbook", fail_ingestion
    )

    with pytest.raises(FileNotFoundError):
        pipeline.run_pipeline()
