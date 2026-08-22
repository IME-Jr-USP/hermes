import time
from collections.abc import Iterator
from itertools import islice

import chromadb
import jupiterweb
from chromadb.api import ClientAPI
from chromadb.utils import embedding_functions
from jupiterweb import Disciplina, Instituto

from constants import (
    DB_COLLECTION_NAME,
    DB_DISTANCE_METRIC,
    DB_PATH,
    EMBEDDING_DEVICE,
    EMBEDDING_MODEL,
    EMBEDDING_NORMALIZE,
)
from utils import get_logger

logger = get_logger(__name__)


def obter_client() -> ClientAPI:
    """Retorna PersistentClient do ChromaDB."""

    client = chromadb.PersistentClient(path=DB_PATH)
    logger.info("Client ChromaDB inicializado em '%s'", DB_PATH)

    return client


def obter_banco_disciplinas(client: ClientAPI) -> chromadb.Collection:
    """Retorna banco de disciplinas. Caso não exista, cria um banco novo vazio."""

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL, device=EMBEDDING_DEVICE, normalize_embeddings=EMBEDDING_NORMALIZE
    )

    collection = client.get_or_create_collection(
        name=DB_COLLECTION_NAME, embedding_function=ef, metadata={"hnsw:space": DB_DISTANCE_METRIC}
    )

    logger.info("Coleção '%s' pronta (%s itens)", DB_COLLECTION_NAME, collection.count())
    return collection


def _obter_id_disciplina(disciplina: Disciplina) -> str:
    """Retorna ID da `disciplina` a ser utilizado no banco de dados."""

    return str(disciplina.sigla).upper()


def _obter_metadata_disciplina(disciplina: Disciplina, instituto: Instituto) -> dict:
    """Retorna metadados da `disciplina` a serem armazenados no banco de dados."""

    return {"ultima_atualizacao": time.time()}  # TODO


def _obter_document_disciplina(disciplina: Disciplina) -> str:
    """Retorna documento da `disciplina` a ser armazenado no banco de dados."""

    return disciplina.obter_dados()["nome"]  # TODO


def _obter_disciplinas_institutos() -> Iterator[tuple[Disciplina, Instituto]]:
    """Retorna pares (`Disciplina`, `Instituto`) com todas as disciplinas encontradas no Jupiterweb."""

    institutos = [jupiterweb.obter_institutos()[3]]  # TODO remover indice
    for instituto in institutos:
        for disciplina in instituto.obter_disciplinas():
            if disciplina.encontrada():
                yield disciplina, instituto
            else:
                logger.debug("Disciplina não encontrada: %s", disciplina)


def _obter_disciplinas_lotes(batch_size: int = 50) -> Iterator[tuple[list[str], list[str], list[dict]]]:
    """
    Obtém as disciplinas do Jupiterweb em lotes de tamanho `batch_size`.
    Cada lote é uma tripla (`ids`, `documents`, `metadatas`), pronto para o banco de dados.
    """

    iterator_disciplinas = _obter_disciplinas_institutos()

    while True:
        lote = islice(iterator_disciplinas, batch_size)
        ids = []
        documents = []
        metadatas = []

        for disciplina, instituto in lote:
            ids.append(_obter_id_disciplina(disciplina))
            documents.append(_obter_document_disciplina(disciplina))
            metadatas.append(_obter_metadata_disciplina(disciplina, instituto))
            logger.debug("Disciplina adicionada ao lote (%s/%s): %s", len(ids), batch_size, disciplina)

        if len(ids) == 0:
            break
        yield ids, documents, metadatas


def atualizar_banco_disciplinas(collection: chromadb.Collection, batch_size: int = 50) -> None:
    """
    Atualiza `collection` com as disciplinas do Jupiterweb, em lotes de tamanho `batch_size` (pode demorar).
    """

    inicio = time.time()
    num_lotes = 0
    num_disciplinas = 0

    logger.info("Atualizando banco de disciplinas: lotes de %s disciplinas", batch_size)

    for ids, documents, metadatas in _obter_disciplinas_lotes(batch_size):
        num_lotes += 1

        logger.debug("Lote %s: enviando %s disciplinas", num_lotes, len(ids))
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

        num_disciplinas += len(ids)
        logger.info("Lote %s: enviou %s disciplinas (total: %s)", num_lotes, len(ids), num_disciplinas)

    duracao = time.time() - inicio
    logger.info("Banco de disciplinas atualizado: %s disciplinas em %.2fs", num_disciplinas, duracao)


def buscar_disciplinas(collection: chromadb.Collection, query: str, num: int = 3) -> chromadb.QueryResult:
    return collection.query(query_texts=[query], n_results=num)


if __name__ == "__main__":  # TODO remover
    client = obter_client()
    collection = obter_banco_disciplinas(client)
    # atualizar_banco_disciplinas(collection)

    while True:
        query = input(" >>> ")
        res = buscar_disciplinas(collection, query, 3)
        print(res)
