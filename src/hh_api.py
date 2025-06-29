from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import requests

from .config import USER_AGENT


class AbstractAPI(ABC):
    """Абстрактный базовый класс для API-подключений.
    Определяет интерфейс для подключения и получения вакансий"""

    @abstractmethod
    def _connect(self) -> None:
        """Метод проверки подключения к API. Должен быть реализован в наследниках"""
        pass

    @abstractmethod
    def get_vacancies(self, keyword: str, per_page: int, area: int, page: int = 0) -> List[Dict[str, Any]]:
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
        if self.__session is None:
            raise ConnectionError("Сессия не инициализирована")
        try:
            response = self.__session.get(url=self.__base_url_vacancies, headers=self.__headers)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ConnectionError(f"Ошибка подключения к API: {e}")

    def get_vacancies(self, keyword: str, per_page: int = 20, area: int = 113, page: int = 0) -> List[Dict[str, Any]]:
        """Получает список вакансий по ключевому слову с параметрами пагинации и региона"""
        self._connect()
        if self.__session is None:
            raise ConnectionError("Сессия не инициализирована")
        params: dict[str, str | int] = {
            "text": keyword,
            "per_page": per_page,
            "area": area,
            "page": page,
        }
        response = self.__session.get(url=self.__base_url_vacancies, params=params, headers=self.__headers)
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError:
            return []
        items = data.get("items", [])
        if not isinstance(items, list):
            return []
        return items

    def get_employers(self, text: str, per_page: int = 10, page: int = 0) -> List[Dict[str, Any]]:
        """Поиск работодателей по тексту с пагинацией"""
        self._connect()
        if self.__session is None:
            raise ConnectionError("Сессия не инициализирована")
        params: dict[str, str | int] = {
            "text": text,
            "per_page": per_page,
            "page": page,
        }
        response = self.__session.get(url=self.__base_url_employers, params=params, headers=self.__headers)
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError:
            return []
        items = data.get("items", [])
        if not isinstance(items, list):
            return []
        return items
