import pandas as pd
import pytest
from pathlib import Path


@pytest.fixture
def sample_excel_file(tmp_path):
    data = {"Дата операции": ["01.04.2024", "15.04.2024", "30.04.2024"], "Сумма операции": [-100, 200, -50]}
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    path = tmp_path / "test.xlsx"
    df.to_excel(path, sheet_name="Отчет по операциям", index=False)
    return path


@pytest.fixture
def sample_dataframe():
    data = {
        # Для get_top_transactions
        "Дата платежа": ["2024-04-01", "2024-04-15", "2024-04-30"],
        "Сумма операции": [-500, -300, 200],
        "Категория": ["Транспорт", "Продукты", "Развлечения"],
        "Описание": ["Поездка", "Магазин", "Кино"],
        # Для get_card_with_spend
        "Сумма операции с округлением": [-500, -100, -50],
        "Номер карты": ["****1234", "****5678", "****1234"],
    }
    df = pd.DataFrame(data)
    df["Дата платежа"] = pd.to_datetime(df["Дата платежа"])
    return df


@pytest.fixture
def mock_excel_data() -> str:
    """Фикстура для предоставления образца данных для excel-файла"""
    data = """
Дата операции,Категория,Сумма платежа,Кэшбэк
01.04.2024 10:00:00,Продукты,-1000,10
15.04.2024 12:00:00,Транспорт,-500,5
30.04.2024 15:00:00,Продукты,-2000,20
05.05.2024 18:00:00,Развлечения,-700,7
"""
    return data

@pytest.fixture
def mock_file_path(tmp_path: pytest.TempPathFactory) -> str:
    """Фикстура для создания фиктивного пути к файлу"""
    file_path = str(Path(tmp_path) / "test.xlsx")
    return file_path
