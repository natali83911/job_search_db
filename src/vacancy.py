from typing import Any, Dict, Optional


class Vacancy:
    """Класс, представляющий вакансию с основными атрибутами."""

    __slots__ = ["title", "url", "salary_from", "salary_to", "description"]

    def __init__(
        self,
        title: str,
        url: str,
        salary_from: Optional[int],
        salary_to: Optional[int],
        description: str,
    ):
        self.title = title
        self.url = url
        self.salary_from = salary_from
        self.salary_to = salary_to
        self.description = description

    def get_salary_average(self) -> Optional[float]:
        """Возвращает среднее значение зарплаты или None, если зарплата не указана."""
        if self.salary_from is not None and self.salary_to is not None:
            return (self.salary_from + self.salary_to) / 2
        elif self.salary_from is not None:
            return float(self.salary_from)
        elif self.salary_to is not None:
            return float(self.salary_to)
        else:
            return None

    @classmethod
    def from_api_data(cls, item: Dict[str, Any]) -> "Vacancy":
        """
        Создаёт объект Vacancy из данных, полученных из API.

        Извлекает информацию о зарплате из вложенного словаря 'salary',
        устанавливая значения salary_from и salary_to, если они присутствуют.

        :param item: Словарь с данными вакансии в формате API
        :return: Экземпляр класса Vacancy, заполненный данными из словаря
        """
        salary_info = item.get("salary")
        salary_from = None
        salary_to = None
        if salary_info and isinstance(salary_info, dict):
            salary_from = salary_info.get("from")
            salary_to = salary_info.get("to")
        return cls(
            title=item.get("name", "Без названия"),
            url=item.get("alternate_url", ""),
            salary_from=salary_from,
            salary_to=salary_to,
            description=(
                item.get("snippet", {}).get("requirement", "")
                or item.get("snippet", {}).get("responsibility", "")
                or ""
            ),
        )
