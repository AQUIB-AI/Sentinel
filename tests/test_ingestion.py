
import pandas as pd
import pytest

from pathlib import Path

from src.sentinel.ingestion.loader import (
    load_workbook,
    EXPECTED_SHEETS,
    REQUIRED_COLUMNS,
)


def create_test_workbook(path: Path):
    """Create a small temporary Excel workbook."""

    sample_data = pd.DataFrame({
        "Invoice": ["489434", "489435"],
        "StockCode": ["85048", "79323P"],
        "Description": ["Product A", "Product B"],
        "Quantity": [2, 3],
        "InvoiceDate": [
            "2010-01-01",
            "2010-01-02"
        ],
        "Price": [10.0, 20.0],
        "Customer ID": ["13085", "13086"],
        "Country": ["United Kingdom", "France"],
    })

    with pd.ExcelWriter(
        path,
        engine="openpyxl"
    ) as writer:

        for sheet in EXPECTED_SHEETS:

            sample_data.to_excel(
                writer,
                sheet_name=sheet,
                index=False
            )


def test_successful_ingestion(tmp_path):

    file_path = tmp_path / "test_data.xlsx"

    create_test_workbook(file_path)

    dataframe = load_workbook(file_path)

    assert len(dataframe) == 4

    assert len(dataframe.columns) == 11

    assert "source_sheet" in dataframe.columns

    assert "source_row" in dataframe.columns

    assert "source_file" in dataframe.columns

    assert set(dataframe["source_sheet"]) == set(
        EXPECTED_SHEETS
    )


def test_missing_file():

    with pytest.raises(FileNotFoundError):

        load_workbook(
            Path("missing_file.xlsx")
        )


def test_missing_required_column(tmp_path):

    file_path = tmp_path / "invalid_data.xlsx"

    invalid_data = pd.DataFrame({
        "Invoice": ["489434"],
        "StockCode": ["85048"],
    })

    with pd.ExcelWriter(
        file_path,
        engine="openpyxl"
    ) as writer:

        for sheet in EXPECTED_SHEETS:

            invalid_data.to_excel(
                writer,
                sheet_name=sheet,
                index=False
            )

    with pytest.raises(ValueError):

        load_workbook(file_path)


def test_missing_expected_sheet(tmp_path):

    file_path = tmp_path / "incomplete_data.xlsx"

    sample_data = pd.DataFrame({
        column: ["sample"]
        for column in REQUIRED_COLUMNS
    })

    sample_data.to_excel(
        file_path,
        sheet_name=EXPECTED_SHEETS[0],
        index=False
    )

    with pytest.raises(ValueError):

        load_workbook(file_path)
