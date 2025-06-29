import os
from configparser import ConfigParser
from typing import Dict, Optional

USER_AGENT = "Mozilla/5.0"


def config(filename: Optional[str] = None, section: str = "postgresql") -> Dict[str, str]:
    """
    Читает параметры подключения к базе данных из файла .ini в кодировке UTF-8.
    Гарантирует, что все значения параметров — строки без лишних пробелов.

    :param filename: Путь к файлу конфигурации, по умолчанию ищет database.ini в корне проекта.
    :param section: Секция в ini-файле с параметрами подключения.
    :return: Словарь параметров подключения.
    :raises Exception: Если секция не найдена.
    """
    if filename is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filename = os.path.join(base_dir, "database.ini")

    parser = ConfigParser()
    with open(filename, encoding="utf-8") as f:
        parser.read_file(f)

    db: Dict[str, str] = {}
    if parser.has_section(section):
        for key, value in parser.items(section):
            clean_value = value.strip()
            # Если значение — байты, декодируем в строку (обычно это не требуется с ConfigParser)
            if isinstance(clean_value, bytes):
                clean_value = clean_value.decode("utf-8", errors="replace")
            db[key] = clean_value
    else:
        raise Exception(f"Section {section} not found in the {filename} file.")
    return db
