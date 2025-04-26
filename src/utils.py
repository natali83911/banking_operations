import datetime
import json
import os
from datetime import datetime as dt_class
from typing import Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()
API_KEY_1 = os.getenv("API_KEY_1")
API_KEY_2 = os.getenv("API_KEY_2")


URL_1 = "https://api.apilayer.com/exchangerates_data/convert"

URL_2 = "https://api.twelvedata.com/price"


def get_time_for_greeting() -> str:
    """
    Функция возвращает  «Доброе утро» / «Добрый день» / «Добрый вечер» / «Доброй ночи»
    в зависимости от текущего времени
    """
    user_date_time_hour = datetime.datetime.now().hour
    if 5 <= user_date_time_hour < 12:
        return "Доброе утро"
    elif 12 <= user_date_time_hour < 18:
        return "Добрый день"
    elif 18 <= user_date_time_hour < 22:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_data_time(date_time: str, date_format: str = "%Y-%m-%d %H:%M:%S") -> List[str]:
    """Функция преобразует форматирует дату, принятую на вход"""
    dt = dt_class.strptime(date_time, date_format)
    start_of_month = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return [start_of_month.strftime("%d.%m.%Y %H:%M:%S"), dt.strftime("%d.%m.%Y %H:%M:%S")]


def get_path_and_period(path_to_file: str, period_date: list) -> pd.DataFrame:
    """
    Функция принимает путь к Excel-файлу и список дат,
    возвращает таблицу в заданном периоде
    """
    try:
        df = pd.read_excel(path_to_file, sheet_name="Отчет по операциям")

        # Преобразуем даты в pd.Timestamp для корректного сравнения
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)

        start_date = pd.to_datetime(period_date[0], format="%d.%m.%Y %H:%M:%S")
        end_date = pd.to_datetime(period_date[1], format="%d.%m.%Y %H:%M:%S")

        filtered_df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]

        return filtered_df.sort_values(by="Дата операции", ascending=True)
    except FileNotFoundError:
        raise ValueError("Файл не найден")


def get_card_with_spend(sorted_df: DataFrame) -> List[Dict]:
    """Функция принимает DataFrame и возвращает список карт с расходами"""

    card_spent_transactions = []
    card_sorted = sorted_df[["Номер карты", "Сумма операции", "Сумма операции с округлением"]]
    for i, row in card_sorted.iterrows():
        if row["Сумма операции"] < 0:
            last_digits = str(row["Номер карты"]).replace("*", "")
            total_spent = row["Сумма операции с округлением"]
            cashback = total_spent // 100
            row_data = {"last_digits": last_digits, "total_spent": total_spent, "cashback": cashback}
            card_spent_transactions.append(row_data)

    return card_spent_transactions


def get_top_transactions(sorted_df: DataFrame, get_top: int) -> List[Dict]:
    """Функция принимает DataFrame и возвращает get_top топ-транзакций по сумме платежа"""
    top_pay_transactions = []
    sorted_pay_df = sorted_df.sort_values(by="Сумма операции", ascending=False)
    top_transactions = sorted_pay_df.head(get_top)
    top_transactions_sorted = top_transactions[["Дата платежа", "Сумма операции", "Категория", "Описание"]]

    for i, row in top_transactions_sorted.iterrows():
        transaction = {
            "date": f'{row["Дата платежа"]}',
            "amount": f'{row["Сумма операции"]}',
            "category": f'{row["Категория"]}',
            "description": f'{row["Описание"]}',
        }
        top_pay_transactions.append(transaction)

    return top_pay_transactions


def get_currency(path_to_json: str) -> List[Dict]:
    """Функция принимает на вход path_to_json и вщзвращает курс валют"""

    currency_rates = []

    with open(path_to_json, "r", encoding="utf-8") as file:
        data = json.load(file)
        currencies = data["user_currencies"]

        for currency in currencies:
            params = {"amount": 1, "from": currency, "to": "RUB"}
            headers = {"apikey": API_KEY_1}
            response = requests.get(URL_1, headers=headers, data=params)
            status_code = response.status_code

            if status_code == 200:
                result = response.json()
                currency_code_response = result["query"]["from"]
                currency_amount = round(result["result"], 2)
                currency_rates.append({"currency": currency_code_response, "rate": currency_amount})
                print(currency_rates)
        return currency_rates


def get_stock(path_to_json: str) -> List[Dict]:
    """Функция принимает на вход path_to_json и возвращает курс валют"""

    stock_rates = []

    with open(path_to_json, "r", encoding="utf-8") as file:
        data = json.load(file)
        stocks = data["user_stocks"]

        for stock in stocks:
            symbol = stock
            params = {"symbol": symbol, "apikey": API_KEY_2}
            response = requests.get(URL_2, params=params)
            status_code = response.status_code

            if status_code == 200:
                data = response.json()
                stock_rates.append({"stock": symbol, "price": float(data["price"])})

    return stock_rates
