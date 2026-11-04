
import pandas as pd
import pytest

from src.sentinel.quality.profiler import profile_data


def make_sample_dataframe():
    """Create a small dataset containing known quality issues."""

    records = [
        {
            "Invoice": "500001",
            "StockCode": "85048",
            "Description": "Product A",
            "Quantity": 2,
            "InvoiceDate": "2010-01-01",
            "Price": 10.0,
            "Customer ID": "13085",
            "Country": "United Kingdom",
            "source_row": 2,
            "source_sheet": "Year 2009-2010",
            "source_file": "test.xlsx",
        },
        {
            "Invoice": "C500002",
            "StockCode": "79323P",
            "Description": "Product B",
            "Quantity": -1,
            "InvoiceDate": "2010-01-02",
            "Price": 5.0,
            "Customer ID": "13086",
            "Country": "France",
            "source_row": 3,
            "source_sheet": "Year 2009-2010",
            "source_file": "test.xlsx",
        },
        {
            "Invoice": "500003",
            "StockCode": "22197",
            "Description": "Product C",
            "Quantity": -2,
            "InvoiceDate": "2010-01-03",
            "Price": 8.0,
            "Customer ID": "13087",
            "Country": "Germany",
            "source_row": 4,
            "source_sheet": "Year 2009-2010",
            "source_file": "test.xlsx",
        },
        {
            "Invoice": "500004",
            "StockCode": "22198",
            "Description": "Product D",
            "Quantity": 1,
            "InvoiceDate": "2010-01-04",
            "Price": -3.0,
            "Customer ID": "13088",
            "Country": "France",
            "source_row": 5,
            "source_sheet": "Year 2009-2010",
            "source_file": "test.xlsx",
        },
        {
            "Invoice": "500005",
            "StockCode": "22199",
            "Description": "Product E",
            "Quantity": 1,
            "InvoiceDate": "2010-01-05",
            "Price": 0.0,
            "Customer ID": "13089",
            "Country": "Germany",
            "source_row": 6,
            "source_sheet": "Year 2009-2010",
            "source_file": "test.xlsx",
        },
        {
            "Invoice": "500006",
            "StockCode": "22200",
            "Description": pd.NA,
            "Quantity": 1,
            "InvoiceDate": "2010-01-06",
            "Price": 12.0,
            "Customer ID": pd.NA,
            "Country": "France",
            "source_row": 7,
            "source_sheet": "Year 2009-2010",
            "source_file": "test.xlsx",
        },
        {
            "Invoice": "500007",
            "StockCode": "22201",
            "Description": "Product G",
            "Quantity": 1,
            "InvoiceDate": "not-a-date",
            "Price": 15.0,
            "Customer ID": "13090",
            "Country": "Germany",
            "source_row": 8,
            "source_sheet": "Year 2009-2010",
            "source_file": "test.xlsx",
        },
    ]

    # Add a duplicate business record with different source metadata.
    duplicate = records[0].copy()
    duplicate["source_row"] = 9
    records.append(duplicate)

    return pd.DataFrame(records)


def test_quality_report_contains_all_sections():
    dataframe = make_sample_dataframe()
    report = profile_data(dataframe)

    assert "completeness" in report
    assert "duplicates" in report
    assert "business_rules" in report
    assert "quality_score" in report


def test_missing_values_are_detected():
    report = profile_data(make_sample_dataframe())

    assert report["completeness"]["total_missing_values"] == 2


def test_business_duplicates_are_detected():
    report = profile_data(make_sample_dataframe())

    assert report["duplicates"]["duplicate_count"] == 1


def test_cancellations_are_classified_correctly():
    report = profile_data(make_sample_dataframe())
    rules = report["business_rules"]

    assert rules["negative_quantity_count"] == 2
    assert rules["likely_cancellation_count"] == 1
    assert rules["suspicious_negative_quantity_count"] == 1


def test_negative_and_zero_prices_are_detected():
    report = profile_data(make_sample_dataframe())
    rules = report["business_rules"]

    assert rules["negative_price_count"] == 1
    assert rules["zero_price_count"] == 1


def test_invalid_dates_are_detected():
    report = profile_data(make_sample_dataframe())
    rules = report["business_rules"]

    assert rules["invalid_date_count"] == 1


def test_missing_customer_and_description_are_soft_flags():
    report = profile_data(make_sample_dataframe())
    rules = report["business_rules"]

    assert rules["missing_customer_id_count"] == 1
    assert rules["missing_description_count"] == 1


def test_invalid_record_count_is_correct():
    report = profile_data(make_sample_dataframe())
    rules = report["business_rules"]

    # One suspicious negative quantity, one negative price,
    # and one invalid date.
    assert rules["invalid_record_count"] == 3


def test_quality_score_is_within_valid_range():
    report = profile_data(make_sample_dataframe())

    score = report["quality_score"]["overall"]

    assert 0 <= score <= 100


def test_profiler_does_not_modify_original_dataframe():
    dataframe = make_sample_dataframe()
    original = dataframe.copy(deep=True)

    profile_data(dataframe)

    pd.testing.assert_frame_equal(dataframe, original)


def test_missing_required_column_is_rejected():
    dataframe = make_sample_dataframe()
    dataframe = dataframe.drop(columns=["Invoice"])

    with pytest.raises(ValueError):
        profile_data(dataframe)
