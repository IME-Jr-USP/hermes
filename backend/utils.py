import logging
import os
from enum import Enum
from logging.handlers import RotatingFileHandler

from config import settings
from constants import LOG_BACKUP_COUNT, LOG_DATE_FORMAT, LOG_FORMAT, LOG_MAX_BYTES

logging.getLogger().addHandler(logging.NullHandler())  # silencia loggers de terceiros


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


class CampusDisciplina(str, Enum):
    LORENA = "Lorena"
    LESTE = "Leste"
    PIRACICABA = "Piracicaba"
    SAO_SEBASTIAO = "São Sebastião"
    BAURU = "Bauru"
    PIRASSUNUNGA = "Pirassununga"
    RIBEIRAO_PRETO = "Ribeirão Preto"
    QUADRILATERO = "Quadrilátero"
    BUTANTA = "Butantã"
    IPIRANGA = "Ipiranga"
    SAO_CARLOS = "São Carlos"
