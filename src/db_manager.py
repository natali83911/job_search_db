from typing import List, Optional, Tuple

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from .company import Company
from .config import config
from .vacancy import Vacancy


class DBManager:
    """
    Класс для работы с базой данных PostgreSQL: создание базы, таблиц,
    вставка и выборка данных о компаниях и вакансиях.
    """

    def __init__(self, dbname: Optional[str] = None) -> None:
        """
        Инициализация менеджера БД.

        :param dbname: Имя базы данных для подключения (если не указано — из config)
        """
        params = config()
        if dbname:
            params["database"] = dbname
        self.params = params
        self.conn: Optional[psycopg2.extensions.connection] = None

    def create_database(self, dbname: str) -> None:
        """
        Создаёт базу данных, если она ещё не существует.

        :param dbname: Имя создаваемой базы данных
        """
        params = self.params.copy()
        params["database"] = "postgres"

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

    import copy

    def connect(self) -> None:
        if self.conn is None or self.conn.closed:
            import copy
            params_copy = copy.deepcopy(self.params)
            for k, v in params_copy.items():
                if isinstance(v, bytes):
                    params_copy[k] = v.decode("utf-8", errors="replace")
                else:
                    params_copy[k] = str(v).strip()
            self.conn = psycopg2.connect(**params_copy)
            self.conn.autocommit = True

    def close(self) -> None:
        """
        Закрывает соединение с базой данных, если оно открыто.
        """
        if self.conn and not self.conn.closed:
            self.conn.close()

    def create_tables(self) -> None:
        """
        Создаёт таблицы companies и vacancies, если они ещё не существуют.
        """
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS companies (
                    company_id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    area VARCHAR(255),
                    url VARCHAR(255)
                );
            """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS vacancies (
                    vacancy_id SERIAL PRIMARY KEY,
                    company_id VARCHAR(50) REFERENCES companies(company_id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    salary_from INTEGER,
                    salary_to INTEGER,
                    url VARCHAR(255) NOT NULL UNIQUE,
                    description TEXT
                );
            """
            )
        print("Таблицы успешно созданы или уже существуют.")

    def insert_company(self, company: "Company") -> None:
        """
        Вставляет компанию в таблицу companies.

        :param company: Объект компании для добавления
        """
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO companies (company_id, name, area, url)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (company_id) DO NOTHING;
            """,
                company.to_db_tuple(),
            )

    def insert_vacancy(self, vacancy: "Vacancy", company_id: str) -> None:
        """
        Вставляет вакансию в таблицу vacancies.

        :param vacancy: Объект вакансии для добавления
        :param company_id: Идентификатор компании, к которой относится вакансия
        """
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO vacancies (company_id, title, salary_from, salary_to, url, description)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING;
            """,
                (
                    company_id,
                    vacancy.title,
                    vacancy.salary_from,
                    vacancy.salary_to,
                    vacancy.url,
                    vacancy.description,
                ),
            )

    def get_companies_and_vacancies_count(self) -> List[Tuple[str, int]]:
        """
        Возвращает список компаний и количества вакансий у каждой компании.

        :return: Список кортежей (название компании, количество вакансий)
        """
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.name, COUNT(v.vacancy_id) AS vacancies_count
                FROM companies c
                LEFT JOIN vacancies v ON c.company_id = v.company_id
                GROUP BY c.name
                ORDER BY vacancies_count DESC;
            """
            )
            return cur.fetchall()

    def get_all_vacancies(self) -> List[str]:
        """
        Возвращает список всех вакансий с деталями в человекочитаемом формате.

        :return: Список строк с информацией о вакансиях
        """
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.name, v.title, v.salary_from, v.salary_to, v.url
                FROM vacancies v
                JOIN companies c ON v.company_id = c.company_id;
            """
            )
            rows = cur.fetchall()

        result: List[str] = []
        for company, title, salary_from, salary_to, url in rows:
            if salary_from is not None and salary_to is not None:
                salary_str = f"{salary_from} - {salary_to}"
            elif salary_from is not None:
                salary_str = f"от {salary_from}"
            elif salary_to is not None:
                salary_str = f"до {salary_to}"
            else:
                salary_str = "Зарплата не указана"
            line = f"Компания: {company}, Вакансия: {title}, Зарплата: {salary_str}, Ссылка: {url}"
            result.append(line)
        return result

    def get_avg_salary(self) -> Optional[float]:
        """
        Возвращает среднюю зарплату по всем вакансиям.
        Для диапазона берётся среднее между salary_from и salary_to,
        если указано только одно значение — берётся оно.

        :return: Средняя зарплата или None, если данных нет
        """
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT AVG(
                    (COALESCE(salary_from, 0) + COALESCE(salary_to, 0)) /
                    NULLIF(CASE WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL THEN 2 ELSE 1 END, 0)
                )
                FROM vacancies
                WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL;
            """
            )
            result = cur.fetchone()
            return result[0] if result else None

    def get_vacancies_with_higher_salary(self) -> List[str]:
        """
        Возвращает список вакансий с зарплатой выше средней.

        :return: Список строк с информацией о вакансиях
        """
        avg_salary = self.get_avg_salary()
        if avg_salary is None:
            return ["Средняя зарплата не рассчитана."]

        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.name, v.title, v.salary_from, v.salary_to, v.url
                FROM vacancies v
                JOIN companies c ON v.company_id = c.company_id;
            """
            )
            rows = cur.fetchall()

        result: List[str] = []
        for company, title, salary_from, salary_to, url in rows:
            if salary_from is not None and salary_to is not None:
                avg = (salary_from + salary_to) / 2
            elif salary_from is not None:
                avg = salary_from
            elif salary_to is not None:
                avg = salary_to
            else:
                avg = 0

            if avg > avg_salary:
                if salary_from is not None and salary_to is not None:
                    salary_str = f"{salary_from} - {salary_to}"
                elif salary_from is not None:
                    salary_str = f"от {salary_from}"
                elif salary_to is not None:
                    salary_str = f"до {salary_to}"
                else:
                    salary_str = "Зарплата не указана"
                line = f"Компания: {company}, Вакансия: {title}, Зарплата: {salary_str}, Ссылка: {url}"
                result.append(line)
        return result

    def get_vacancies_with_keyword(self, keyword: str) -> List[str]:
        """
        Возвращает список вакансий, в названии которых содержится переданное слово.

        :param keyword: Ключевое слово для поиска в названии вакансии
        :return: Список строк с информацией о вакансиях
        """
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.name, v.title, v.salary_from, v.salary_to, v.url
                FROM vacancies v
                JOIN companies c ON v.company_id = c.company_id
                WHERE v.title ILIKE %s;
            """,
                (f"%{keyword}%",),
            )
            rows = cur.fetchall()

        result: List[str] = []
        for company, title, salary_from, salary_to, url in rows:
            if salary_from is not None and salary_to is not None:
                salary_str = f"{salary_from} - {salary_to}"
            elif salary_from is not None:
                salary_str = f"от {salary_from}"
            elif salary_to is not None:
                salary_str = f"до {salary_to}"
            else:
                salary_str = "Зарплата не указана"

            line = f"Компания: {company}, Вакансия: {title}, Зарплата: {salary_str}, Ссылка: {url}"
            result.append(line)

        return result