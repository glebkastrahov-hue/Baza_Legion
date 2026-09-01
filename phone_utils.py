"""
Приведение номера телефона к единому формату: +<только цифры>.
"""
import re
from typing import Optional


def normalize_phone(raw: str) -> Optional[str]:
    """
    Принимает "сырую" строку с номером, возвращает нормализованный номер
    вида "+79261234567" или None, если строка не похожа на номер.
    """
    if raw is None:
        return None

    raw = str(raw).strip()
    if not raw.startswith("+"):
        return None

    digits = re.sub(r"\D", "", raw)

    if len(digits) < 10:
        return None

    return "+" + digits
