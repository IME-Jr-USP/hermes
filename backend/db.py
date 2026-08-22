import time

import chromadb
import jupiterweb
from jupiterweb import Disciplina

from constants import COLLECTION_NAME, DB_PATH
from utils import get_logger

logger = get_logger(__name__)


def obter_banco_disciplinas() -> chromadb.Collection:
    """Retorna banco de disciplinas. Caso não exista, cria um banco novo vazio."""

    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_or_create_collection(name=COLLECTION_NAME)


def _obter_metadados_disciplina(disciplina: Disciplina) -> dict:
    """Retorna metadados da disciplina a serem armazenados no banco de dados vetorial."""

    return {"ultima_atualizacao": time.time()}  # TODO


def _obter_documento_disciplina(disciplina: Disciplina) -> str:
    """Retorna documento da disciplina a ser armazenado no banco de dados vetorial."""

    return disciplina.obter_dados()["nome"]  # TODO


def obter_disciplinas_jupiterweb(apenas_oferecidas: bool = True) -> list[Disciplina]:
    """
    Retorna lista de disciplinas do Jupiterweb (pode demorar).
    Todas as disciplina retornadas tem os dados carregados, evitando que as futuras chamadas a disciplina.obter_dados() façam scraping.
    Caso apenas_oferecidas seja True, retorna apenas disciplinas com oferecimento cadastrado.
    """

    resultado = []
    institutos = jupiterweb.obter_institutos()
    institutos = [institutos[i] for i in [11, 15, 37]]  # TODO remover

    inicio = time.time()
    logger.info("Obtendo disciplinas do Jupiterweb: %s institutos", len(institutos))

    for i in range(len(institutos)):
        inst = institutos[i]
        disc = inst.obter_disciplinas()
        logger.info("Instituto %s/%s: encontrou %s disciplinas em %s", i + 1, len(institutos), len(disc), str(inst))

        for d in disc:
            dados = d.obter_dados()
            if "nome" not in dados:
                continue

            if not apenas_oferecidas or d.possui_oferecimento():
                resultado.append(d)
                logger.debug("Disciplina adicionada: %s", str(d))
    duracao = time.time() - inicio
    logger.info("Disciplinas obtidas: %s disciplinas em %.2fs", len(resultado), duracao)
    return resultado


def atualizar_banco_disciplinas(
    collection: chromadb.Collection, disciplinas: list[Disciplina], batch_size: int = 100
) -> None:
    """
    Atualiza banco de disciplinas com as disciplinas fornecidas.
    Caso uma disciplina já exista no banco, ela será atualizada. Caso não exista, ela será adicionada.
    """

    inicio = time.time()
    num_batches = (len(disciplinas) + batch_size - 1) // batch_size
    num_disciplinas = 0

    logger.info("Atualizando banco de disciplinas: %s disciplinas em %s lotes", len(disciplinas), num_batches)

    for i in range(0, len(disciplinas), batch_size):
        batch = disciplinas[i : i + batch_size]
        num_batch = i // batch_size + 1

        ids = []
        documents = []
        metadatas = []

        for disciplina in batch:
            ids.append(disciplina.sigla)
            documents.append(_obter_documento_disciplina(disciplina))
            metadatas.append(_obter_metadados_disciplina(disciplina))

        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        logger.info("Lote %s/%s: enviou %s disciplinas", num_batch, num_batches, len(ids))
        num_disciplinas += len(ids)
    duracao = time.time() - inicio
    logger.info("Banco de disciplinas atualizado: %s disciplinas em %.2fs", num_disciplinas, duracao)
