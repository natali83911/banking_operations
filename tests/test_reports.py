import pandas as pd
import pytest

from src.reports import expenses_by_category, get_data_from_file, save_result_to_txt


@pytest.mark.parametrize(
    "category,date,expected_count",
    [
        ("Продукты", "2025-04-28", 2),
        ("Транспорт", "2025-04-28", 1),
        ("Продукты", None, 2),
        ("Неизвестная", "2025-04-28", 0),
    ],
)
def test_expenses_by_category_counts(sample_transactions, category, date, expected_count, tmp_path):
    test_file = tmp_path / "test_report.txt"

    @save_result_to_txt(str(test_file))
    def tested_func(*args, **kwargs):
        # Вызываем оригинальную функцию без декоратора, чтобы избежать двойной записи в файл
        return expenses_by_category.__wrapped__(*args, **kwargs)

    result = tested_func(sample_transactions, category, date)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == expected_count
    assert test_file.exists()


def test_expenses_by_category_invalid_date(sample_transactions):
    with pytest.raises(ValueError):
        expenses_by_category(sample_transactions, "Продукты", "неправильная_дата")


def test_get_data_from_file_reads_excel(monkeypatch):
    fake_df = pd.DataFrame({"A": [1, 2]})

    def fake_read_excel(path):
        return fake_df

    monkeypatch.setattr("src.reports.pd.read_excel", fake_read_excel)

    df = get_data_from_file("fake.xlsx")
    assert df.equals(fake_df)


def test_save_result_to_txt_writes_txt(tmp_path, sample_transactions):
    test_file = tmp_path / "out.txt"

    @save_result_to_txt(str(test_file))
    def func(df):
        return df

    func(sample_transactions)
    assert test_file.exists()
    content = test_file.read_text(encoding="utf-8")
    assert content.strip() != ""


def test_expenses_by_category_logging(sample_transactions, tmp_path):
    test_file = tmp_path / "log_test.txt"

    @save_result_to_txt(str(test_file))
    def tested_func(*args, **kwargs):
        return expenses_by_category.__wrapped__(*args, **kwargs)

    tested_func(sample_transactions, "Продукты", "2025-04-28")
    assert test_file.exists()
