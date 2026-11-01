import json
import logging
import time

import chromadb
import jupiterweb
from chromadb.api import ClientAPI
from chromadb.api.types import Metadata
from chromadb.utils import embedding_functions
from config import settings
from constants import (
    DB_COLLECTION_NAME,
    DB_DISTANCE_METRIC,
    DB_DOCUMENT_CHAVES,
    DB_EMBEDDING_NORMALIZE,
    DB_UPSERT_BATCH_SIZE,
    MetaKey,
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
        _client = chromadb.PersistentClient(path=str(settings.db_path))
        logger.info("Client ChromaDB inicializado em '%s'", settings.db_path)
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
            model_name=settings.embedding_model,
            device=settings.embedding_device,
            normalize_embeddings=DB_EMBEDDING_NORMALIZE,
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
        MetaKey.SIGLA: disciplina.sigla,
        MetaKey.INSTITUTO_NOME: instituto.nome,
        MetaKey.INSTITUTO_ABREV: instituto.abrev.upper(),
        MetaKey.INSTITUTO_CODIGO: instituto.codigo,
        MetaKey.INSTITUTO_CAMPUS: instituto.campus,
        MetaKey.DEPARTAMENTO: dados.get("departamento", ""),
        MetaKey.NOME: dados.get("nome", ""),
        MetaKey.NOME_INGLES: dados.get("nome ingles", ""),
        MetaKey.CREDITOS_AULA: dados.get("creditos aula", "0"),
        MetaKey.CREDITOS_TRABALHO: dados.get("creditos trabalho", "0"),
        MetaKey.CARGA_HORARIA_TOTAL: dados.get("carga horaria total", "0"),
        MetaKey.TIPO: dados.get("tipo", ""),
        MetaKey.ATIVACAO: dados.get("ativacao", ""),
        MetaKey.DESATIVACAO: dados.get("desativacao", ""),
        MetaKey.EMENTA: dados.get("ementa", ""),
        MetaKey.OBJETIVOS: dados.get("objetivos", ""),
        MetaKey.CONTEUDO_PROGRAMATICO: dados.get("conteudo programatico", ""),
        MetaKey.AVALIACAO_METODO: dados.get("instrumentos e criterios de avaliacao", {}).get("metodo de avaliacao", ""),
        MetaKey.AVALIACAO_CRITERIO: dados.get("instrumentos e criterios de avaliacao", {}).get("criterio de avaliacao", ""),
        MetaKey.AVALIACAO_NORMA_RECUP: dados.get("instrumentos e criterios de avaliacao", {}).get("norma de recuperacao", ""),
        MetaKey.DOCENTES_RESPONSAVEIS: dados.get("docente(s) responsavel(eis)", ""),
        MetaKey.URL_PRINCIPAL: disciplina.url_principal,
        MetaKey.URL_OFERECIMENTO: disciplina.url_oferecimento,
        MetaKey.URL_REQUISITOS: disciplina.url_requisitos,
        MetaKey.ULTIMA_ATUALIZACAO: time.time(),
    }

    # seção unificada de bibliografia
    metadata[MetaKey.BIBLIOGRAFIA] = ""
    if "bibliografia" in dados:
        metadata[MetaKey.BIBLIOGRAFIA] += dados["bibliografia"] + "\n"
    if "bibliografia basica" in dados:
        metadata[MetaKey.BIBLIOGRAFIA] += "bibliografia basica:\n" + dados["bibliografia basica"] + "\n"
    if "bibliografia complementar" in dados:
        metadata[MetaKey.BIBLIOGRAFIA] += "bibliografia complementar:\n" + dados["bibliografia complementar"] + "\n"

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

    metadata[MetaKey.PROFESSORES] = [str(i) for i in professores]
    metadata[MetaKey.TIPOS_VAGA] = [str(i) for i in tipos_vaga]
    metadata[MetaKey.DIAS_SEMANA_OFERECIDA] = [str(i) for i in dias_semana]
    metadata[MetaKey.HORARIOS_OFERECIDA] = [str(i) for i in horas_aula]
    metadata[MetaKey.TURMAS_OFERECIDAS] = json.dumps(turmas, ensure_ascii=False)

    # converter seções numéricas
    for i in [MetaKey.CREDITOS_AULA, MetaKey.CREDITOS_TRABALHO, MetaKey.CARGA_HORARIA_TOTAL]:
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
    for k in DB_DOCUMENT_CHAVES:
        if k in dados:
            sections.append(f"{k.capitalize()}: {str(dados[k]).strip()}")

    return "\n\n".join([str(i) for i in sections])


def _upsert_banco_disciplinas(ids: list[str], documents: list[str], metadatas: list[Metadata], num_lote: int) -> None:
    """Faz upsert de lote no banco de disciplinas."""

    collection = obter_banco_disciplinas()

    logger.debug("Lote %s: enviando %s disciplinas", num_lote, len(ids))
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    logger.info("Lote %s: enviou %s disciplinas (total no banco: %s)", num_lote, len(ids), collection.count())


def atualizar_banco_disciplinas(institutos: list[Instituto] | None = None, batch_size: int = DB_UPSERT_BATCH_SIZE) -> None:
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
    ids_existentes = set(collection.get(where={MetaKey.INSTITUTO_CODIGO: {"$in": [i.codigo for i in institutos]}})["ids"])
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
