import json
import logging
import time

import chromadb
import jupiterweb
from chromadb.api import ClientAPI
from chromadb.api.types import Metadata
from chromadb.utils import embedding_functions
from constants import (
    DB_COLLECTION_NAME,
    DB_DISTANCE_METRIC,
    DB_PATH,
    DISCIPLINA_DOCUMENT_CHAVES,
    EMBEDDING_DEVICE,
    EMBEDDING_MODEL,
    EMBEDDING_NORMALIZE,
)
from jupiterweb import Disciplina, HorarioAula, Instituto, Oferecimento
from utils import get_logger

logger = get_logger(__name__)
logging.getLogger("sentence_transformers").setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

_client: ClientAPI | None = None
_collection: chromadb.Collection | None = None


def obter_client() -> ClientAPI:
    """Retorna a instância única do cliente ChromaDB, criando-a na primeira chamada."""

    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=DB_PATH)
        logger.info("Client ChromaDB inicializado em '%s'", DB_PATH)
    return _client


def obter_banco_disciplinas() -> chromadb.Collection:
    """
    Retorna a instância única do banco de disciplinas, carregando-o na primeira chamada.
    Se não existir na primeira chamada, cria um banco novo vazio.
    """

    global _collection
    if _collection is None:
        client = obter_client()

        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL,
            device=EMBEDDING_DEVICE,
            normalize_embeddings=EMBEDDING_NORMALIZE,
        )

        _collection = client.get_or_create_collection(
            name=DB_COLLECTION_NAME,
            embedding_function=ef,  # pyright: ignore[reportArgumentType]
            metadata={"hnsw:space": DB_DISTANCE_METRIC},
        )

        logger.info("Banco de disciplinas '%s' pronto (%s itens)", DB_COLLECTION_NAME, _collection.count())
    return _collection


def _obter_id_disciplina(disciplina: Disciplina) -> str:
    """Retorna ID da `disciplina` a ser utilizado no banco de dados."""

    return str(disciplina.sigla).upper()


def _obter_metadata_disciplina(disciplina: Disciplina, instituto: Instituto) -> Metadata:
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
        "docentes_responsaveis": dados.get("docente(s) responsavel(eis)", ""),
        "url_principal": disciplina.url_principal,
        "url_oferecimento": disciplina.url_oferecimento,
        "url_requisitos": disciplina.url_requisitos,
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

    # seções de oferecimento
    professores = set()
    tipos_vaga = set()
    dias_semana = set()
    horas_aula = set()
    turmas = []

    for turma in dados.get("oferecimento", []):
        if not isinstance(turma, Oferecimento):
            continue

        tipos_vaga.update(turma.vagas.keys())
        dados_turma = {"horarios": []}

        for horario in turma.horarios:
            if not isinstance(horario, HorarioAula):
                continue

            if horario.professor:
                professores.add(horario.professor)
            if horario.dia_semana:
                dias_semana.add(horario.dia_semana)
            if horario.hora_inicio:
                horas_aula.add(horario.hora_inicio)

            dados_turma["horarios"].append(
                {
                    "hora_inicio": horario.hora_inicio,
                    "hora_fim": horario.hora_fim,
                    "professor": horario.professor,
                    "dia_semana": horario.dia_semana,
                }
            )
        turmas.append(dados_turma)

    metadata["professores"] = [str(i) for i in professores]
    metadata["tipos_vaga"] = [str(i) for i in tipos_vaga]
    metadata["dias_semana_oferecida"] = [str(i) for i in dias_semana]
    metadata["horarios_oferecida"] = [str(i) for i in horas_aula]
    metadata["turmas_oferecidas"] = json.dumps(turmas, ensure_ascii=False)

    # converter seções numéricas
    for i in ["creditos_aula", "creditos_trabalho", "carga_horaria_total"]:
        metadata[i] = str(metadata[i]).split()[0]
        if metadata[i].isnumeric():
            metadata[i] = int(metadata[i])

    # converter seções de tipo inválido
    for k, v in metadata.items():
        if not isinstance(v, (int, str, list, float, bool)) and v != None:
            metadata[k] = None
            logger.warning("Chave '%s' dos metadados de '%s' tem tipo '%s' (foi convertida para None)", k, disciplina, type(v))
        if isinstance(v, list) and len(v) == 0:
            metadata[k] = None
            logger.warning("Chave '%s' dos metadados de '%s' é lista vazia (foi convertida para None)", k, disciplina)

    return metadata


def _obter_document_disciplina(disciplina: Disciplina, instituto: Instituto) -> str:
    """Retorna documento da `disciplina` a ser armazenado no banco de dados."""

    dados = disciplina.obter_dados()
    sections = []

    if "nome" in dados:
        sections.append(dados["nome"])
    if instituto:
        if "departamento" in dados:
            sections.append(f"{instituto.nome} ({instituto.abrev}) - {dados['departamento']}")
        else:
            sections.append(f"{instituto.nome} ({instituto.abrev})")
    for k in DISCIPLINA_DOCUMENT_CHAVES:
        if k in dados:
            sections.append(f"{k.capitalize()}: {str(dados[k]).strip()}")

    return "\n\n".join([str(i) for i in sections])


def _upsert_banco_disciplinas(ids: list[str], documents: list[str], metadatas: list[Metadata], num_lote: int) -> None:
    """Faz upsert de lote no banco de disciplinas."""

    collection = obter_banco_disciplinas()

    logger.debug("Lote %s: enviando %s disciplinas", num_lote, len(ids))
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    logger.info("Lote %s: enviou %s disciplinas (total no banco: %s)", num_lote, len(ids), collection.count())


def atualizar_banco_disciplinas(institutos: list[Instituto] | None = None, batch_size: int = 50) -> None:
    """
    Sincroniza o banco com as disciplinas atualmente oferecidas no Jupiterweb (pode
    demorar).

    Insere disciplinas novas, atualiza as já existentes e remove do banco as que já não
    estão sendo oferecidas ou que já não existem mais. As inserções/atualizações são
    feitas em lotes de tamanho `batch_size`, exceto pelo último que pode ser menor.

    Se `institutos` forem informados, restringe a sincronização às disciplinas desses
    institutos. Nesse caso, apenas elas são inseridas, atualizadas ou removidas, e o
    restante do banco não é alterado. Se `instituto=None`, considera todos os institutos
    do Jupiterweb, e o banco todo é atualizado.
    """

    if institutos is None:
        institutos = jupiterweb.obter_institutos()

    inicio = time.time()
    num_lotes = 0

    logger.info("Atualizando banco de disciplinas: %s institutos (lotes de %s)", len(institutos), batch_size)

    collection = obter_banco_disciplinas()
    ids_existentes = set(collection.get(where={"instituto_codigo": {"$in": [i.codigo for i in institutos]}})["ids"])
    ids_atualizados = set()
    logger.debug("Banco tem %s disciplinas de institutos selecionados para atualização", len(ids_existentes))

    ids = []
    documents = []
    metadatas = []

    for instituto in institutos:
        logger.debug("Extraindo disciplinas de '%s'", instituto)

        for disciplina in instituto.obter_disciplinas():
            try:
                disciplina.obter_dados()
            except Exception as e:  # noqa: BLE001
                logger.error("Erro ao obter dados da disciplina '%s' (ignorada): %s", disciplina, e)
                continue

            if not disciplina.encontrada():
                logger.debug("Disciplina '%s' não encontrada no Jupiterweb (ignorada)", disciplina)
                continue
            if not disciplina.possui_oferecimento():
                logger.debug("Disciplina '%s' sem oferecimento (ignorada)", disciplina)
                continue

            id_ = _obter_id_disciplina(disciplina)
            ids_atualizados.add(id_)
            ids.append(id_)
            documents.append(_obter_document_disciplina(disciplina, instituto))
            metadatas.append(_obter_metadata_disciplina(disciplina, instituto))
            logger.info("Lote %s: disciplina '%s' adicionada (%s/%s)", num_lotes + 1, disciplina, len(ids), batch_size)

            if len(ids) >= batch_size:
                _upsert_banco_disciplinas(ids, documents, metadatas, num_lotes + 1)

                num_lotes += 1
                ids.clear()
                documents.clear()
                metadatas.clear()
    if len(ids) > 0:
        _upsert_banco_disciplinas(ids, documents, metadatas, num_lotes + 1)
        num_lotes += 1

    ids_desatualizados = ids_existentes - ids_atualizados
    if ids_desatualizados:
        logger.info("Removendo %s disciplinas desatualizadas do banco (sem oferecimento ou inexistentes)", len(ids_desatualizados))
        for id_ in ids_desatualizados:
            logger.debug("Removendo disciplina desatualizada: '%s'", id_)
        collection.delete(ids=list(ids_desatualizados))

    duracao = time.time() - inicio
    logger.info(
        "Banco de disciplinas atualizado (em %.2fs): adicionadas/atualizadas: %s | removidas: %s | total no banco: %s",
        duracao,
        len(ids_atualizados),
        len(ids_desatualizados),
        collection.count(),
    )
