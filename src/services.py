import json
import logging
import os

import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))  # Директория src/
project_root = os.path.join(current_dir, "..")  # Переходим на уровень выше (корень проекта)

# Создаем папку logs в корне проекта, если её нет
logs_dir = os.path.join(project_root, "logs")
os.makedirs(logs_dir, exist_ok=True)

# Создаем путь к файлу services.log
log_file_path = os.path.join(logs_dir, "services.log")


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def analyze_cashback_categories(file_path: str, year: int, month: int) -> str:
    """
    Анализирует выгодность категорий повышенного кешбэка.
    Возвращает JSON с анализом сколько на каждой категории можно заработать кешбэка.
    """
    logger.debug(
        "Вызвана функция analyze_cashback_categories с параметрами:"
        f"file_path={file_path}, year={year}, month={month}"
    )
    try:
        df = pd.read_excel(file_path)
        logger.debug(f"Файл {file_path} успешно прочитан")
        # Фильтруем данные по году и месяцу
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
        filtered_data = df[(df["Дата операции"].dt.year == year) & (df["Дата операции"].dt.month == month)]
        logger.debug(f"Данные отфильтрованы по году={year} и месяцу={month}")
        filtered_data = filtered_data[filtered_data["Кэшбэк"] > 0]
        logger.debug("Отфильтрованы операции с положительным кешбэком")
        filtered_data = filtered_data[filtered_data["Сумма платежа"] < 0]
        logger.debug("Отфильтрованы операции с отрицательной суммой платежа")

        # Группируем данные по категориям и суммируем суммы операций
        category_totals = filtered_data.groupby("Категория")["Сумма платежа"].sum()
        logger.debug("Суммы платежей сгруппированы по категориям")

        # Рассчитываем кешбэк для каждой категории
        category_cashbacks = abs(category_totals) // 100
        logger.debug("Рассчитан кешбэк для каждой категории")

        # Преобразуем результат в словарь
        result = category_cashbacks.to_dict()
        logger.debug(f"Результат преобразован в словарь: {result}")

        # Возвращаем JSON
        logger.debug("Результат преобразован в JSON")
        return json.dumps(result, ensure_ascii=False, indent=4)
    except FileNotFoundError:
        logger.error(f"Файл {file_path} не найден.")
        return json.dumps({}, ensure_ascii=False, indent=4)  # Возвращаем пустой JSON
    except pd.errors.EmptyDataError:
        logger.error(f"Файл {file_path} пуст.")
        return json.dumps({}, ensure_ascii=False, indent=4)  # Возвращаем пустой JSON
    except KeyError as e:
        logger.error(f"Отсутствует столбец: {e}")
        return json.dumps({}, ensure_ascii=False, indent=4)  # Возвращаем пустой JSON
    except Exception as e:
        logger.exception(f"Произошла ошибка: {e}")
        return json.dumps({}, ensure_ascii=False, indent=4)  # Возвращаем пустой JSON
