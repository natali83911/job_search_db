from typing import Optional, Tuple


class Company:
    """Класс для хранения информации о компании."""

    def __init__(self, company_id: str, name: str, area: Optional[str], url: Optional[str]):
        """Инициализация обьекта класса Company"""
        self.company_id = company_id
        self.name = name
        self.area = area
        self.url = url

    def to_db_tuple(self) -> Tuple[str, str, Optional[str], Optional[str]]:
        """Возвращает данные компании в виде кортежа для вставки в базу данных."""
        return (self.company_id, self.name, self.area, self.url)

    @classmethod
    def from_api_data(cls, data: dict) -> "Company":
        """
        Создаёт объект Company из данных, полученных из API.

        :param data: Словарь с данными компании в формате API
        :return: Экземпляр класса Company, заполненный данными из словаря
        """
        area_name = data.get("area", {}).get("name") if data.get("area") else None
        return cls(
            company_id=data.get("id", ""),
            name=data.get("name", ""),
            area=area_name,
            url=data.get("alternate_url", ""),
        )
