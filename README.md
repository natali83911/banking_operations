# Banking operations

## Описание
Этот проект предназначен для анализа банковских транзакций, формирования отчетов, расчёта кешбэка по категориям, получения курсов валют и стоимости акций.
В проекте реализованы функции для фильтрации транзакций, составления топа трат, анализа выгодности кешбэка и сохранения результатов в текстовые файлы.

## Структура проекта
~~~
project_root/
│
├── src/
│    └── reports.py          # Основной модуль с функциями анализа
├── results/                 # Папка для сохранения файлов с результатами
├── tests/
│    └── test_reports.py     # Тесты для функций анализа
├── requirements.txt         # Список зависимостей
└── README.md                # Документация (вы читаете её!)
~~~
## Основные функции
1. main_info(date_time: str) -> str
Формирует JSON-ответ с приветствием, аналитикой по картам, топ-5 транзакциями, курсами валют и стоимостью акций на заданную дату.

2. analyze_cashback_categories(file_path: str, year: int, month: int) -> str
Анализирует выгоду по категориям повышенного кешбэка за выбранный месяц и год, возвращает результат в формате JSON.

3. expenses_by_category(transactions: pd.DataFrame, category: str, date: Optional[str]) -> pd.DataFrame
Возвращает траты по заданной категории за последние 3 месяца от переданной даты.

Результат автоматически сохраняется в файл results/result_reports.txt с помощью декоратора.

4. get_data_from_file(path_to_file: str) -> pd.DataFrame
Загружает Excel-файл с транзакциями и возвращает pandas DataFrame.

## Как использовать
Для установки и запуска проекта необходимо выполнить следующие шаги:

1.  **Клонируйте репозиторий:**

    ```
    git clone git@github.com:natali83911/banking_operations.git
    ```

2.  **Перейдите в папку проекта:**

    ```
    cd banking_operations
    ```

3.  **Установите зависимости с помощью Poetry:**

    ```
    poetry install
    poetry add --group lint flake8
    poetry add --group lint mypy
    poetry add --group lint black
    poetry add --group lint isort
    poetry add --group dev pytest
    poetry add python-dotenv
    poetry add pandas
    poetry add openpyxl
    
    ```

## Использование функций в коде
~~~
from config import PATH_TO_EXCEL
from src.reports import expenses_by_category, get_data_from_file
from src.services import analyze_cashback_categories
from src.views import main_info

# Получить общий отчет
print(main_info("2021-12-15 15:30:00"))

# Анализ кешбэка за март 2018
print(analyze_cashback_categories("transactions.xlsx", 2018, 3))

# Получить траты по категории "Аптеки"
df = get_data_from_file("transactions.xlsx")
result = expenses_by_category(df, "Аптеки", "2019-04-01")
print(result)
~~~
## Результаты
Все отчёты и выгрузки сохраняются в папке results/ в корне проекта.

## Тестирование
В проекте используются тесты, написанные с использованием `pytest`. Для запуска тестов выполните следующие шаги:

1. **Убедитесь, что установлены все зависимости (см. раздел "Установка").**
2. **Активируйте виртуальное окружение Poetry:**
~~~
    poetry env activate    
~~~
3. **Запустите тесты с помощью команды `pytest`:**
~~~
    pytest tests    
~~~

## Зависимости

Проект использует следующие зависимости:
*   Python 3.12.4
*   Poetry (для управления зависимостями)
*   pandas
*   openpyxl (для чтения Excel)
*   pytest (для тестов)

## Примечания
1. Для корректной работы функции анализа кешбэка в Excel-файле должны быть столбцы:
Дата операции, Категория, Сумма платежа, Кэшбэк.

2. Все функции логируют свои действия через стандартный модуль logging.


## Лицензия

Этот проект лицензирован по [лицензии MIT](LICENSE).

