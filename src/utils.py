import datetime
import json
import logging
import os
from datetime import datetime as dt_class
from typing import Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv
from pandas import DataFrame

current_dir = os.path.dirname(os.path.abspath(__file__))  # Директория src/
project_root = os.path.join(current_dir, "..")  # Переходим на уровень выше (корень проекта)

# Создаем папку logs в корне проекта, если её нет
logs_dir = os.path.join(project_root, "logs")
os.makedirs(logs_dir, exist_ok=True)

# Создаем путь к файлу utils.log
log_file_path = os.path.join(logs_dir, "utils.log")


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

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
    logger.debug("Вызвана функция get_time_for_greeting")
    user_date_time_hour = datetime.datetime.now().hour
    if 5 <= user_date_time_hour < 12:
        logger.debug("Возвращено: Доброе утро")
        return "Доброе утро"
    elif 12 <= user_date_time_hour < 18:
        logger.debug("Возвращено: Добрый день")
        return "Добрый день"
    elif 18 <= user_date_time_hour < 22:
        logger.debug("Возвращено: Добрый вечер")
        return "Добрый вечер"
    else:
        logger.debug("Возвращено: Доброй ночи")
        return "Доброй ночи"


def get_data_time(date_time: str, date_format: str = "%Y-%m-%d %H:%M:%S") -> List[str]:
    """Функция форматирует дату, принятую на вход"""
    logger.debug(f"Вызвана функция get_data_time с параметрами: date_time={date_time}," f" date_format={date_format}")
    try:
        dt = dt_class.strptime(date_time, date_format)
        start_of_month = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        result = [start_of_month.strftime("%d.%m.%Y %H:%M:%S"), dt.strftime("%d.%m.%Y %H:%M:%S")]
        logger.debug(f"Результат форматирования: {result}")
        return result
    except Exception as e:
        logger.exception(f"Ошибка форматирования даты: {e}")
        return []


def get_path_and_period(path_to_file: str, period_date: list) -> pd.DataFrame:
    """
    Функция принимает путь к Excel-файлу и список дат,
    возвращает таблицу в заданном периоде
    """
    logger.debug(
        f"Вызвана функция get_path_and_period с параметрами:"
        f" path_to_file={path_to_file}, period_date={period_date}"
    )
    try:
        df = pd.read_excel(path_to_file, sheet_name="Отчет по операциям")

        # Преобразуем даты в pd.Timestamp для корректного сравнения
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)

        start_date = pd.to_datetime(period_date[0], format="%d.%m.%Y %H:%M:%S")
        end_date = pd.to_datetime(period_date[1], format="%d.%m.%Y %H:%M:%S")

        filtered_df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]
        logger.debug(f"Количество строк после фильтрации: {len(filtered_df)}")

        result = filtered_df.sort_values(by="Дата операции", ascending=True)
        logger.debug("Таблица успешно отфильтрована и отсортирована")
        return result
    except FileNotFoundError:
        logger.error(f"Файл не найден: {path_to_file}")
        raise ValueError("Файл не найден")


def get_card_with_spend(sorted_df: DataFrame) -> List[Dict]:
    """Функция принимает DataFrame и возвращает список карт с расходами"""
    logger.debug("Вызвана функция get_card_with_spend")

    card_spent_transactions = []

    try:
        # Проверка наличия необходимых столбцов
        required_columns = ["Номер карты", "Сумма операции", "Сумма операции с округлением"]
        if not all(col in sorted_df.columns for col in required_columns):
            logger.warning(f"Отсутствуют обязательные столбцы: {required_columns}")
            raise ValueError("Отсутствуют обязательные столбцы")

        card_sorted = sorted_df[required_columns]
        logger.debug("Отобраны необходимые столбцы из DataFrame")

        for i, row in card_sorted.iterrows():
            if row["Сумма операции"] < 0:
                last_digits = str(row["Номер карты"]).replace("*", "")
                total_spent = row["Сумма операции с округлением"]
                cashback = total_spent // 100
                row_data = {"last_digits": last_digits, "total_spent": total_spent, "cashback": cashback}
                card_spent_transactions.append(row_data)
                logger.debug(f"Обработано {len(card_spent_transactions)} транзакций")

    except Exception as e:
        logger.exception(f"Ошибка обработки данных: {e}")
        return []

    return card_spent_transactions


def get_top_transactions(sorted_df: DataFrame, get_top: int) -> List[Dict]:
    """Функция принимает DataFrame и возвращает get_top топ-транзакций по сумме платежа"""
    logger.debug(f"Вызвана функция get_top_transactions с параметрами: sorted_df, get_top={get_top}")
    top_pay_transactions = []

    try:
        # Проверка наличия обязательных столбцов
        required_columns = ["Дата платежа", "Сумма операции", "Категория", "Описание"]
        if not all(col in sorted_df.columns for col in required_columns):
            logger.warning(f"Отсутствуют обязательные столбцы: {required_columns}")
            raise ValueError("Отсутствуют обязательные столбцы")

        # Проверка типа параметра get_top
        if not isinstance(get_top, int) or get_top < 0:
            logger.error(f"Некорректный параметр get_top: {get_top}")
            raise ValueError("Параметр get_top должен быть положительным целым числом")

        # Сортировка и выбор топ-N транзакций
        sorted_pay_df = sorted_df.sort_values(by="Сумма операции", ascending=False)
        top_transactions = sorted_pay_df.head(get_top)
        logger.debug(f"Выбрано топ-{get_top} транзакций")

        # Форматирование данных
        top_transactions_sorted = top_transactions[required_columns]

        for i, row in top_transactions_sorted.iterrows():
            transaction = {
                "date": str(row["Дата платежа"]),
                "amount": str(row["Сумма операции"]),
                "category": str(row["Категория"]),
                "description": str(row["Описание"]),
            }
            top_pay_transactions.append(transaction)
            logger.debug(f"Сформировано {len(top_pay_transactions)} топ-транзакций")

    except Exception as e:
        logger.exception(f"Ошибка обработки транзакций: {e}")
        return []

    return top_pay_transactions


def get_currency(path_to_json: str) -> List[Dict]:
    """Функция принимает на вход path_to_json и вщзвращает курс валют"""
    logger.debug(f"Вызвана функция get_currency с параметром: path_to_json={path_to_json}")

    currency_rates = []

    try:
        # Чтение JSON-файла
        with open(path_to_json, "r", encoding="utf-8") as file:
            data = json.load(file)
        logger.debug(f"Файл {path_to_json} успешно прочитан")

        # Проверка наличия ключа "user_currencies"
        if "user_currencies" not in data:
            logger.warning("Ключ 'user_currencies' отсутствует в JSON")
            raise KeyError("Ключ 'user_currencies' отсутствует в JSON")

        # Обработка валют
        for currency in data["user_currencies"]:
            try:
                logger.debug(f"Обработка валюты: {currency}")
                # Сетевой запрос
                params = {"amount": 1, "from": currency, "to": "RUB"}
                headers = {"apikey": API_KEY_1}
                response = requests.get(URL_1, headers=headers, params=params, timeout=10)

                # Проверка статуса ответа
                response.raise_for_status()  # Выбросит HTTPError при статусе 4xx/5xx

                result = response.json()
                logger.debug(f"Результат запроса API: {result}")

                # Проверка структуры ответа
                if "query" not in result or "result" not in result:
                    logger.warning("Некорректная структура ответа API")
                    raise ValueError("Некорректная структура ответа API")

                currency_code = result["query"]["from"]
                currency_amount = round(result["result"], 2)
                currency_rates.append({"currency": currency_code, "rate": currency_amount})
                logger.debug(f"Курс валюты {currency_code}: {currency_amount}")

            except requests.exceptions.RequestException as e:
                logger.exception(f"Ошибка при обработке валюты {currency}: {e}")
                continue

    except FileNotFoundError:
        logger.error(f"Файл {path_to_json} не найден")
        return []
    except json.JSONDecodeError:
        logger.error(f"Ошибка декодирования JSON в файле {path_to_json}")
        return []
    except KeyError as e:
        logger.error(f"Ошибка в структуре JSON: {e}")
        return []
    except Exception as e:
        logger.exception(f"Неизвестная ошибка: {e}")
        return []
    logger.debug(f"Возвращаемые курсы валют: {currency_rates}")
    return currency_rates


def get_stock(path_to_json: str) -> List[Dict]:
    """Функция принимает на вход path_to_json и возвращает курс валют"""
    logger.debug(f"Вызвана функция get_stock с параметром: path_to_json={path_to_json}")

    stock_rates = []

    try:
        # Чтение файла
        with open(path_to_json, "r", encoding="utf-8") as file:
            data = json.load(file)
        logger.debug(f"Файл {path_to_json} успешно прочитан")

        # Проверка наличия ключа
        if "user_stocks" not in data:
            logger.warning("Ключ 'user_stocks' отсутствует в JSON")
            raise KeyError("Ключ 'user_stocks' отсутствует в JSON")

        # Обработка акций
        for symbol in data["user_stocks"]:
            try:
                logger.debug(f"Обработка акции: {symbol}")
                params = {"symbol": symbol, "apikey": API_KEY_2}
                response = requests.get(URL_2, params=params, timeout=10)
                response.raise_for_status()
                stock_data = response.json()
                logger.debug(f"Результат запроса API: {stock_data}")

                if "price" not in stock_data:
                    logger.warning("Ключ 'price' отсутствует в ответе API")
                    raise ValueError("Ключ 'price' отсутствует в ответе API")

                stock_rates.append({"stock": symbol, "price": float(stock_data["price"])})
                logger.debug(f"Цена акции {symbol}: {stock_data['price']}")

            except requests.exceptions.RequestException as e:
                logger.exception(f"Ошибка при обработке акции {symbol}: {e}")
                continue

    except FileNotFoundError:
        logger.error(f"Файл {path_to_json} не найден")
        return []
    except json.JSONDecodeError:
        logger.error(f"Ошибка декодирования JSON в файле {path_to_json}")
        return []
    except KeyError as e:
        logger.error(f"Ошибка в структуре JSON: {e}")
        return []
    except Exception as e:
        logger.exception(f"Неизвестная ошибка: {e}")
        return []

    logger.debug(f"Возвращаемые данные об акциях: {stock_rates}")
    return stock_rates
