
import json
from pathlib import Path

import pandas as pd
import pytest

from src.sentinel.storage import writer


@pytest.fixture
def sample_result():
    """Create sample pipeline outputs for storage testing."""

    return {
        "cleaned": pd.DataFrame({
            "Invoice": ["500001"],
            "Quantity": [2],
            "Price": [10.0],
        }),
        "cancellations": pd.DataFrame({
            "Invoice": ["C500002"],
            "Quantity": [-1],
            "Price": [5.0],
        }),
        "quarantine": pd.DataFrame({
            "Invoice": ["500003"],
            "quarantine_reason": ["Negative price"],
        }),
        "summary": {
            "total_input_records": 3,
            "cleaned_sales_records": 1,
            "cancellation_records": 1,
            "quarantined_records": 1,
        },
    }


def configure_test_directories(tmp_path, monkeypatch):
    """Redirect storage outputs to temporary test directories."""

    monkeypatch.setattr(
        writer, "PROCESSED_DIR", tmp_path / "processed"
    )
    monkeypatch.setattr(
        writer, "QUARANTINE_DIR", tmp_path / "quarantine"
    )
    monkeypatch.setattr(
        writer, "REPORTS_DIR", tmp_path / "reports"
    )


def test_storage_creates_all_output_files(
    tmp_path, monkeypatch, sample_result
):
    configure_test_directories(tmp_path, monkeypatch)

    paths = writer.save_pipeline_outputs(sample_result)

    assert set(paths.keys()) == {
        "cleaned",
        "cancellations",
        "quarantine",
        "summary",
    }

    for path in paths.values():
        assert Path(path).exists()


def test_cleaned_csv_contains_expected_records(
    tmp_path, monkeypatch, sample_result
):
    configure_test_directories(tmp_path, monkeypatch)

    paths = writer.save_pipeline_outputs(sample_result)

    saved = pd.read_csv(
        paths["cleaned"],
        dtype={"Invoice": "string"},
    )

    assert len(saved) == 1
    assert saved.iloc[0]["Invoice"] == "500001"
    assert saved.iloc[0]["Quantity"] == 2
    assert saved.iloc[0]["Price"] == 10.0


def test_cancellation_csv_contains_expected_records(
    tmp_path, monkeypatch, sample_result
):
    configure_test_directories(tmp_path, monkeypatch)

    paths = writer.save_pipeline_outputs(sample_result)

    saved = pd.read_csv(
        paths["cancellations"],
        dtype={"Invoice": "string"},
    )

    assert len(saved) == 1
    assert saved.iloc[0]["Invoice"] == "C500002"


def test_quarantine_csv_contains_expected_records(
    tmp_path, monkeypatch, sample_result
):
    configure_test_directories(tmp_path, monkeypatch)

    paths = writer.save_pipeline_outputs(sample_result)

    saved = pd.read_csv(
        paths["quarantine"],
        dtype={"Invoice": "string"},
    )

    assert len(saved) == 1
    assert saved.iloc[0]["Invoice"] == "500003"
    assert saved.iloc[0]["quarantine_reason"] == "Negative price"


def test_summary_json_is_saved_correctly(
    tmp_path, monkeypatch, sample_result
):
    configure_test_directories(tmp_path, monkeypatch)

    paths = writer.save_pipeline_outputs(sample_result)

    with open(paths["summary"], encoding="utf-8") as file:
        summary = json.load(file)

    assert summary["total_input_records"] == 3
    assert summary["cleaned_sales_records"] == 1


def test_invalid_input_is_rejected():
    with pytest.raises(TypeError):
        writer.save_pipeline_outputs("invalid")


def test_missing_output_is_rejected():
    with pytest.raises(ValueError):
        writer.save_pipeline_outputs({
            "cleaned": pd.DataFrame(),
        })
