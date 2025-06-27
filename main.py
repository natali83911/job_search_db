from src.db_manager import DBManager
from src.utils import user_interface_with_keyword
from src.hh_api import HeadHunterAPI
from src.company import Company
from src.vacancy import Vacancy


if __name__ == "__main__":
    db_manager = DBManager()
    db_manager.create_database("hh_db")
    db_manager = DBManager(dbname="hh_db")
    db_manager.create_tables()


    api = HeadHunterAPI()
    keyword = "разработчик"
    companies = api.get_employers(keyword, per_page=10)
    for company_data in companies:
        company = Company.from_api_data(company_data)
        db_manager.insert_company(company)
        vacancies = api.get_vacancies(keyword, per_page=10)
        for vacancy_data in vacancies:
            vacancy = Vacancy.from_api_data(vacancy_data)
            db_manager.insert_vacancy(vacancy, company.company_id)

    # Запуск интерфейса
    user_interface_with_keyword(db_manager)


