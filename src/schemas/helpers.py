import re


def normalize_and_validate_russian_phone(value: str | None) -> str | None:
    """
    Утилита для валидации и нормализации российских номеров телефонов.
    Превращает +7, 7, 8 и форматы со скобками/дефисами в чистые '79999999999'.
    Если передан None (для опциональных полей), возвращает None.
    """
    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError("Номер телефона должен быть строкой")

    cleaned = re.sub(r"[\s\-\(\)]", "", value)
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if cleaned.startswith("8"):
        cleaned = "7" + cleaned[1:]

    if not re.match(r"^7\d{10}$", cleaned):
        raise ValueError("Неверный формат телефона. Ожидается: +79999999999")

    return cleaned
