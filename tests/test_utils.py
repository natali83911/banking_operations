import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

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


@pytest.mark.parametrize(
    "input_date",
    [
        "31-12-2024 23:59:59",
        "2024-13-01 00:00:00",
        "2024-02-30 12:00:00",
        "",
        None,
    ],
)
def test_get_data_time_invalid(input_date):
    assert get_data_time(input_date) == []


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


# @patch("pandas.read_excel")
# def test_get_card_with_spend(mock_read_excel, sample_dataframe):
#
#     result = get_card_with_spend(sample_dataframe)
#     # Проверки
#     assert len(result) == 2
#     assert result[0]["last_digits"] == "1234"
#     assert result[0]["total_spent"] == -500
#     assert result[0]["cashback"] == -5
#
#     assert result[1]["last_digits"] == "5678"
#     assert result[1]["total_spent"] == -100
#     assert result[1]["cashback"] == -1
def test_get_card_with_spend_valid(sample_dataframe):
    result = get_card_with_spend(sample_dataframe)
    assert len(result) == 2
    assert result[0]["last_digits"] == "1234"
    assert result[0]["total_spent"] == -500
    assert result[1]["last_digits"] == "5678"


def test_get_card_with_spend_missing_columns(sample_dataframe):
    # Удаляем обязательный столбец
    invalid_df = sample_dataframe.drop(columns=["Сумма операции"])
    result = get_card_with_spend(invalid_df)
    assert result == []


def test_get_card_with_spend_empty_df():
    empty_df = pd.DataFrame(columns=["Номер карты", "Сумма операции", "Сумма операции с округлением"])
    result = get_card_with_spend(empty_df)
    assert result == []


def test_get_card_with_spend_invalid_dtypes():
    invalid_df = pd.DataFrame(
        {
            "Номер карты": [1234],  # Номер карты как число вместо строки
            "Сумма операции": ["-500"],  # Строка вместо числа
            "Сумма операции с округлением": [-500],
        }
    )
    result = get_card_with_spend(invalid_df)
    assert result == []


@pytest.mark.parametrize("top_n, expected", [(1, 1), (3, 3), (5, 3)])
def test_get_top_transactions(sample_dataframe, top_n, expected):
    result = get_top_transactions(sample_dataframe, top_n)
    assert len(result) == expected


def test_get_top_transactions_invalid_columns():
    invalid_df = pd.DataFrame({"Неправильный столбец": [1, 2, 3]})
    assert get_top_transactions(invalid_df, 2) == []


def test_get_top_transactions_negative_top():
    df = pd.DataFrame(
        {"Дата платежа": ["2024-01-01"], "Сумма операции": [100], "Категория": ["Транспорт"], "Описание": ["Поездка"]}
    )
    assert get_top_transactions(df, -5) == []


def test_get_top_transactions_zero_top():
    df = pd.DataFrame(
        {"Дата платежа": ["2024-01-01"], "Сумма операции": [100], "Категория": ["Транспорт"], "Описание": ["Поездка"]}
    )
    result = get_top_transactions(df, 0)
    assert len(result) == 0


@patch("requests.get")
def test_get_currency_success(mock_get, tmp_path):
    # Подготовка тестового JSON
    json_data = {"user_currencies": ["USD", "EUR"]}
    json_file = tmp_path / "test.json"
    json_file.write_text(json.dumps(json_data), encoding="utf-8")

    # Мок ответа API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"query": {"from": "USD"}, "result": 75.1234}
    mock_get.return_value = mock_response

    result = get_currency(str(json_file))
    assert len(result) == 2
    assert result[0]["currency"] == "USD"
    assert result[0]["rate"] == 75.12


def test_get_currency_file_not_found():
    result = get_currency("non_existent_file.json")
    assert result == []


def test_get_currency_invalid_json(tmp_path):
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{malformed json}", encoding="utf-8")

    result = get_currency(str(invalid_json))
    assert result == []


def test_get_currency_missing_key(tmp_path):
    json_data = {"wrong_key": ["USD"]}
    json_file = tmp_path / "test.json"
    json_file.write_text(json.dumps(json_data), encoding="utf-8")

    result = get_currency(str(json_file))
    assert result == []


@patch("requests.get")
def test_get_currency_network_error(mock_get, tmp_path):
    json_data = {"user_currencies": ["USD"]}
    json_file = tmp_path / "test.json"
    json_file.write_text(json.dumps(json_data), encoding="utf-8")

    mock_get.side_effect = requests.exceptions.ConnectionError

    result = get_currency(str(json_file))
    assert result == []


@patch("requests.get")
def test_get_stock_success(mock_get, tmp_path):
    """Тест успешного выполнения."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"price": "150.0"}  # Проверка конвертации в float
    mock_get.return_value = mock_response

    config = {"user_stocks": ["AAPL"]}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    result = get_stock(config_path)
    assert result[0]["price"] == 150.0


@patch("requests.get")
def test_get_stock_missing_price(mock_get, tmp_path):
    """Тест на отсутствие ключа 'price' в ответе API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}  # Нет ключа "price"
    mock_get.return_value = mock_response

    config = {"user_stocks": ["AAPL"]}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    result = get_stock(config_path)
    assert result == []  # Все акции пропущены из-за ошибки


def test_get_stock_file_not_found():
    """Тест на отсутствие файла."""
    result = get_stock("non_existent.json")
    assert result == []
