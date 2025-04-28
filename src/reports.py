import datetime
import logging
import os
from functools import wraps
from typing import Optional

import pandas as pd

from config import MAIN_DIR

current_dir = os.path.dirname(os.path.abspath(__file__))  # Директория src/
project_root = os.path.join(current_dir, "..")  # Переходим на уровень выше (корень проекта)

# Создаем папку logs в корне проекта, если её нет
logs_dir = os.path.join(project_root, "logs")
os.makedirs(logs_dir, exist_ok=True)

# Создаем путь к файлу reports.log
log_file_path = os.path.join(logs_dir, "reports.log")


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def save_result_to_txt(filename: str):
    """
    Декоратор, который сохраняет результат функции в текстовый файл с именем filename,
    создавая файл в папке 'results' в корне проекта.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            results_dir = os.path.join(MAIN_DIR, "results")
            os.makedirs(results_dir, exist_ok=True)
            full_path = os.path.join(results_dir, filename)

            logger.debug(f"Вызов функции {func.__name__} с args={args} kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                with open(full_path, "w", encoding="utf-8") as f:
                    if hasattr(result, "to_string"):
                        f.write(result.to_string())
                    else:
                        f.write(str(result))
                logger.debug(f"Результат функции {func.__name__} успешно сохранён в файл '{full_path}'")
                return result
            except Exception as e:
                logger.error(f"Ошибка при выполнении функции {func.__name__} или записи в файл: {e}", exc_info=True)
                raise

        return wrapper

    return decorator


def get_data_from_file(path_to_file: str) -> pd.DataFrame:
    """
    Читает Excel-файл и возвращает DataFrame.
    """
    logger.debug(f"Чтение Excel-файла: {path_to_file}")
    df = pd.read_excel(path_to_file)
    return df


@save_result_to_txt("result_reports.txt")
def expenses_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
    Возвращает траты по заданной категории за последние 3 месяца от переданной даты.
    Если дата не передана, используется текущая дата.
    """
    logger.debug(f"Начало обработки расходов по категории '{category}' с датой '{date}'")
    if date is None:
        current_date = datetime.datetime.now()
        logger.debug(f"Дата не указана, используется текущая дата: {current_date}")
    else:
        try:
            current_date = pd.to_datetime(date)
            logger.debug(f"Дата преобразована: {current_date}")
        except Exception as e:
            logger.error(f"Неверный формат даты: {date}", exc_info=True)
            raise ValueError(f"Неверный формат даты: {date}") from e
    if not pd.api.types.is_datetime64_any_dtype(transactions["Дата операции"]):
        transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], dayfirst=True, errors="coerce")
        logger.debug("Столбец 'Дата операции' преобразован в datetime")
    three_months_ago = current_date - pd.DateOffset(months=3)
    filtered = transactions[
        (transactions["Категория"] == category)
        & (transactions["Дата операции"] >= three_months_ago)
        & (transactions["Дата операции"] <= current_date)
        & (transactions["Сумма платежа"] < 0)
    ].copy()

    filtered["Израсходовано"] = filtered["Сумма платежа"].abs()
    logger.debug(f"Найдено {len(filtered)} записей по категории '{category}' за последние 3 месяца")

    return filtered.reset_index(drop=True)
