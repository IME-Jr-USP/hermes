import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from config import settings
from constants import LOG_BACKUP_COUNT, LOG_DATE_FORMAT, LOG_FORMAT, LOG_MAX_BYTES


def get_logger(name: str) -> logging.Logger:
    """Retorna logger com nome fornecido, configurado para logar em arquivo e no console."""

    logger = logging.getLogger(name)
    logger.propagate = False

    if logger.handlers:
        return logger

    os.makedirs(os.path.dirname(settings.log_path), exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    for handler in (
        RotatingFileHandler(settings.log_path, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"),
        logging.StreamHandler(),
    ):
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(settings.log_level)
    return logger


def truncar_texto(texto: str, limite: int) -> str:
    """Trunca `texto` em `limite` caracteres sem cortar palavras"""

    if len(texto) <= limite:
        return texto
    return texto[:limite].rsplit(" ", 1)[0] + "..."


def agora_iso() -> str:
    """Retorna a data e hora atual no formato ISO 8601, truncada para segundos."""

    return datetime.now().isoformat(timespec="seconds")
