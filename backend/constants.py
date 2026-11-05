from enum import Enum
from typing import Final

# ---------------------------------- Logs ------------------------------------ #
LOG_MAX_BYTES: Final = 5 * 1024 * 1024
LOG_BACKUP_COUNT: Final = 3
LOG_FORMAT: Final = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT: Final = "%Y-%m-%d %H:%M:%S"

# ------------------------------ Banco de Dados ------------------------------ #
DB_COLLECTION_NAME: Final = "disciplinas_jupiterweb"
DB_DISTANCE_METRIC: Final = "cosine"
DB_EMBEDDING_NORMALIZE: Final = True  # para similaridade por cosseno
DB_UPSERT_BATCH_SIZE: Final = 50
DB_DELETE_BATCH_SIZE: Final = 50
DB_BIBLIOGRAFIA_SECOES = (
    ("bibliografia", ""),
    ("bibliografia basica", "Bibliografia básica"),
    ("bibliografia complementar", "Bibliografia complementar"),
)
DB_DOCUMENT_SECOES: Final = (
    ("ementa", "Ementa", 2000),
    ("objetivos", "Objetivos", 1500),
    ("conteudo programatico", "Conteúdo programático", 2500),
)

# ---------------------------------- Busca ----------------------------------- #
BUSCA_MAX_RESULTADOS: Final = 20
BUSCA_DEFAULT_RESULTADOS: Final = 10
BUSCA_EMENTA_RESUMO_MAX_CHARS: Final = 200


class MetaKey:
    """Chaves dos metadados no ChromaDB (fonte única para db.py e agent.py)."""

    SIGLA: Final = "sigla"
    NOME: Final = "nome"
    NOME_INGLES: Final = "nome_ingles"
    INSTITUTO_NOME: Final = "instituto_nome"
    INSTITUTO_ABREV: Final = "instituto_abrev"
    INSTITUTO_CODIGO: Final = "instituto_codigo"
    INSTITUTO_CAMPUS: Final = "instituto_campus"
    DEPARTAMENTO: Final = "departamento"
    CREDITOS_AULA: Final = "creditos_aula"
    CREDITOS_TRABALHO: Final = "creditos_trabalho"
    CREDITOS_TOTAL: Final = "creditos_total"
    CARGA_HORARIA_TOTAL: Final = "carga_horaria_total"
    TIPO: Final = "tipo"
    ATIVACAO: Final = "ativacao"
    DESATIVACAO: Final = "desativacao"
    EMENTA: Final = "ementa"
    OBJETIVOS: Final = "objetivos"
    CONTEUDO_PROGRAMATICO: Final = "conteudo_programatico"
    DOCENTES_RESPONSAVEIS: Final = "docentes_responsaveis"
    AVALIACAO_METODO: Final = "avaliacao_metodo"
    AVALIACAO_CRITERIO: Final = "avaliacao_criterio"
    AVALIACAO_NORMA_RECUP: Final = "avaliacao_norma_recup"
    BIBLIOGRAFIA: Final = "bibliografia"
    TEM_REQUISITOS: Final = "tem_requisitos"
    REQUISITOS_JSON: Final = "requisitos_json"
    PERIODO_IDEAL_JSON: Final = "periodo_ideal_json"
    URL_PRINCIPAL: Final = "url_principal"
    URL_OFERECIMENTO: Final = "url_oferecimento"
    URL_REQUISITOS: Final = "url_requisitos"
    URL_LISTAGEM_INSTITUTO: Final = "url_listagem_instituto"
    ULTIMA_ATUALIZACAO: Final = "ultima_atualizacao"


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
