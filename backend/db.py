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
    DISCIPLINA_CHAVES_DOCUMENT,
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

    dados = disciplina.obter_dados()

    metadata = {
        "sigla": disciplina.sigla,
        "instituto_nome": instituto.nome,
        "instituto_abrev": instituto.abrev.upper(),
        "instituto_codigo": instituto.codigo,
        "instituto_campus": instituto.campus,
        "departamento": dados.get("departamento", ""),
        "nome": dados.get("nome", ""),
        "nome_ingles": dados.get("nome ingles", ""),
        "creditos_aula": dados.get("creditos aula", "0"),
        "creditos_trabalho": dados.get("creditos trabalho", "0"),
        "carga_horaria_total": dados.get("carga horaria total", "0"),
        "tipo": dados.get("tipo", ""),
        "ativacao": dados.get("ativacao", ""),
        "desativacao": dados.get("desativacao", ""),
        "ementa": dados.get("ementa", ""),
        "objetivos": dados.get("objetivos", ""),
        "conteudo_programatico": dados.get("conteudo programatico", ""),
        "avaliacao_metodo": dados.get("instrumentos e criterios de avaliacao", {}).get("metodo de avaliacao", ""),
        "avaliacao_criterio": dados.get("instrumentos e criterios de avaliacao", {}).get("criterio de avaliacao", ""),
        "avaliacao_norma_recup": dados.get("instrumentos e criterios de avaliacao", {}).get("norma de recuperacao", ""),
        "docentes_responsaveis": [
            str(i).strip() for i in dados.get("docente(s) responsavel(eis)", "").splitlines() if i
        ],
        "oferecida": disciplina.possui_oferecimento(),
        "ultima_atualizacao": time.time(),
    }

    # seção unificada de bibliografia
    metadata["bibliografia"] = ""
    if "bibliografia" in dados:
        metadata["bibliografia"] += dados["bibliografia"] + "\n"
    if "bibliografia basica" in dados:
        metadata["bibliografia"] += "bibliografia basica:\n" + dados["bibliografia basica"] + "\n"
    if "bibliografia complementar" in dados:
        metadata["bibliografia"] += "bibliografia complementar:\n" + dados["bibliografia complementar"] + "\n"

    # converter seções numéricas
    for i in ["creditos_aula", "creditos_trabalho", "carga_horaria_total"]:
        metadata[i] = str(metadata[i]).split()[0]
        if metadata[i].isnumeric():
            metadata[i] = int(metadata[i])

    # converter seções de tipo inválido
    for k, v in metadata.items():
        if not (isinstance(v, (int, str, list, float, bool)) or (v is None)):
            metadata[k] = str(v)
            logger.warning(
                "Chave '%s' tem tipo inválido '%s' em metadados da disciplina '%s' (foi convertida para string)",
                k,
                type(v),
                disciplina,
            )
        if isinstance(v, list) and len(v) == 0:
            metadata[k] = ""
            logger.warning(
                "Chave '%s' era lista vazia em metadatados da disciplina '%s' (foi convertida para string vazia)",
                k,
                disciplina,
            )

    return metadata


def _obter_document_disciplina(disciplina: Disciplina) -> str:
    """Retorna documento da `disciplina` a ser armazenado no banco de dados."""

    dados = disciplina.obter_dados()
    document = ""

    for k in DISCIPLINA_CHAVES_DOCUMENT:
        if k in dados:
            document += str(dados[k]) + "\n"

    return document


def _obter_disciplinas_institutos() -> Iterator[tuple[Disciplina, Instituto]]:
    """Retorna pares (`Disciplina`, `Instituto`) com todas as disciplinas encontradas no Jupiterweb."""

    institutos = [jupiterweb.obter_institutos()[39]]  # TODO remover indice
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
    ids_atualizados = set()

    logger.info("Atualizando banco de disciplinas: lotes de %s disciplinas", batch_size)

    for ids, documents, metadatas in _obter_disciplinas_lotes(batch_size):
        num_lotes += 1

        logger.debug("Lote %s: enviando %s disciplinas", num_lotes, len(ids))
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

        ids_atualizados.update(ids)
        logger.info("Lote %s: enviou %s disciplinas (total: %s)", num_lotes, len(ids), len(ids_atualizados))

    # TODO trocar para oferecimento=False aquelas disciplinas que nao foram atualizadas e tem oferecimento=True (já não estão no Jupiterweb)

    duracao = time.time() - inicio
    logger.info("Banco de disciplinas atualizado: %s disciplinas em %.2fs", len(ids_atualizados), duracao)


def buscar_disciplinas(collection: chromadb.Collection, query: str, num: int = 3) -> chromadb.QueryResult:
    return collection.query(query_texts=[query], n_results=num)


if __name__ == "__main__":  # TODO remover
    client = obter_client()
    collection = obter_banco_disciplinas(client)
    atualizar_banco_disciplinas(collection)

    while True:
        query = input(" >>> ")
        res = buscar_disciplinas(collection, query, 3)
        print(res)
