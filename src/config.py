import os
from configparser import ConfigParser

USER_AGENT = "Mozilla/5.0"
import psycopg2
from psycopg2 import sql

def config(filename: str = None, section: str = "postgresql") -> dict:
    """
    Читает параметры подключения к базе данных из файла .ini в кодировке UTF-8.
    Гарантирует, что все значения параметров — строки без лишних пробелов.

    :param filename: Путь к файлу конфигурации, по умолчанию ищет database.ini в корне проекта
    :param section: Секция в ini-файле с параметрами подключения
    :return: Словарь параметров подключения
    """
    if filename is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filename = os.path.join(base_dir, "database.ini")

    parser = ConfigParser()
    with open(filename, encoding='utf-8') as f:
        parser.read_file(f)

    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for key, value in params:
            clean_value = value.strip()
            # Если значение — байты, декодируем в строку
            if isinstance(clean_value, bytes):
                clean_value = clean_value.decode("utf-8", errors="replace")
            db[key] = clean_value
    else:
        raise Exception(f"Section {section} not found in the {filename} file.")
    return db



