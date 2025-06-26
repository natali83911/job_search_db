import os
from configparser import ConfigParser

USER_AGENT = "Mozilla/5.0"


def config(filename: str = None, section: str = "postgresql") -> dict:
    """
    Читает параметры подключения к базе данных из файла .ini
    """
    if filename is None:
        # Определяем абсолютный путь к файлу database.ini в корне проекта
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filename = os.path.join(base_dir, "database.ini")

    parser = ConfigParser()
    parser.read(filename)

    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f"Section {section} not found in the {filename} file.")
    return db
