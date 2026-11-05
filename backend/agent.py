import json
from enum import Enum
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
    """Consulta informações detalhadas de uma ou mais disciplinas da USP a
    partir de suas siglas.

    Use esta ferramenta quando o usuário informar a(s) sigla(s) exata(s) da(s)
    disciplina(s) (ex.: "MAC0110", "PCS3616") ou quando precisar obter
    informações adicionais sobre disciplinas encontradas anteriormente por meio
    da ferramenta de busca. Não utilize esta ferramenta para encontrar
    disciplinas por tema ou assunto; nesse caso, utilize a ferramenta de busca
    de disciplinas.

    Consultas em lote: sempre que precisar consultar informações de várias
    disciplinas, reúna todas as siglas e envie-as em uma única chamada desta
    ferramenta. Não faça chamadas individuais para cada disciplina quando for
    possível consultá-las conjuntamente. Ao selecionar disciplinas encontradas
    em uma busca anterior, determine primeiro quais delas são relevantes para a
    solicitação do usuário e consulte todas as selecionadas de uma só vez. Faça
    chamadas adicionais somente se surgir a necessidade de consultar outras
    disciplinas que não estavam incluídas na consulta anterior.

    Retorna os metadados armazenados de cada disciplina encontrada, incluindo
    nome, instituto, campus, ementa, objetivos, conteúdo programático, créditos,
    carga horária, requisitos, período ideal, entre outros. Utilize apenas os
    campos relevantes para responder à pergunta do usuário; não é necessário
    listar todas as informações retornadas.

    Returns:
        String JSON contendo:
        - disciplinas: lista de objetos com todos os metadados das disciplinas encontradas, na mesma ordem das siglas informadas;
        - siglas_nao_encontradas: lista das siglas informadas que não foram encontradas.
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

    Todas as condições de atributos diferentes são combinadas por
    conjunção (AND). Uma disciplina só é retornada se satisfizer
    simultaneamente todos os filtros preenchidos.

    Para atributos representados por listas, basta corresponder a um
    dos valores informados (OR).

    Os atributos instituto_nomes, instituto_abrevs e instituto_campi
    aceitam múltiplos valores. Se instituto_nomes e instituto_abrevs
    forem preenchidos simultaneamente, ambas as condições deverão ser
    satisfeitas.

    Para cada atributo numérico, os limites mínimo e máximo, quando
    informados, definem um intervalo inclusivo. Se apenas um deles
    for informado, somente aquela restrição é aplicada.

    Campos None ou omitidos não impõem restrições. Listas vazias e
    strings vazias também são tratadas como ausência de filtro.
    """

    instituto_nomes: list[str] | None = Field(
        default=None,
        description=("Lista de nomes completos dos institutos responsáveis pelas disciplinas. " "Basta pertencer a um dos institutos informados."),
    )

    instituto_abrevs: list[str] | None = Field(
        default=None,
        description=(
            "Lista de abreviações dos institutos responsáveis pelas disciplinas "
            "(ex.: ['IME', 'POLI']). Basta pertencer a um dos institutos informados."
        ),
    )

    instituto_campi: list[CampusDisciplina] | None = Field(
        default=None,
        description=(
            "Lista de campi onde os institutos responsáveis pelas disciplinas " "estão localizados. Basta corresponder a um dos campi informados."
        ),
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

    creditos_total_min: int | None = Field(
        default=None,
        ge=0,
        description=(
            "Número mínimo de créditos totais da disciplina, inclusive. "
            "Créditos totais correspondem à soma dos créditos-aula e dos "
            "créditos-trabalho. Use este campo quando o usuário mencionar "
            "créditos sem especificar créditos-aula ou créditos-trabalho,"
            "ou quando mencionar créditos totais."
        ),
    )

    creditos_total_max: int | None = Field(
        default=None,
        ge=0,
        description=(
            "Número máximo de créditos totais da disciplina, inclusive. "
            "Créditos totais correspondem à soma dos créditos-aula e dos "
            "créditos-trabalho. Use este campo quando o usuário mencionar "
            "créditos sem especificar créditos-aula ou créditos-trabalho,"
            "ou quando mencionar créditos totais."
        ),
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

    @field_validator("instituto_nomes", mode="before")
    @classmethod
    def normalizar_instituto_nomes(cls, valor: Any) -> Any:
        if valor is None:
            return None

        if isinstance(valor, str):
            valor = [valor]

        if isinstance(valor, (list, tuple)):
            valores = [v.strip() if isinstance(v, str) else v for v in valor]
            valores = [v for v in valores if v != ""]
            return valores or None

        return valor

    @field_validator("instituto_abrevs", mode="before")
    @classmethod
    def normalizar_instituto_abrevs(cls, valor: Any) -> Any:
        if valor is None:
            return None

        if isinstance(valor, str):
            valor = [valor]

        if isinstance(valor, (list, tuple)):
            valores = [v.strip().upper().removesuffix("-USP") if isinstance(v, str) else v for v in valor]
            valores = [v for v in valores if v != ""]
            return valores or None

        return valor

    @field_validator("instituto_campi", mode="before")
    @classmethod
    def normalizar_instituto_campi(cls, valor: Any) -> Any:
        if valor is None:
            return None

        if isinstance(valor, str):
            valor = [valor]

        if isinstance(valor, (list, tuple)):
            valores = [v.strip() if isinstance(v, str) else v for v in valor]
            valores = [v for v in valores if v != ""]
            return valores or None

        return valor

    @staticmethod
    def _adicionar_filtro_lista(
        condicoes: list[dict],
        chave: str,
        valores: list | None,
    ) -> None:
        """Adiciona uma condição de igualdade ou pertencimento à lista."""

        if not valores:
            return

        valores = [v.value if isinstance(v, Enum) else v for v in valores]

        if len(valores) == 1:
            condicoes.append({chave: valores[0]})
        else:
            condicoes.append({chave: {"$in": valores}})

    def montar_where(self) -> dict | None:
        """
        Constrói o filtro where do ChromaDB equivalente aos filtros informados.

        As alternativas de um mesmo atributo são combinadas por disjunção
        (OR): basta corresponder a um dos valores informados.

        Os filtros de atributos diferentes são combinados por conjunção
        (AND): todas as condições devem ser satisfeitas.
        """

        condicoes = []

        self._adicionar_filtro_lista(condicoes, MetaKey.INSTITUTO_NOME, self.instituto_nomes)
        self._adicionar_filtro_lista(condicoes, MetaKey.INSTITUTO_ABREV, self.instituto_abrevs)
        self._adicionar_filtro_lista(condicoes, MetaKey.INSTITUTO_CAMPUS, self.instituto_campi)

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
        str,
        Field(
            description=(
                "Palavras-chave e expressões curtas que representem os temas, "
                "conceitos ou áreas de interesse do usuário. Combine vários "
                "termos relacionados em uma única string, preferencialmente "
                "separados por vírgulas (ex.: 'evolução darwiniana, seleção "
                "natural, origem das espécies'). Não inclua a solicitação "
                "completa em linguagem natural, siglas de disciplinas ou "
                "critérios determinísticos. Se a busca depender exclusivamente "
                "de filtros, deixe este campo vazio."
            )
        ),
    ] = "",
    filtros: Annotated[
        FiltroDisciplinas | None,
        Field(
            description=(
                "Restrições determinísticas para limitar os resultados. "
                "Informe somente os critérios estabelecidos pelo usuário "
                "ou inferidos com segurança do contexto. Todas as condições "
                "preenchidas devem ser satisfeitas simultaneamente, exceto "
                "quando houver várias abreviações de institutos: nesse caso, "
                "basta a disciplina pertencer a um dos institutos informados."
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
                f"(entre 1 e {BUSCA_MAX_RESULTADOS}). Utilize o valor padrão "
                f"({BUSCA_DEFAULT_RESULTADOS}) na maioria das buscas. Aumente "
                "esse valor somente quando a busca for particularmente ampla "
                "ou quando houver uma justificativa para explorar mais candidatos. "
                "Não ajuste esse parâmetro simplesmente para corresponder à "
                "quantidade de disciplinas que o usuário deseja receber: a "
                "quantidade recuperada pode ser maior que a quantidade apresentada."
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
    Combine diferentes termos quando necessário, preferencialmente separados
    por vírgulas. A busca semântica compara essas expressões com os nomes e
    o conteúdo das disciplinas, incluindo ementas, objetivos e conteúdo
    programático. Não utilize siglas isoladas como consulta semântica.

    Quando o usuário estabelecer critérios determinísticos, como instituto,
    campus, créditos ou carga horária, aplique-os por meio dos filtros.
    Todas as condições informadas devem ser satisfeitas simultaneamente,
    exceto quando houver alternativas para um mesmo critério. Por exemplo,
    se o usuário aceitar disciplinas do IME ou da Poli, basta que a disciplina
    pertença a um desses institutos.

    Se o usuário solicitar disciplinas apenas por critérios determinísticos,
    sem especificar um assunto de interesse, realize a busca utilizando
    exclusivamente os filtros, sem necessidade de consulta semântica.
    Nesse caso, deixe o campo query vazio e forneça pelo menos um filtro.

    Utilize somente critérios explicitamente estabelecidos pelo usuário ou
    que possam ser inferidos com segurança do contexto da conversa. Ao
    refinar uma busca anterior, preserve os interesses e filtros que
    continuem pertinentes.

    A quantidade de resultados retornados pela ferramenta representa o
    conjunto de disciplinas candidatas à seleção, não necessariamente a
    quantidade que deve ser apresentada ao usuário. Analise os resultados
    e selecione aqueles mais relevantes para a solicitação, respeitando
    a quantidade solicitada pelo usuário quando houver uma.

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

    if query.strip().lower() in {"", "null", "none"}:
        query = None
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


@lru_cache
def obter_agent() -> CompiledStateGraph:
    """Retorna novo agente do Hermes (única instância, criada na primeira
    chamada)."""

    model = ChatOpenRouter(
        model=settings.agent_model,
        api_key=settings.openrouter_api_key.get_secret_value(),
    )

    agent = create_agent(
        model=model,
        tools=[consultar_disciplinas, buscar_disciplinas],
        system_prompt=settings.system_prompt_path.read_text(encoding="utf-8"),
        checkpointer=InMemorySaver(),
    )

    logger.info("Agente criado com modelo '%s'", settings.agent_model)
    return agent


def obter_resposta(mensagem: str, conversa_id: str) -> str:
    """Envia mensagem para agente na conversa especificada, e retorna a sua
    resposta em texto."""

    agent = obter_agent()
    config: RunnableConfig = {"configurable": {"thread_id": conversa_id}}

    logger.info("obter_resposta: iniciando (conversa_id=%s)", conversa_id)

    try:
        resultado = agent.invoke(
            {"messages": [{"role": "user", "content": mensagem}]},
            config=config,
        )
    except Exception:
        logger.exception("obter_resposta: erro durante a execução (conversa_id=%s)", conversa_id)
        raise

    return resultado["messages"][-1].content
