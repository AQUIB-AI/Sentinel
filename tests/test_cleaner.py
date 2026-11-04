
import pandas as pd
import pytest

from src.sentinel.processing.cleaner import clean_data


def make_sample_data():
    records = [
        ["500001", "A1", "Product A", 2, "2010-01-01", 10.0, "1001", "UK", 2],
        ["C500002", "A2", "Product B", -1, "2010-01-02", 5.0, "1002", "UK", 3],
        ["500003", "A3", "Product C", -2, "2010-01-03", 8.0, "1003", "UK", 4],
        ["500004", "A4", "Product D", 1, "2010-01-04", -3.0, "1004", "UK", 5],
        ["500005", "A5", "Product E", 1, "invalid-date", 15.0, "1005", "UK", 6],
        ["500006", "A6", "Product F", 1, "2010-01-06", 12.0, "1006", None, 7],
        ["500007", "A7", None, 1, "2010-01-07", 0.0, None, "UK", 8],
    ]

    columns = [
        "Invoice", "StockCode", "Description", "Quantity",
        "InvoiceDate", "Price", "Customer ID", "Country",
        "source_row",
    ]

    dataframe = pd.DataFrame(records, columns=columns)

    dataframe["source_sheet"] = "Test"
    dataframe["source_file"] = "test.xlsx"

    # Duplicate the first business record.
    duplicate = dataframe.iloc[[0]].copy()
    duplicate["source_row"] = 99

    return pd.concat([dataframe, duplicate], ignore_index=True)


def test_cleaning_returns_all_expected_outputs():
    result = clean_data(make_sample_data())

    assert "cleaned" in result
    assert "cancellations" in result
    assert "quarantine" in result
    assert "summary" in result


def test_duplicates_are_removed():
    result = clean_data(make_sample_data())

    assert result["summary"]["duplicates_removed"] == 1


def test_cancellations_are_separated():
    result = clean_data(make_sample_data())

    assert len(result["cancellations"]) == 1
    assert result["cancellations"].iloc[0]["Invoice"] == "C500002"


def test_invalid_records_are_quarantined():
    result = clean_data(make_sample_data())

    assert len(result["quarantine"]) == 4


def test_valid_sales_are_retained():
    result = clean_data(make_sample_data())

    assert len(result["cleaned"]) == 2


def test_zero_price_is_flagged():
    result = clean_data(make_sample_data())

    assert result["summary"]["zero_price_review_flags"] == 1


def test_missing_customer_and_description_are_flagged():
    result = clean_data(make_sample_data())

    assert result["summary"]["missing_customer_id_flags"] == 1
    assert result["summary"]["missing_description_flags"] == 1


def test_transaction_amount_is_calculated():
    result = clean_data(make_sample_data())

    sales = result["cleaned"]

    assert "total_amount" in sales.columns
    assert sales.iloc[0]["total_amount"] == 20.0


def test_original_dataframe_is_not_modified():
    dataframe = make_sample_data()
    original = dataframe.copy(deep=True)

    clean_data(dataframe)

    pd.testing.assert_frame_equal(dataframe, original)


def test_empty_dataframe_is_rejected():
    with pytest.raises(ValueError):
        clean_data(pd.DataFrame())


def test_missing_required_column_is_rejected():
    dataframe = make_sample_data().drop(columns=["Invoice"])

    with pytest.raises(ValueError):
        clean_data(dataframe)
