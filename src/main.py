from config import PATH_TO_EXCEL
from src.services import analyze_cashback_categories
from src.views import main_info

if __name__ == "__main__":
    print(main_info("2021-12-15 15:30:00"))

    print(analyze_cashback_categories(PATH_TO_EXCEL, 2018, 3))
