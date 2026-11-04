import json
import logging
import os
import re
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any

from chromadb.api.types import Metadata
from config import settings
from constants import LOG_BACKUP_COUNT, LOG_DATE_FORMAT, LOG_FORMAT, LOG_MAX_BYTES
from jupiterweb import Disciplina

# ---------------------------------- Logger ---------------------------------- #


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


# -------------------------- Processamento de texto -------------------------- #

logger = get_logger(__name__)


def truncar_texto(texto: str, limite: int) -> str:
    """Trunca `texto` em `limite` caracteres sem cortar palavras"""

    if len(texto) <= limite:
        return texto
    return texto[:limite].rsplit(" ", 1)[0] + "..."


def limpar_texto(valor: Any) -> str:
    """Converte `valor` do scraper em texto com espaços e quebras de linha
    normalizados."""

    if valor is None:
        return ""
    if isinstance(valor, dict):
        valor = "\n".join(f"{k}: {limpar_texto(v)}" for k, v in valor.items())
    elif isinstance(valor, (list, tuple, set)):
        valor = "\n".join(limpar_texto(v) for v in valor)

    texto = str(valor).replace("\r", "\n").replace("\xa0", " ")
    texto = re.sub(r"[ \t]+", " ", texto)  # espaços e tabs repetidos viram um espaço
    texto = re.sub(r"\s*\n\s*", "\n", texto)  # tira espaços ao redor das quebras e linhas vazias
    return texto.strip()


def texto_para_int(texto: str, default: Any = None) -> int | Any:
    """Extrai o primeiro inteiro de `texto` (ex.: '4 créditos aula' vira 4).
    Retorna `default` se não encontrar."""

    m = re.search(r"\d+", str(texto)) if texto is not None else None
    return int(m.group()) if m else default


def serializar_requisitos(requisitos: dict) -> str:
    """
    Serializa dicionário de requisitos e retorna JSON correspondente.
    Ex: {curso: [[Requisito, ...], ...]} vira JSON {curso: [[{"sigla", "tipo"}, ...], ...]}.
    """

    if not requisitos:
        return ""
    saida = {curso: [[{"sigla": r.sigla, "tipo": r.tipo} for r in grupo] for grupo in grupos] for curso, grupos in requisitos.items()}
    return json.dumps(saida, ensure_ascii=False)


def limpar_metadata(metadata: dict[str, Any], disciplina: Disciplina) -> Metadata:
    """
    Remove chaves None e com valores de tipos inválidos, para uso em metadados
    do ChromaDB.
    """

    validos = {}
    for chave, valor in metadata.items():
        if valor is None:
            continue
        if not isinstance(valor, (str, int, float, bool)):
            logger.warning("Chave '%s' dos metadados de '%s' tem tipo inválido '%s' (foi omitida)", chave, disciplina, type(valor))
            continue
        validos[chave] = valor
    return validos


# ---------------------------------- Outros ---------------------------------- #


def agora_iso() -> str:
    """Retorna a data e hora atual no formato ISO 8601, truncada para segundos."""

    return datetime.now().isoformat(timespec="seconds")
