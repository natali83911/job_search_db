import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import sql

from .config import config
from .db_manager import DBManager
from .hh_api import HeadHunterAPI
from .company import Company
from .vacancy import Vacancy

def create_database(db_name: str) -> None:
    """
    Создаёт базу данных, если она ещё не существует.

    :param db_name: Имя базы данных для создания.
    :return: None
    """
    params = config()
    params["database"] = "postgres"
    conn = psycopg2.connect(**params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s;", (db_name,))
            exists = cur.fetchone()
            if not exists:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
                print(f"База данных '{db_name}' успешно создана.")
            else:
                print(f"База данных '{db_name}' уже существует.")
    finally:
        conn.close()

def fill_database_with_api_data(db_manager: DBManager, api: HeadHunterAPI) -> None:
    """
    Запрашивает у пользователя ключевое слово для поиска, загружает компании и вакансии из API HeadHunter,
    и добавляет их в базу данных.

    :param db_manager: Объект для управления базой данных (DBManager).
    :param api: Объект для работы с API HeadHunter (HeadHunterAPI).
    :return: None
    :raises SystemExit: Если ключевое слово не введено, программа завершается.
    """
    keyword = input("Введите ключевое слово для поиска компаний и вакансий: ").strip()
    if not keyword:
        print("Ключевое слово не может быть пустым. Завершение работы.")
        exit()

    companies = api.get_employers(keyword, per_page=10)
    for company_data in companies:
        company = Company.from_api_data(company_data)
        vacancies = api.get_vacancies(keyword, per_page=10)
        if vacancies:
            db_manager.insert_company(company)
            for vacancy_data in vacancies:
                vacancy = Vacancy.from_api_data(vacancy_data)
                db_manager.insert_vacancy(vacancy, company.company_id)
    print("Данные успешно загружены и сохранены в базу.")

def setup_and_fill_database(db_name: str = "hh_db") -> DBManager:
    """
    Полная инициализация базы: создание, создание таблиц, заполнение данными.

    :param db_name: Имя базы данных.
    :return: Объект DBManager для работы с базой.
    """
    create_database(db_name)
    db_manager = DBManager(dbname=db_name)
    db_manager.create_tables()
    api = HeadHunterAPI()
    fill_database_with_api_data(db_manager, api)
    return db_manager

def user_interface_with_keyword(db_manager: DBManager) -> None:
    """
    Функция взаимодействия с пользователем.
    Сначала запрашивает ключевое слово для поиска вакансий,
    затем позволяет выполнять остальные действия с фильтрацией по ключевому слову.

    :param db_manager: Объект для управления базой данных (DBManager).
    :return: None
    """
    keyword = input("Введите ключевое слово для поиска вакансий: ").strip()
    if not keyword:
        print("Ключевое слово не может быть пустым. Завершение работы.")
        return

    while True:
        print("\nВыберите действие:")
        print("1 - Показать компании и количество вакансий")
        print("2 - Показать все вакансии")
        print("3 - Показать среднюю зарплату по вакансиям")
        print("4 - Показать вакансии с зарплатой выше средней")
        print(f"5 - Показать вакансии с ключевым словом '{keyword}'")
        print("0 - Выход")

        choice = input("Введите номер действия: ").strip()

        if choice == "1":
            print("\nКомпании и количество вакансий:")
            companies = db_manager.get_companies_and_vacancies_count()
            for name, count in companies:
                print(f"- {name}: {count}")

        elif choice == "2":
            print("\nВсе вакансии:")
            vacancies = db_manager.get_all_vacancies()
            for vacancy_str in vacancies:
                print(f"- {vacancy_str}")

        elif choice == "3":
            avg_salary = db_manager.get_avg_salary()
            if avg_salary is not None:
                print(f"\nСредняя зарплата по вакансиям: {avg_salary:.2f}")
            else:
                print("\nСредняя зарплата не рассчитана.")

        elif choice == "4":
            print("\nВакансии с зарплатой выше средней:")
            vacancies = db_manager.get_vacancies_with_higher_salary()
            for vacancy_str in vacancies:
                print(f"- {vacancy_str}")

        elif choice == "5":
            print(f"\nВакансии с ключевым словом '{keyword}':")
            vacancies = db_manager.get_vacancies_with_keyword(keyword)
            if vacancies:
                for vacancy_str in vacancies:
                    print(f"- {vacancy_str}")
            else:
                print("Вакансии не найдены.")

        elif choice == "0":
            print("Выход из программы.")
            break

        else:
            print("Некорректный ввод. Пожалуйста, введите номер действия из списка.")

