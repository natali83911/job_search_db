from typing import Optional, Tuple


class Company:
    """Класс для хранения информации о компании."""

    def __init__(self, company_id: str, name: str, area: Optional[str], url: Optional[str]):
        self.company_id = company_id
        self.name = name
        self.area = area
        self.url = url

    def to_db_tuple(self) -> Tuple[str, str, Optional[str], Optional[str]]:
        """
        Возвращает данные компании в виде кортежа для вставки в базу данных.
        Порядок соответствует колонкам таблицы.
        """
        return (self.company_id, self.name, self.area, self.url)
