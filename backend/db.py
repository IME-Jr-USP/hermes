import json
import logging
import time
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.types import Metadata
from chromadb.utils import embedding_functions
from config import settings
from constants import (
    DB_BIBLIOGRAFIA_SECOES,
    DB_COLLECTION_NAME,
    DB_DELETE_BATCH_SIZE,
    DB_DISTANCE_METRIC,
    DB_DOCUMENT_SECOES,
    DB_EMBEDDING_NORMALIZE,
    DB_UPSERT_BATCH_SIZE,
    MetaKey,
)
from jupiterweb import Disciplina, Instituto, obter_instituto, obter_institutos
from utils import (
    agora_iso,
    get_logger,
    limpar_metadata,
    limpar_texto,
    serializar_requisitos,
    texto_para_int,
    truncar_texto,
)

logger = get_logger(__name__)
logging.getLogger("sentence_transformers").setLevel(logging.INFO)


# ---------------------------------- Acesso ---------------------------------- #


@lru_cache
def obter_client() -> ClientAPI:
    """Devolve o cliente do ChromaDB (única instância, criada na primeira chamada)."""

    client = chromadb.PersistentClient(path=str(settings.db_path))
    logger.info("Cliente do ChromaDB criado em %s", settings.db_path)
    return client


@lru_cache
def obter_banco_disciplinas() -> chromadb.Collection:
    """Devolve a coleção de disciplinas do ChromaDB (única instância, criada na primeira chamada)."""

    client = obter_client()

    logger.debug("Criando função de embedding com modelo %s (%s)", settings.embedding_model, settings.embedding_device)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
        normalize_embeddings=DB_EMBEDDING_NORMALIZE,
    )

    logger.debug("Obtendo coleção de disciplinas do ChromaDB: %s", DB_COLLECTION_NAME)
    collection = client.get_or_create_collection(
        name=DB_COLLECTION_NAME,
        embedding_function=ef,  # pyright: ignore[reportArgumentType]
        configuration={"hnsw": {"space": DB_DISTANCE_METRIC}},
    )

    logger.info("Obteve coleção de disciplinas do ChromaDB: %s", DB_COLLECTION_NAME)
    return collection


# ---------------------------- Conversão de dados ---------------------------- #


def _obter_id_disciplina(disciplina: Disciplina) -> str:
    """Devolve o ID da disciplina para ser usado no banco de dados."""

    return disciplina.sigla.upper().strip()


def _obter_metadata_disciplina(disciplina: Disciplina) -> Metadata:
    """Devolve os metadados da disciplina para serem usados no banco de dados."""

    dados = disciplina.obter_dados()
    instituto = obter_instituto(disciplina.codigo_instituto) if disciplina.codigo_instituto else None

    metadata = {}

    # identificação
    metadata[MetaKey.SIGLA] = disciplina.sigla
    metadata[MetaKey.NOME] = limpar_texto(dados.get("nome"))
    metadata[MetaKey.NOME_INGLES] = limpar_texto(dados.get("nome ingles"))

    # instituto
    metadata[MetaKey.INSTITUTO_NOME] = instituto.nome if instituto else None
    metadata[MetaKey.INSTITUTO_ABREV] = instituto.abrev if instituto else None
    metadata[MetaKey.INSTITUTO_CODIGO] = instituto.codigo if instituto else None
    metadata[MetaKey.INSTITUTO_CAMPUS] = instituto.campus if instituto else None
    metadata[MetaKey.DEPARTAMENTO] = limpar_texto(dados.get("departamento"))

    # créditos e tipo
    metadata[MetaKey.CREDITOS_AULA] = texto_para_int(dados.get("creditos aula"), 0)
    metadata[MetaKey.CREDITOS_TRABALHO] = texto_para_int(dados.get("creditos trabalho"), 0)
    metadata[MetaKey.CREDITOS_TOTAL] = metadata[MetaKey.CREDITOS_AULA] + metadata[MetaKey.CREDITOS_TRABALHO]
    metadata[MetaKey.CARGA_HORARIA_TOTAL] = texto_para_int(dados.get("carga horaria total"))
    metadata[MetaKey.TIPO] = limpar_texto(dados.get("tipo"))

    # ativação e desativação
    metadata[MetaKey.ATIVACAO] = limpar_texto(dados.get("ativacao"))
    metadata[MetaKey.DESATIVACAO] = limpar_texto(dados.get("desativacao"))

    # conteúdo (para exibição)
    metadata[MetaKey.EMENTA] = limpar_texto(dados.get("ementa"))
    metadata[MetaKey.OBJETIVOS] = limpar_texto(dados.get("objetivos"))
    metadata[MetaKey.CONTEUDO_PROGRAMATICO] = limpar_texto(dados.get("conteudo programatico"))
    metadata[MetaKey.DOCENTES_RESPONSAVEIS] = limpar_texto(dados.get("docente(s) responsavel(eis)"))

    # método de avaliação
    avaliacao = dados.get("instrumentos e criterios de avaliacao", {})
    if not isinstance(avaliacao, dict):
        avaliacao = {"metodo de avaliacao": avaliacao}

    metadata[MetaKey.AVALIACAO_METODO] = limpar_texto(avaliacao.get("metodo de avaliacao"))
    metadata[MetaKey.AVALIACAO_CRITERIO] = limpar_texto(avaliacao.get("criterio de avaliacao"))
    metadata[MetaKey.AVALIACAO_NORMA_RECUP] = limpar_texto(avaliacao.get("norma de recuperacao"))

    # bibliografia
    bibliografia = []
    for chave, rotulo in DB_BIBLIOGRAFIA_SECOES:
        texto = limpar_texto(dados.get(chave))
        if texto:
            bibliografia.append(f"{rotulo}:\n{texto}" if rotulo else texto)
    metadata[MetaKey.BIBLIOGRAFIA] = "\n\n".join(bibliografia)

    # requisitos e período ideal
    requisitos = dados.get("requisitos", {})
    periodo_ideal = dados.get("periodo ideal", {})

    metadata[MetaKey.TEM_REQUISITOS] = bool(requisitos)
    metadata[MetaKey.REQUISITOS_JSON] = serializar_requisitos(requisitos)
    metadata[MetaKey.PERIODO_IDEAL_JSON] = json.dumps(periodo_ideal, ensure_ascii=False) if periodo_ideal else None

    # TODO: oferecimentos (horários, turmas e professores)

    # urls
    metadata[MetaKey.URL_PRINCIPAL] = disciplina.url_principal
    metadata[MetaKey.URL_REQUISITOS] = disciplina.url_requisitos
    metadata[MetaKey.URL_OFERECIMENTO] = disciplina.url_oferecimento
    metadata[MetaKey.URL_LISTAGEM_INSTITUTO] = instituto.url_listagem if instituto else None

    # outros
    metadata[MetaKey.ULTIMA_ATUALIZACAO] = time.time()

    return limpar_metadata(metadata, disciplina)


def _obter_document_disciplina(disciplina: Disciplina) -> str:
    """Devolve o documento da disciplina para ser usado no banco de dados."""

    dados = disciplina.obter_dados()

    nome = limpar_texto(dados.get("nome"))
    instituto = obter_instituto(disciplina.codigo_instituto).nome if disciplina.codigo_instituto else limpar_texto(dados.get("instituto"))
    departamento = limpar_texto(dados.get("departamento"))

    titulo = f"Disciplina: {nome}"
    if instituto:
        titulo += f"\nInstituto: {instituto}"
    if departamento:
        titulo += f"\nDepartamento: {departamento}"

    secoes = [titulo]

    for chave, rotulo, limite in DB_DOCUMENT_SECOES:
        texto = limpar_texto(dados.get(chave))
        secoes.append(f"{rotulo}: {truncar_texto(texto, limite)}")

    return "\n\n".join(secoes)


# ----------------------------- Operações básicas ---------------------------- #


@dataclass
class ResultadoOperacao:
    ok: list[str]
    falhas: dict[str, str]  # {id: mensagem de erro}


def _gravar_lote(disciplinas: Iterable[Disciplina]) -> None:
    """Grava um lote de disciplinas no banco de dados de uma vez. Usado
    internamente por `upsert_disciplinas()`."""

    disciplinas = list(disciplinas)

    ids = [_obter_id_disciplina(d) for d in disciplinas]
    metadatas = [_obter_metadata_disciplina(d) for d in disciplinas]
    documents = [_obter_document_disciplina(d) for d in disciplinas]

    collection = obter_banco_disciplinas()
    collection.upsert(ids=ids, metadatas=metadatas, documents=documents)


def _apagar_lote(disciplinas: Iterable[Disciplina]) -> None:
    """Apaga um lote de disciplinas do banco de dados de uma vez. Usado
    internamente por `delete_disciplinas()`."""

    ids = list({_obter_id_disciplina(d) for d in disciplinas})
    collection = obter_banco_disciplinas()
    collection.delete(ids=ids)


def upsert_disciplinas(disciplinas: Iterable[Disciplina], batch_size: int = DB_UPSERT_BATCH_SIZE) -> ResultadoOperacao:
    """Insere ou atualiza disciplinas no banco de dados em lotes."""

    disciplinas = list(disciplinas)
    resultado = ResultadoOperacao(ok=[], falhas={})

    for i in range(0, len(disciplinas), batch_size):
        batch = disciplinas[i : i + batch_size]

        try:
            _gravar_lote(batch)
            resultado.ok.extend([_obter_id_disciplina(d) for d in batch])
        except Exception as e:
            logger.exception("Falha ao gravar lote de disciplinas: %s", [d.sigla for d in batch])
            for d in batch:
                resultado.falhas[_obter_id_disciplina(d)] = str(e)

    return resultado


def delete_disciplinas(disciplinas: Iterable[Disciplina], batch_size: int = DB_DELETE_BATCH_SIZE) -> ResultadoOperacao:
    """Exclui disciplinas do banco de dados em lotes."""

    disciplinas = list(disciplinas)
    resultado = ResultadoOperacao(ok=[], falhas={})

    for i in range(0, len(disciplinas), batch_size):
        batch = disciplinas[i : i + batch_size]

        try:
            _apagar_lote(batch)
            resultado.ok.extend([_obter_id_disciplina(d) for d in batch])
        except Exception as e:
            logger.exception("Falha ao apagar lote de disciplinas: %s", [d.sigla for d in batch])
            for d in batch:
                resultado.falhas[_obter_id_disciplina(d)] = str(e)

    return resultado


# ----------------------------- Registro externo ----------------------------- #


class StatusDisciplina(StrEnum):
    """Status de uma disciplina em uma run de atualização do banco de dados."""

    PENDENTE = "pendente"
    CONCLUIDA = "concluida"
    FALHA = "falha"


class StatusRun(StrEnum):
    """Status de uma run de atualização do banco de dados."""

    EM_ANDAMENTO = "em_andamento"
    COMPLETA = "completa"


class DadosRun(TypedDict):
    """Dados de uma run de atualização do banco de dados."""

    status: StatusRun
    iniciada_em: str
    finalizada_em: str | None
    pendentes: list[str]
    concluidas: list[str]
    falhas: dict[str, str]
    codigos_institutos: dict[str, str]  # relaciona disciplinas aos institutos que as oferecem


def _gerar_run_id() -> str:
    """Gera um ID único para uma run de atualização do banco de dados."""

    i = 1
    while _run_path(f"run-{i}").exists():
        i += 1
    return f"run-{i}"


def _run_path(run_id: str) -> Path:
    """Devolve o caminho da run de atualização do banco de dados."""

    return settings.runs_path / f"{run_id}.json"


def _ler_run(run_id: str) -> DadosRun:
    """Lê o arquivo de status da run de atualização do banco de dados."""

    return json.loads(_run_path(run_id).read_text(encoding="utf-8"))


def _gravar_run(run_id: str, dados: DadosRun) -> None:
    """Reescreve dados no arquivo de status da run de atualização do banco de
    dados. Cria o arquivo se não existir."""

    path = _run_path(run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


# ---------------------------- Operações de rotina --------------------------- #


def _processar_pendentes(run_id: str, batch_size: int = DB_UPSERT_BATCH_SIZE) -> None:
    """Processa as disciplinas pendentes de uma run de atualização do banco de
    dados, em lotes, gravando o progresso da run após cada lote. Não atualiza o
    status da run. Usada internamente por `retomar_run()`."""

    dados = _ler_run(run_id)
    if not dados["pendentes"]:
        return

    total = len(dados["pendentes"])
    num_lotes = (total + batch_size - 1) // batch_size
    logger.info("Processando %s pendentes de %s (%s lotes de %s)", total, run_id, num_lotes, batch_size)

    for n in range(1, num_lotes + 1):
        batch = dados["pendentes"][:batch_size]
        dados["pendentes"] = dados["pendentes"][batch_size:]

        disciplinas = [Disciplina(s, codigo_instituto=dados["codigos_institutos"].get(s)) for s in batch]
        logger.debug("Lote %s/%s (%s): obtendo dados das %s disciplinas", n, num_lotes, run_id, len(disciplinas))

        existentes: list[Disciplina] = []
        inexistentes: list[Disciplina] = []

        for i in range(len(disciplinas)):
            d = disciplinas[i]

            logger.debug("Lote %s/%s (%s): obtendo dados da disciplina %s (%s/%s)", n, num_lotes, run_id, d.sigla, i + 1, len(disciplinas))
            d.obter_dados()

            if d.encontrada():
                existentes.append(d)
            else:
                inexistentes.append(d)
                logger.warning("Disciplina %s não encontrada no Jupiterweb (não será gravada)", d.sigla)

        logger.debug(
            "Lote %s/%s (%s): enviando %s disciplinas encontradas (%s inexistentes)", n, num_lotes, run_id, len(existentes), len(inexistentes)
        )
        resultado = upsert_disciplinas(existentes, batch_size=batch_size)

        dados["concluidas"].extend(resultado.ok)
        dados["falhas"].update(resultado.falhas)

        if len(batch) > 1 and not existentes:  # lote sem disciplinas existentes (suspeita de erro no site)
            dados["falhas"].update({d.sigla: "pertence a lote com apenas disciplinas inexistentes (suspeita de site instável)" for d in inexistentes})
            logger.warning("Lote %s/%s (%s): nenhuma disciplina encontrada; registradas como falha (suspeita de site instável)", n, num_lotes, run_id)
        else:
            dados["concluidas"].extend(d.sigla for d in inexistentes)  # disciplinas inexistentes são consideradas processadas

        _gravar_run(run_id, dados)
        logger.info("Lote %s/%s (%s): processado (%s enviadas, %s falhas)", n, num_lotes, run_id, len(resultado.ok), len(resultado.falhas))

    logger.info("Pendentes de %s processadas: restam %s pendentes e %s falhas", run_id, len(dados["pendentes"]), len(dados["falhas"]))


def _processar_falhas(run_id: str) -> None:
    """Marca as disciplinas que falharam de uma run de atualização do banco de
    dados como pendentes novamente, e tenta reprocessá-las. Não atualiza o
    status da run. Usada internamente por `retomar_run()`."""

    dados = _ler_run(run_id)
    if not dados["falhas"]:
        return

    logger.info("Reprocessando %s disciplinas que falharam em %s (tornam-se pendentes)", len(dados["falhas"]), run_id)

    dados["pendentes"].extend(dados["falhas"].keys())
    dados["falhas"] = {}
    _gravar_run(run_id, dados)
    _processar_pendentes(run_id, batch_size=1)


def criar_run(disciplinas: Iterable[Disciplina]) -> str:
    """
    Cria uma run para atualizar o banco de dados com as disciplinas
    fornecidas. Retorna o ID da run.

    A run é criada com status "em andamento", e as disciplinas são marcadas como
    pendentes. A função não processa as disciplinas, apenas cria o registro da run. Para
    processar as disciplinas, use `retomar_run()`.

    É preferível que as disciplinas passadas tenham o atributo `codigo_instituto` preenchido,
    para ser utilizado como metadado no banco de dados.
    """

    disciplinas = list(disciplinas)
    siglas_disciplinas = list({d.sigla for d in disciplinas})
    codigos_institutos = {d.sigla: d.codigo_instituto for d in disciplinas}

    run_id = _gerar_run_id()
    path = _run_path(run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=False)

    dados: DadosRun = {
        "status": StatusRun.EM_ANDAMENTO,
        "iniciada_em": agora_iso(),
        "finalizada_em": None,
        "concluidas": [],
        "falhas": {},
        "pendentes": siglas_disciplinas,
        "codigos_institutos": codigos_institutos,
    }

    _gravar_run(run_id, dados)
    logger.info("Criada nova run de atualização do banco de dados: %s (%s disciplinas)", run_id, len(siglas_disciplinas))
    return run_id


def retomar_run(run_id: str, batch_size: int = DB_UPSERT_BATCH_SIZE) -> StatusRun:
    """
    Retoma/começa uma run de atualização do banco de dados. Se a run estiver
    completa, não faz nada. Se a run estiver em andamento, processa as
    disciplinas pendentes, e depois tenta reprocessar as disciplinas que
    falharam. No final, se não houverem disciplinas pendentes ou falhas, marca a
    run como completa.
    """

    dados = _ler_run(run_id)
    if dados["status"] == StatusRun.COMPLETA:
        logger.info("Run de atualização %s já está completa", run_id)
        return StatusRun.COMPLETA

    start = time.time()

    dados["status"] = StatusRun.EM_ANDAMENTO
    logger.info(
        "Retomando run de atualização %s: %s concluídas, %s pendentes, %s falhas",
        run_id,
        len(dados["concluidas"]),
        len(dados["pendentes"]),
        len(dados["falhas"]),
    )

    _processar_pendentes(run_id, batch_size)
    _processar_falhas(run_id)

    dados = _ler_run(run_id)  # estado atualizado
    if dados["pendentes"] or dados["falhas"]:
        logger.warning(
            "Run de atualização %s não foi concluída: %s concluídas, %s pendentes, %s falhas",
            run_id,
            len(dados["concluidas"]),
            len(dados["pendentes"]),
            len(dados["falhas"]),
        )
        return StatusRun.EM_ANDAMENTO

    dados["status"] = StatusRun.COMPLETA
    dados["finalizada_em"] = agora_iso()
    _gravar_run(run_id, dados)
    logger.info("Run de atualização %s concluída (em %.1f segundos)", run_id, time.time() - start)

    return StatusRun.COMPLETA


def sincronizar_disciplinas(institutos: Iterable[Instituto] | None = None, batch_size: int = DB_UPSERT_BATCH_SIZE) -> str:
    """
    Sincroniza o banco de dados com o Jupiterweb (pode demorar). Se `institutos`
    for fornecido, apenas disciplinas desses institutos serão sincronizadas.
    Retorna run_id da run de atualização do banco de dados utilizado para a sincronização.
    """

    # TODO: filtrar por oferecidas apenas

    institutos = list(institutos) if institutos else obter_institutos()

    logger.info("Obtendo disciplinas de %s institutos para sincronização", len(institutos))

    disciplinas = []
    for i in institutos:
        logger.debug("Obtendo disciplinas do instituto %s (%s)", i.codigo, i.nome)
        disciplinas_instituto = i.obter_disciplinas()

        disciplinas.extend(disciplinas_instituto)
        logger.debug("Obtidas %s disciplinas do instituto %s (%s)", len(disciplinas_instituto), i.codigo, i.nome)

    run_id = criar_run(disciplinas)
    retomar_run(run_id, batch_size)
    return run_id
