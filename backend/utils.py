import logging
import os
from logging.handlers import RotatingFileHandler

from constants import LOG_PATH

logging.getLogger().addHandler(logging.NullHandler()) # silencia loggers de terceiros

def get_logger(name: str) -> logging.Logger:
    """Retorna logger com nome fornecido, configurado para logar em arquivo e no console."""
    
    logger = logging.getLogger(name)
    logger.propagate = False
 
    if logger.handlers:
        return logger
 
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
 
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    for handler in (
        RotatingFileHandler(LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"),
        logging.StreamHandler(),
    ):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
 
    logger.setLevel(logging.DEBUG)
    return logger