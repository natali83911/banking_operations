import json
from io import StringIO
from typing import Dict
from unittest.mock import patch

import pandas as pd
import pytest

from src.services import analyze_cashback_categories


@patch("pandas.read_excel")
@pytest.mark.parametrize(
    "year, month, expected_result",
    [
        (
            2024,
            4,
            {"Продукты": 30, "Транспорт": 5},
        ),
        (
            2024,
            5,
            {"Развлечения": 7},  # Corrected expected result
        ),
    ],
)
def test_analyze_cashback_categories(
    mock_read_excel,
    mock_file_path: str,
    mock_excel_data: str,
    year: int,
    month: int,
    expected_result: Dict,
) -> None:
    """Тест функции analyze_cashback_categories с использованием имитированных данных"""
    mock_df = pd.read_csv(StringIO(mock_excel_data))
    mock_df["Дата операции"] = pd.to_datetime(mock_df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    mock_read_excel.return_value = mock_df
    result = analyze_cashback_categories(mock_file_path, year, month)
    assert json.loads(result) == expected_result


@patch("pandas.read_excel")
@pytest.mark.parametrize(
    "scenario, expected_output",
    [
        ("file_not_found", {}),
        ("empty_file", {}),
        ("missing_columns", {}),
        ("invalid_data", {}),
    ],
)
def test_exception_handling(mock_read_excel, scenario, expected_output):
    # Arrange
    test_file = "test.xlsx"
    year = 2024
    month = 4

    if scenario == "file_not_found":
        mock_read_excel.side_effect = FileNotFoundError
    elif scenario == "empty_file":
        mock_read_excel.side_effect = pd.errors.EmptyDataError
    elif scenario == "missing_columns":
        mock_read_excel.return_value = pd.DataFrame({"Wrong_Column": [1, 2, 3]})
    elif scenario == "invalid_data":
        mock_read_excel.return_value = pd.DataFrame(
            {"Дата операции": ["invalid_date"], "Кэшбэк": [5], "Сумма платежа": [-100]}
        )

    result = analyze_cashback_categories(test_file, year, month)
    assert json.loads(result) == expected_output
    if scenario in ["file_not_found", "empty_file"]:
        mock_read_excel.assert_called_once_with(test_file)
