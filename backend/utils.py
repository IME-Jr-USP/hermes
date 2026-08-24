import logging
import os
from enum import Enum
from logging.handlers import RotatingFileHandler

from constants import LOG_PATH

logging.getLogger().addHandler(logging.NullHandler())  # silencia loggers de terceiros


def get_logger(name: str) -> logging.Logger:
    """Retorna logger com nome fornecido, configurado para logar em arquivo e no console."""

    logger = logging.getLogger(name)
    logger.propagate = False

    if logger.handlers:
        return logger

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    for handler in (
        RotatingFileHandler(LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"),
        logging.StreamHandler(),
    ):
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logging.DEBUG)
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
