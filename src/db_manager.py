import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import List, Tuple, Optional
from config import config
from company import Company
from vacancy import Vacancy



class DBManager:
    """Класс для управления базой данных PostgreSQL."""

    def __init__(self, dbname: Optional[str] = None) -> None:
        """
        Инициализация подключения.
        Если dbname не передан, подключается к базе по умолчанию из конфигурации.
        """
        params = config()
        if dbname:
            params['database'] = dbname
        self.params = params
        self.conn = None

    def create_database(self, dbname: str) -> None:
        params = self.params.copy()
        params['database'] = 'postgres'

        conn = psycopg2.connect(**params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s;", (dbname,))
                exists = cur.fetchone()
                if not exists:
                    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
                    print(f"База данных '{dbname}' успешно создана.")
                else:
                    print(f"База данных '{dbname}' уже существует.")
        finally:
            conn.close()

    def connect(self) -> None:
        """Устанавливает соединение с базой данных."""
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(**self.params)
            self.conn.autocommit = True

    def close(self) -> None:
        """Закрывает соединение с базой данных."""
        if self.conn and not self.conn.closed:
            self.conn.close()

    def create_tables(self) -> None:
        """Создает таблицы companies и vacancies."""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    company_id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    area VARCHAR(255),
                    url VARCHAR(255)
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vacancies (
                    vacancy_id SERIAL PRIMARY KEY,
                    company_id VARCHAR(50) REFERENCES companies(company_id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    salary VARCHAR(100),
                    url VARCHAR(255) NOT NULL UNIQUE,
                    description TEXT
                );
            """)
        print("Таблицы успешно созданы или уже существуют.")

    def insert_company(self, company: "Company") -> None:
        """Вставляет компанию в таблицу companies."""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO companies (company_id, name, area, url)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (company_id) DO NOTHING;
            """, (company.company_id, company.name, company.area, company.url))

    def insert_vacancy(self, vacancy: "Vacancy", company_id: str) -> None:
        """Вставляет вакансию в таблицу vacancies."""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO vacancies (company_id, title, salary, url, description)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING;
            """, (company_id, vacancy.title, vacancy.salary, vacancy.url, vacancy.description))

    def get_companies_and_vacancies_count(self) -> List[Tuple[str, int]]:
        """
        Возвращает список компаний и количество вакансий у каждой компании.
        Результат отсортирован по убыванию количества вакансий.
        """
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT c.name, COUNT(v.vacancy_id) AS vacancies_count
                FROM companies c
                LEFT JOIN vacancies v ON c.company_id = v.company_id
                GROUP BY c.name
                ORDER BY vacancies_count DESC;
            """)
            results = cur.fetchall()
        # Формируем человекочитаемый список строк
        return [(name, count) for name, count in results]

    def get_all_vacancies(self) -> List[str]:
        """
        Возвращает список всех вакансий в человекочитаемом формате:
        "Компания: <название>, Вакансия: <название>, Зарплата: <зарплата>, Ссылка: <url>"
        """
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT c.name, v.title, COALESCE(v.salary, 'Зарплата не указана'), v.url
                FROM vacancies v
                JOIN companies c ON v.company_id = c.company_id;
            """)
            rows = cur.fetchall()

        result = []
        for company, title, salary, url in rows:
            line = f"Компания: {company}, Вакансия: {title}, Зарплата: {salary}, Ссылка: {url}"
            result.append(line)
        return result

    def get_avg_salary(self) -> Optional[float]:
        """
        Возвращает среднюю зарплату по вакансиям, корректно обрабатывая строки salary.
        """
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT AVG(salary_int) FROM (
                    SELECT
                        CASE
                            WHEN salary ~ E'\\d+' THEN CAST(regexp_replace(salary, '[^0-9]', '', 'g') AS INTEGER)
                            ELSE NULL
                        END AS salary_int
                    FROM vacancies
                    WHERE salary IS NOT NULL
                      AND salary <> ''
                      AND salary <> 'Зарплата не указана'
                ) AS subquery;
            """)
            result = cur.fetchone()
            return result[0] if result else None

    def get_vacancies_with_higher_salary(self) -> List[str]:
        """
        Возвращает список вакансий с зарплатой выше средней в человекочитаемом формате.
        """
        avg_salary = self.get_avg_salary()
        if avg_salary is None:
            return ["Средняя зарплата не рассчитана."]

        self.connect()
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT c.name, v.title, COALESCE(v.salary, 'Зарплата не указана'), v.url
                FROM vacancies v
                JOIN companies c ON v.company_id = c.company_id
                WHERE (
                    CASE 
                        WHEN salary LIKE 'от %' THEN CAST(SPLIT_PART(salary, ' ', 2) AS INTEGER)
                        WHEN salary LIKE 'до %' THEN CAST(SPLIT_PART(salary, ' ', 2) AS INTEGER)
                        WHEN salary LIKE '%-%' THEN CAST(SPLIT_PART(salary, '-', 1) AS INTEGER)
                        ELSE 0
                    END
                ) > %s;
            """, (avg_salary,))
            rows = cur.fetchall()

        result = []
        for company, title, salary, url in rows:
            line = f"Компания: {company}, Вакансия: {title}, Зарплата: {salary}, Ссылка: {url}"
            result.append(line)
        return result

    def get_vacancies_with_keyword(self, keyword: str) -> List[str]:
        """
        Возвращает список вакансий, в названии которых содержится keyword (без учета регистра),
        в человекочитаемом формате.
        """
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT c.name, v.title, COALESCE(v.salary, 'Зарплата не указана'), v.url
                FROM vacancies v
                JOIN companies c ON v.company_id = c.company_id
                WHERE v.title ILIKE %s;
            """, (f"%{keyword}%",))
            rows = cur.fetchall()

        result = []
        for company, title, salary, url in rows:
            line = f"Компания: {company}, Вакансия: {title}, Зарплата: {salary}, Ссылка: {url}"
            result.append(line)
        return result


def test_db_manager():
    db_name = "hh_test_db"
    db = DBManager()

    # 1. Создаем базу данных (если еще не создана)
    db.create_database(db_name)

    # 2. Подключаемся к новой базе
    db = DBManager(dbname=db_name)
    db.create_tables()

    # 3. Вставляем тестовые компании
    companies = [
        Company("1", "Компания А", "Москва", "https://hh.ru/employer/1"),
        Company("2", "Компания Б", "Санкт-Петербург", "https://hh.ru/employer/2"),
    ]
    for company in companies:
        db.insert_company(company)

    # 4. Вставляем тестовые вакансии
    vacancies = [
        Vacancy("Разработчик Python", "https://hh.ru/vacancy/1", "от 100000 руб.", "Описание вакансии 1"),
        Vacancy("Тестировщик", "https://hh.ru/vacancy/2", "до 80000 руб.", "Описание вакансии 2"),
        Vacancy("Менеджер проекта", "https://hh.ru/vacancy/3", "120000 - 150000 руб.", "Описание вакансии 3"),
    ]
    db.insert_vacancy(vacancies[0], "1")
    db.insert_vacancy(vacancies[1], "1")
    db.insert_vacancy(vacancies[2], "2")

    # 5. Проверяем методы выборки

    print("Компании и количество вакансий:")
    for name, count in db.get_companies_and_vacancies_count():
        print(f"{name}: {count}")

    print("\nВсе вакансии:")
    for vacancy_str in db.get_all_vacancies():
        print(vacancy_str)

    avg_salary = db.get_avg_salary()
    print(f"\nСредняя зарплата: {avg_salary}")

    print("\nВакансии с зарплатой выше средней:")
    for vacancy_str in db.get_vacancies_with_higher_salary():
        print(vacancy_str)

    print("\nВакансии с ключевым словом 'Python':")
    for vacancy_str in db.get_vacancies_with_keyword("Python"):
        print(vacancy_str)

    # 6. Закрываем соединение
    db.close()

if __name__ == "__main__":
    test_db_manager()
