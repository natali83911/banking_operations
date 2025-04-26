import json

from config import PATH_TO_EXCEL, PATH_TO_JSON

from .utils import (get_card_with_spend, get_currency, get_data_time, get_path_and_period, get_stock,
                    get_time_for_greeting, get_top_transactions)


def main_info(date_time: str) -> str:
    """
    Функция, принимающая на вход строку с датой и временем в формате
    YYYY-MM-DD HH:MM:SS  и возвращающую JSON-ответ
    """
    # Делаем срез файла на определенный диапазон
    time_period = get_data_time(date_time)
    sorted_df = get_path_and_period(PATH_TO_EXCEL, time_period)

    # Приветствие
    greeting = get_time_for_greeting()

    # По каждой карте
    cards = get_card_with_spend(sorted_df)

    # Топ-5 транзакций по сумме платежа
    top_transactions = get_top_transactions(sorted_df, 5)

    # Курс валют
    currency_rates = get_currency(PATH_TO_JSON)

    # Стоимость акций
    stock_prices = get_stock(PATH_TO_JSON)

    data = {
        "greeting": greeting,
        "cards": cards,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }

    json_data = json.dumps(data, ensure_ascii=False, indent=4)

    return json_data
