import json
from functools import lru_cache
from typing import Annotated, Any

from config import settings
from constants import (
    BUSCA_DEFAULT_RESULTADOS,
    BUSCA_EMENTA_RESUMO_MAX_CHARS,
    BUSCA_MAX_RESULTADOS,
    CampusDisciplina,
    MetaKey,
)
from db import obter_banco_disciplinas
from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openrouter import ChatOpenRouter
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field, field_validator
from utils import get_logger, truncar_texto

logger = get_logger(__name__)

# ----------------------------------- Tools ---------------------------------- #


@tool
def consultar_disciplinas(
    siglas: Annotated[
        list[str],
        Field(
            description=(
                "Lista de siglas exatas das disciplinas que devem ser consultadas. "
                "Informe uma ou mais siglas, sem nomes ou descrições das disciplinas. "
                "Não diferencia maiúsculas de minúsculas."
            )
        ),
    ],
) -> str:
    """Consulta informações detalhadas de uma ou mais disciplinas da USP a partir de suas siglas.

    Use esta ferramenta quando o usuário já souber a(s) sigla(s) exata(s) da(s)
    disciplina(s) (ex.: "MAC0110", "PCS3616") ou quando quiser se aprofundar em
    disciplinas encontradas anteriormente. Não use esta ferramenta para buscar
    disciplinas por tema ou assunto; nesse caso, utilize a ferramenta de busca
    de disciplinas.

    Se o usuário pedir informações sobre várias disciplinas, passe todas as
    siglas de uma vez nesta única chamada, em vez de chamar a ferramenta
    separadamente para cada uma.

    Retorna os metadados armazenados de cada disciplina encontrada, incluindo
    nome, instituto, campus, ementa, objetivos, conteúdo programático, créditos,
    carga horária, requisitos, período ideal, entre outros. Utilize apenas os
    campos relevantes para responder à pergunta do usuário; não é necessário
    listar todas as informações retornadas.

    Returns:
        String JSON contendo:
        - disciplinas: lista de objetos com todos os metadados das disciplinas
          encontradas, na mesma ordem das siglas informadas;
        - siglas_nao_encontradas: lista das siglas que não foram encontradas.
    """

    siglas = list(dict.fromkeys(s.strip().upper() for s in siglas if s.strip()))

    if not siglas:
        logger.warning("consultar_disciplinas: nenhuma sigla informada")
        return json.dumps({"disciplinas": [], "siglas_nao_encontradas": []}, ensure_ascii=False)

    logger.info("consultar_disciplinas: siglas=%s", siglas)

    resultado = obter_banco_disciplinas().get(ids=siglas, include=["metadatas"])
    metadados_por_sigla = dict(zip(resultado["ids"], resultado["metadatas"]))
    ids_encontrados = set(resultado["ids"])

    disciplinas = [
        {
            **(metadados_por_sigla[sigla] or {}),
            MetaKey.SIGLA: sigla,
        }
        for sigla in siglas
        if sigla in ids_encontrados
    ]

    resposta = {
        "disciplinas": disciplinas,
        "siglas_nao_encontradas": [sigla for sigla in siglas if sigla not in ids_encontrados],
    }

    logger.info("consultar_disciplinas: %s encontradas e %s não encontradas", len(resposta["disciplinas"]), len(resposta["siglas_nao_encontradas"]))
    return json.dumps(resposta, ensure_ascii=False, indent=2)


class FiltroDisciplinas(BaseModel):
    """Filtros opcionais para restringir a busca de disciplinas.

    Todas as condições informadas são combinadas por conjunção (AND):
    uma disciplina só é retornada se satisfizer simultaneamente todos
    os filtros preenchidos.

    Para cada atributo numérico, os limites mínimo e máximo, quando
    informados, definem um intervalo inclusivo. Se apenas um deles for
    informado, somente aquela restrição é aplicada.

    Campos None ou omitidos não impõem restrições. Não utilize 0 ou
    strings vazias para representar a ausência de um filtro.

    Os campos instituto_nome e instituto_abrev representam duas formas
    de identificar o mesmo instituto. Normalmente, basta informar um
    deles. Se ambos forem preenchidos, a disciplina deverá corresponder
    aos dois valores.
    """

    instituto_nome: str | None = Field(
        default=None,
        description=(
            "Nome completo e oficial do instituto responsável pela disciplina "
            "(ex.: 'Faculdade de Medicina Veterinária e Zootecnia'). "
            "Utilize o nome completo, não apenas parte dele."
        ),
    )

    instituto_abrev: str | None = Field(
        default=None,
        description=(
            "Abreviação do instituto responsável pela disciplina "
            "(ex.: 'IME', 'POLI', 'ESALQ'). Utilize a sigla sem o sufixo "
            "'-USP'. Maiúsculas e minúsculas são aceitas."
        ),
    )

    instituto_campus: CampusDisciplina | None = Field(
        default=None,
        description=("Campus da USP ao qual pertence o instituto responsável pela " "disciplina. Utilize um dos valores permitidos."),
    )

    creditos_aula_min: int | None = Field(
        default=None,
        ge=0,
        description=("Número mínimo de créditos-aula da disciplina, inclusive. " "Se None, não há restrição mínima."),
    )

    creditos_aula_max: int | None = Field(
        default=None,
        ge=0,
        description=("Número máximo de créditos-aula da disciplina, inclusive. " "Se None, não há restrição máxima."),
    )

    creditos_trabalho_min: int | None = Field(
        default=None,
        ge=0,
        description=("Número mínimo de créditos-trabalho da disciplina, inclusive. " "Se None, não há restrição mínima."),
    )

    creditos_trabalho_max: int | None = Field(
        default=None,
        ge=0,
        description=("Número máximo de créditos-trabalho da disciplina, inclusive. " "Se None, não há restrição máxima."),
    )

    carga_horaria_total_min: int | None = Field(
        default=None,
        ge=0,
        description=("Carga horária total mínima da disciplina, em horas, inclusive. " "Se None, não há restrição mínima."),
    )

    carga_horaria_total_max: int | None = Field(
        default=None,
        ge=0,
        description=("Carga horária total máxima da disciplina, em horas, inclusive. " "Se None, não há restrição máxima."),
    )

    @field_validator("instituto_nome", mode="before")
    @classmethod
    def normalizar_instituto_nome(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            return valor.strip() or None
        return valor

    @field_validator("instituto_abrev", mode="before")
    @classmethod
    def normalizar_instituto_abrev(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            valor = valor.strip().upper()
            valor = valor.removesuffix("-USP")
            return valor or None
        return valor

    def montar_where(self) -> dict[str, Any] | None:
        """Constrói o filtro where do ChromaDB equivalente aos filtros informados.

        Todas as condições são combinadas por conjunção (AND).
        Retorna None se nenhum filtro estiver preenchido.
        """

        condicoes: list[dict[str, Any]] = []

        if self.instituto_nome is not None:
            condicoes.append({MetaKey.INSTITUTO_NOME: self.instituto_nome})

        if self.instituto_abrev is not None:
            condicoes.append({MetaKey.INSTITUTO_ABREV: self.instituto_abrev})

        if self.instituto_campus is not None:
            condicoes.append({MetaKey.INSTITUTO_CAMPUS: self.instituto_campus.value})

        if self.creditos_aula_min is not None:
            condicoes.append({MetaKey.CREDITOS_AULA: {"$gte": self.creditos_aula_min}})

        if self.creditos_aula_max is not None:
            condicoes.append({MetaKey.CREDITOS_AULA: {"$lte": self.creditos_aula_max}})

        if self.creditos_trabalho_min is not None:
            condicoes.append({MetaKey.CREDITOS_TRABALHO: {"$gte": self.creditos_trabalho_min}})

        if self.creditos_trabalho_max is not None:
            condicoes.append({MetaKey.CREDITOS_TRABALHO: {"$lte": self.creditos_trabalho_max}})

        if self.carga_horaria_total_min is not None:
            condicoes.append({MetaKey.CARGA_HORARIA_TOTAL: {"$gte": self.carga_horaria_total_min}})

        if self.carga_horaria_total_max is not None:
            condicoes.append({MetaKey.CARGA_HORARIA_TOTAL: {"$lte": self.carga_horaria_total_max}})

        if not condicoes:
            return None

        if len(condicoes) == 1:
            return condicoes[0]

        return {"$and": condicoes}


@tool
def buscar_disciplinas(
    query: Annotated[
        str | None,
        Field(
            description=(
                "Palavras-chave e expressões curtas que representem os temas, "
                "conceitos ou áreas de interesse do usuário. Combine vários "
                "termos quando necessário. Não inclua siglas de disciplinas, "
                "filtros determinísticos ou a solicitação completa em linguagem "
                "natural. Utilize None quando a busca depender exclusivamente "
                "de filtros determinísticos."
            )
        ),
    ] = None,
    filtros: Annotated[
        FiltroDisciplinas | None,
        Field(
            description=(
                "Restrições determinísticas para limitar os resultados. "
                "Informe somente os critérios estabelecidos pelo usuário "
                "ou inferidos com segurança do contexto. Todas as condições "
                "preenchidas são aplicadas simultaneamente."
            )
        ),
    ] = None,
    n_resultados: Annotated[
        int,
        Field(
            ge=1,
            le=BUSCA_MAX_RESULTADOS,
            description=(
                f"Número máximo de disciplinas candidatas a retornar pela busca "
                f"(entre 1 e {BUSCA_MAX_RESULTADOS}). Não precisa corresponder à "
                "quantidade de disciplinas que será apresentada ao usuário. "
                "Se não houver uma necessidade específica, utilize o valor padrão."
            ),
        ),
    ] = BUSCA_DEFAULT_RESULTADOS,
) -> str:
    """Busca disciplinas da USP por similaridade semântica e filtros determinísticos.

    Use esta ferramenta quando o usuário quiser descobrir, encontrar, sugerir
    ou listar disciplinas com base em temas, assuntos, conceitos, áreas de
    interesse ou critérios específicos.

    Quando houver um assunto de interesse, formule a consulta utilizando
    palavras-chave e expressões curtas que representem os temas relevantes.
    Combine diferentes termos quando necessário. A busca semântica compara
    essas expressões com os nomes e o conteúdo das disciplinas, incluindo
    ementas, objetivos e conteúdo programático. Não utilize siglas isoladas
    como consulta semântica.

    Quando o usuário estabelecer critérios determinísticos, como instituto,
    campus, créditos ou carga horária, aplique-os por meio dos filtros.
    Todas as condições informadas devem ser satisfeitas simultaneamente.

    Se o usuário solicitar disciplinas apenas por critérios determinísticos,
    sem especificar um assunto de interesse, realize a busca utilizando
    exclusivamente os filtros, sem necessidade de consulta semântica.
    Nesse caso, informe ao parâmetro de consulta o valor None e forneça
    pelo menos um filtro.

    Utilize somente critérios explicitamente estabelecidos pelo usuário ou
    que possam ser inferidos com segurança do contexto da conversa. Ao
    refinar uma busca anterior, preserve os interesses e filtros que
    continuem pertinentes.

    A quantidade de resultados retornados pela ferramenta representa o conjunto
    de disciplinas candidatas à seleção, não necessariamente a quantidade que
    deve ser apresentada ao usuário. Analise os resultados e selecione aqueles
    mais relevantes para a solicitação, respeitando a quantidade solicitada
    pelo usuário quando houver uma.

    Quando houver consulta semântica, os resultados são ordenados do mais
    para o menos relevante em relação à consulta. Em buscas exclusivamente
    por filtros, não há ordenação por relevância semântica.

    Returns:
        String JSON contendo uma lista de disciplinas encontradas. Cada
        objeto contém:
        - sigla: sigla da disciplina;
        - nome: nome da disciplina;
        - instituto: abreviação do instituto responsável;
        - ementa: resumo da ementa.

        Quando houver consulta semântica, as disciplinas são ordenadas
        por relevância. Quando houver somente filtros, a ordem é a
        retornada pelo banco de dados.

        Retorna uma lista vazia ("[]") quando nenhuma disciplina satisfizer
        a consulta e os filtros. Se nem consulta nem filtros forem
        fornecidos, retorna um objeto JSON com a chave "erro".
    """

    if query is not None:
        query = query.strip() or None

    where = filtros.montar_where() if filtros is not None else None

    if query is None and where is None:
        logger.warning("buscar_disciplinas: consulta e filtros ausentes")
        return json.dumps(
            {"erro": "Informe uma consulta semântica ou pelo menos um filtro."},
            ensure_ascii=False,
        )

    logger.info("buscar_disciplinas: query='%s', filtros='%s'", query, where)
    collection = obter_banco_disciplinas()

    if query is not None:
        resultado = collection.query(query_texts=[query], n_results=n_resultados, where=where, include=["metadatas"])
        ids = resultado["ids"][0] if resultado["ids"] else []
        metadados = resultado["metadatas"][0] if resultado["metadatas"] and resultado["metadatas"][0] else []
    else:
        resultado = collection.get(where=where, limit=n_resultados, include=["metadatas"])
        ids = resultado["ids"]
        metadados = resultado["metadatas"] or []

    if not ids:
        logger.warning("buscar_disciplinas: nenhuma encontrada")
        return json.dumps([], ensure_ascii=False)

    saida = []

    for i, sigla in enumerate(ids):
        metadata = metadados[i] if i < len(metadados) else {}
        metadata = metadata or {}

        item = {
            "sigla": sigla,
            "nome": metadata.get(MetaKey.NOME) or "",
            "instituto": metadata.get(MetaKey.INSTITUTO_ABREV) or "",
            "ementa": truncar_texto(metadata.get(MetaKey.EMENTA) or "", BUSCA_EMENTA_RESUMO_MAX_CHARS),
        }

        saida.append(item)

    logger.info("buscar_disciplinas: %s encontradas", len(saida))
    return json.dumps(saida, ensure_ascii=False, indent=2)


# --------------------------------- Interação -------------------------------- #


def _extrair_texto_resposta(conteudo: Any) -> str:
    """Extrai o texto de uma resposta do modelo."""

    if isinstance(conteudo, str):
        return conteudo

    if isinstance(conteudo, list):
        partes = []

        for bloco in conteudo:
            if isinstance(bloco, str):
                partes.append(bloco)
            elif isinstance(bloco, dict):
                tipo = bloco.get("type")
                texto = bloco.get("text")

                if tipo in (None, "text") and isinstance(texto, str):
                    partes.append(texto)

        return "\n".join(partes)

    return ""


@lru_cache
def obter_agent() -> CompiledStateGraph:
    """Retorna novo agente do Hermes (única instância, criada na primeira
    chamada)."""

    model = ChatOpenRouter(
        model=settings.agent_model,
        api_key=settings.openrouter_api_key.get_secret_value(),
    )

    return create_agent(
        model=model,
        tools=[consultar_disciplinas, buscar_disciplinas],
        system_prompt=settings.system_prompt_path.read_text(encoding="utf-8"),
        checkpointer=InMemorySaver(),
    )


def obter_resposta(mensagem: str, conversa_id: str) -> str:
    """Envia mensagem para agente na conversa especificada, e retorna a sua
    resposta em texto."""

    agent = obter_agent()
    config: RunnableConfig = {"configurable": {"thread_id": conversa_id}}

    resultado = agent.invoke(
        {"messages": [{"role": "user", "content": mensagem}]},
        config=config,
    )

    return _extrair_texto_resposta(resultado)
