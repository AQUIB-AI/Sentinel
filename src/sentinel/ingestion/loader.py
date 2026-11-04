
"""
Sentinel - Data Ingestion Engine

Responsibilities:
1. Validate source file.
2. Validate workbook sheets.
3. Validate required columns.
4. Load yearly transaction data.
5. Combine records.
6. Preserve source metadata.
"""

import logging
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# 1. Project configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "online_retail_II.xlsx"
)

EXPECTED_SHEETS = [
    "Year 2009-2010",
    "Year 2010-2011",
]

REQUIRED_COLUMNS = [
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer ID",
    "Country",
]

LOGGER = logging.getLogger(__name__)


# --------------------------------------------------
# 2. File validation
# --------------------------------------------------

def validate_source_file(file_path: Path) -> None:
    """Verify that the source workbook exists."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Source dataset not found: {file_path}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"Source path is not a file: {file_path}"
        )

    if file_path.suffix.lower() != ".xlsx":
        raise ValueError(
            "Expected an Excel .xlsx file."
        )


# --------------------------------------------------
# 3. Schema validation
# --------------------------------------------------

def validate_schema(
    dataframe: pd.DataFrame,
    sheet_name: str
) -> None:
    """Verify that all required columns exist."""

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Schema validation failed for {sheet_name}. "
            f"Missing columns: {missing_columns}"
        )


# --------------------------------------------------
# 4. Workbook ingestion
# --------------------------------------------------

def load_workbook(
    file_path: Path = DEFAULT_DATA_PATH
) -> pd.DataFrame:
    """
    Load all expected sheets and combine them.

    Original records are preserved.
    No cleaning or deletion is performed.
    """

    file_path = Path(file_path)

    LOGGER.info("Starting data ingestion: %s", file_path)

    # Validate source file.
    validate_source_file(file_path)

    frames = []

    with pd.ExcelFile(
        file_path,
        engine="openpyxl"
    ) as workbook:

        available_sheets = workbook.sheet_names

        # Validate expected worksheets.
        missing_sheets = [
            sheet
            for sheet in EXPECTED_SHEETS
            if sheet not in available_sheets
        ]

        if missing_sheets:
            raise ValueError(
                f"Missing expected worksheets: {missing_sheets}"
            )

        LOGGER.info(
            "Workbook contains %d worksheets.",
            len(available_sheets)
        )

        # Read each expected worksheet.
        for sheet_name in EXPECTED_SHEETS:

            LOGGER.info(
                "Reading worksheet: %s",
                sheet_name
            )

            dataframe = pd.read_excel(
                workbook,
                sheet_name=sheet_name,
                dtype={
                    "Invoice": "string",
                    "StockCode": "string",
                    "Customer ID": "string",
                }
            )

            # Validate column structure.
            validate_schema(
                dataframe,
                sheet_name
            )

            # Preserve original Excel row numbers.
            dataframe["source_row"] = range(
                2,
                len(dataframe) + 2
            )

            # Preserve original worksheet name.
            dataframe["source_sheet"] = sheet_name

            # Preserve original source filename.
            dataframe["source_file"] = file_path.name

            LOGGER.info(
                "Loaded %s records from %s",
                len(dataframe),
                sheet_name
            )

            frames.append(dataframe)

            del dataframe

    # Combine both worksheets.
    combined_data = pd.concat(
        frames,
        ignore_index=True
    )

    LOGGER.info(
        "Ingestion completed successfully. Total records: %d",
        len(combined_data)
    )

    return combined_data


# --------------------------------------------------
# 5. Execute ingestion independently
# --------------------------------------------------

def main():

    reports_directory = PROJECT_ROOT / "reports"

    reports_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                reports_directory / "sentinel.log",
                encoding="utf-8"
            ),
        ],
        force=True
    )

    LOGGER.info("SENTINEL INGESTION ENGINE STARTED")

    dataframe = load_workbook()

    print("\n====================================")
    print(" SENTINEL INGESTION SUMMARY")
    print("====================================")

    print(f"Total records: {len(dataframe):,}")
    print(f"Total columns: {len(dataframe.columns)}")

    print("\nRecords per source worksheet:")

    print(
        dataframe["source_sheet"].value_counts()
    )

    print("\nCombined dataset preview:")

    print(dataframe.head())

    print("\nData types:")

    print(dataframe.dtypes)

    print("\nIngestion completed successfully.")


if __name__ == "__main__":
    main()
