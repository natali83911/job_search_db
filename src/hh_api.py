from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import requests

from config import USER_AGENT


class AbstractAPI(ABC):
    """Абстрактный базовый класс для API-подключений.
    Определяет интерфейс для подключения и получения вакансий"""

    @abstractmethod
    def _connect(self) -> None:
        """Метод проверки подключения к API. Должен быть реализован в наследниках"""
        pass

    @abstractmethod
    def get_vacancies(self, keyword: str, per_page: int, page: int = 0) -> List[Dict[str, Any]]:
        """Метод получения вакансий по ключевым словам. Должен быть реализован в наследниках"""
        pass

    @abstractmethod
    def get_employers(self, text: str, per_page: int = 10, page: int = 0) -> List[Dict[str, Any]]:
        """Метод получения списка работодателей по поисковому запросу"""
        pass


class HeadHunterAPI(AbstractAPI):
    """Класс для работы с API HeadHunter.
    Реализует методы подключения и получения вакансий"""

    def __init__(self) -> None:
        """Инициализация объекта HeadHunterAPI.
        Устанавливает базовые URL и заголовки для запросов"""
        self.__base_url_vacancies = "https://api.hh.ru/vacancies"
        self.__base_url_employers = "https://api.hh.ru/employers"
        self.__headers = {"User-Agent": USER_AGENT}
        self.__session: Optional[requests.Session] = requests.Session()

    def _connect(self) -> None:
        """Проверка доступности API вакансий."""
        try:
            response = self.__session.get(url=self.__base_url_vacancies, headers=self.__headers)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ConnectionError(f"Ошибка подключения к API: {e}")

    def get_vacancies(self, keyword: str, per_page: int = 20, area: int = 113, page: int = 0) -> List[Dict[str, Any]]:
        """Получает список вакансий по ключевому слову с параметрами пагинации и региона"""
        self._connect()
        params = {"text": keyword, "per_page": per_page, "area": area, "page": page}
        response = self.__session.get(url=self.__base_url_vacancies, params=params, headers=self.__headers)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        if not isinstance(items, list):
            return []
        return items

    def get_employers(self, text: str, per_page: int = 10, page: int = 0) -> List[Dict[str, Any]]:
        """Поиск работодателей по тексту с пагинацией"""
        self._connect()
        params = {"text": text, "per_page": per_page, "page": page}
        response = self.__session.get(url=self.__base_url_employers, params=params, headers=self.__headers)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        if not isinstance(items, list):
            return []
        return items


if __name__ == "__main__":
    api = HeadHunterAPI()

    try:
        vacancies = api.get_vacancies(keyword="разработчик", per_page=10)
        print(f"Получено вакансий: {len(vacancies)}")
        for v in vacancies:
            print(f"Вакансия: {v.get('name')}, URL: {v.get('alternate_url')}")
    except Exception as e:
        print(f"Ошибка при получении вакансий: {e}")

    print("\n" + "-" * 40 + "\n")

    try:
        employers = api.get_employers(text="it", per_page=10)
        print(f"Найдено работодателей: {len(employers)}")
        for e in employers:
            print(f"Компания: {e.get('name')}, ID: {e.get('id')}")
    except Exception as e:
        print(f"Ошибка при поиске работодателей: {e}")
