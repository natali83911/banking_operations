import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.utils import (get_card_with_spend, get_currency, get_data_time, get_path_and_period, get_stock,
                       get_time_for_greeting, get_top_transactions)


@pytest.mark.parametrize(
    "mock_hour, expected",
    [
        (5, "Доброе утро"),
        (11, "Доброе утро"),
        (12, "Добрый день"),
        (17, "Добрый день"),
        (18, "Добрый вечер"),
        (21, "Добрый вечер"),
        (22, "Доброй ночи"),
        (4, "Доброй ночи"),
        (0, "Доброй ночи"),
    ],
)
@patch("src.utils.datetime.datetime")
def test_get_time_for_greeting(mock_datetime, mock_hour, expected):
    mock_datetime_instance = MagicMock()
    mock_datetime_instance.hour = mock_hour
    mock_datetime.now.return_value = mock_datetime_instance
    assert get_time_for_greeting() == expected


@pytest.mark.parametrize(
    "input_date, expected",
    [
        ("2024-12-31 23:59:59", ["01.12.2024 00:00:00", "31.12.2024 23:59:59"]),
        ("2024-02-29 12:00:00", ["01.02.2024 00:00:00", "29.02.2024 12:00:00"]),
        ("2023-01-01 00:00:00", ["01.01.2023 00:00:00", "01.01.2023 00:00:00"]),
    ],
)
def test_get_data_time(input_date, expected):
    assert get_data_time(input_date) == expected


@patch("pandas.read_excel")
@pytest.mark.parametrize(
    "period, expected_dates, expected_length",
    [
        (["01.04.2024 00:00:00", "15.04.2024 23:59:59"], ["01.04.2024", "15.04.2024"], 2),
        (["01.01.1900 00:00:00", "02.01.1900 00:00:00"], [], 0),
        (["30.04.2024 00:00:00", "30.04.2024 23:59:59"], ["30.04.2024"], 1),
    ],
)
def test_get_path_and_period(mock_read, sample_excel_file, period, expected_dates, expected_length):
    #  Генерируем DataFrame внутри теста, перед мокингом
    data = {"Дата операции": ["01.04.2024", "15.04.2024", "30.04.2024"], "Сумма операции": [-100, 200, -50]}
    real_df = pd.DataFrame(data)
    real_df["Дата операции"] = pd.to_datetime(real_df["Дата операции"], dayfirst=True)

    # Настраиваем mock, чтобы он возвращал подготовленный DataFrame
    mock_read.return_value = real_df

    # Вызываем функцию
    result = get_path_and_period(sample_excel_file, period)

    # Проверки
    assert len(result) == expected_length

    if expected_length > 0:
        # Преобразуем даты в строки для сравнения
        result_dates = result["Дата операции"].dt.strftime("%d.%m.%Y").tolist()
        assert result_dates == expected_dates


@patch("pandas.read_excel")
def test_get_card_with_spend(mock_read_excel, sample_dataframe):

    result = get_card_with_spend(sample_dataframe)
    # Проверки
    assert len(result) == 2
    assert result[0]["last_digits"] == "1234"
    assert result[0]["total_spent"] == -500
    assert result[0]["cashback"] == -5

    assert result[1]["last_digits"] == "5678"
    assert result[1]["total_spent"] == -100
    assert result[1]["cashback"] == -1


@pytest.mark.parametrize("top_n, expected", [(1, 1), (3, 3), (5, 3)])
def test_get_top_transactions(sample_dataframe, top_n, expected):
    result = get_top_transactions(sample_dataframe, top_n)
    assert len(result) == expected


@patch("requests.get")
def test_get_currency(mock_get, tmp_path):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"query": {"from": "USD"}, "result": 75.50}
    mock_get.return_value = mock_response

    config = {"user_currencies": ["USD"]}
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)

    result = get_currency(config_path)
    assert result[0]["rate"] == 75.50


@patch("requests.get")
def test_get_stock(mock_get, tmp_path):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"price": 150.0}
    mock_get.return_value = mock_response

    config = {"user_stocks": ["AAPL"]}
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)

    result = get_stock(config_path)
    assert result[0]["price"] == 150.0
