import re
from typing import Any, Dict, List, Optional


class Vacancy:
    """Класс, представляющий вакансию с основными атрибутами:
    - title: название вакансии
    - url: ссылка на вакансию
    - salary: информация о зарплате (строка)
    - description: описание вакансии"""

    __slots__ = ["title", "url", "salary", "description"]

    def __init__(self, title: str, url: str, salary: str, description: str):
        """Инициализация объекта вакансии.

        :param title: название вакансии
        :param url: ссылка на вакансию
        :param salary: зарплата в виде строки
        :param description: описание вакансии"""
        self.title = title
        self.url = url
        self.salary = self._validate_salary(salary)
        self.description = description

    def _validate_salary(self, salary: Optional[str]) -> str:
        """Проверяет и нормализует значение зарплаты"""
        if not salary or salary.strip() == "":
            return "Зарплата не указана"
        return salary

    def _salary_to_int(self) -> int:
        """Преобразует строку зарплаты в целое число для сравнения.
        Берёт первое найденное число в строке.
        Если чисел нет — возвращает 0"""
        if isinstance(self.salary, str):
            nums = re.findall(r"\d+", self.salary.replace(" ", ""))
            if nums:
                return int(nums[0])
        elif isinstance(self.salary, (int, float)):
            return int(self.salary)
        return 0

    def __lt__(self, other: "Vacancy") -> bool:
        return self._salary_to_int() < other._salary_to_int()

    def __le__(self, other: "Vacancy") -> bool:
        return self._salary_to_int() <= other._salary_to_int()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vacancy):
            return NotImplemented
        return self._salary_to_int() == other._salary_to_int()

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Vacancy):
            return NotImplemented
        return self._salary_to_int() != other._salary_to_int()

    def __gt__(self, other: "Vacancy") -> bool:
        return self._salary_to_int() > other._salary_to_int()

    def __ge__(self, other: "Vacancy") -> bool:
        return self._salary_to_int() >= other._salary_to_int()

    @classmethod
    def cast_to_object_list(cls, vacancies_json: List[Dict[str, Any]]) -> List["Vacancy"]:
        """Преобразует список вакансий в формате JSON (список словарей) в список объектов Vacancy"""
        objects = []
        for item in vacancies_json:
            title = item.get("name", "Без названия")
            url = item.get("alternate_url", "")
            salary_info = item.get("salary")
            if salary_info and isinstance(salary_info, dict):
                if salary_info.get("from") and salary_info.get("to"):
                    salary = f"{salary_info['from']} - {salary_info['to']} {salary_info.get('currency', '')}"
                elif salary_info.get("from"):
                    salary = f"от {salary_info['from']} {salary_info.get('currency', '')}"
                elif salary_info.get("to"):
                    salary = f"до {salary_info['to']} {salary_info.get('currency', '')}"
                else:
                    salary = "Зарплата не указана"
            else:
                salary = "Зарплата не указана"
            description = (
                item.get("snippet", {}).get("requirement", "")
                or item.get("snippet", {}).get("responsibility", "")
                or ""
            )
            vacancy = cls(title, url, salary, description)
            objects.append(vacancy)
        return objects


# if __name__ == "__main__":
#     from hh_api import HeadHunterAPI
#
#
#     api = HeadHunterAPI()
#
#     try:
#
#         vacancies_json = api.get_vacancies(keyword="python", per_page=10)
#         vacancies = Vacancy.cast_to_object_list(vacancies_json)
#
#         print(f"Получено вакансий: {len(vacancies)}\n")
#
#         for i, vacancy in enumerate(vacancies, start=1):
#             print(f"Вакансия #{i}")
#             print(f"Название: {vacancy.title}")
#             print(f"Зарплата: {vacancy.salary}")
#             print(f"Ссылка: {vacancy.url}")
#             print(f"Описание: {vacancy.description[:200]}...")
#             print("-" * 40)
#
#     except Exception as e:
#         print(f"Ошибка при получении или обработке вакансий: {e}")
