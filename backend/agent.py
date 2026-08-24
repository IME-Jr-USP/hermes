import json
from pprint import pprint
from typing import Annotated

from constants import AGENT_MODEL, SYSTEM_PROMPT
from db import obter_banco_disciplinas
from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_core.utils.uuid import uuid7
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field
from utils import CampusDisciplina, get_logger, truncar_texto

logger = get_logger(__name__)


class FiltroDisciplinas(BaseModel):
    """Filtros opcionais para restringir a busca de disciplinas.

    Em todos os campos, um valor None (ou omitido) significa que aquele filtro
    não é aplicado — não use 0 ou string vazia para indicar "sem filtro".
    """

    instituto_nome: str | None = Field(
        default=None,
        description="Nome completo do instituto responsável pela disciplina " "(ex.: 'Faculdade de Medicina Veterinária e Zootecnia').",
    )
    instituto_abrev: str | None = Field(
        default=None,
        description="Abreviação do instituto, em maiúsculas e sem o sufixo '-USP' " "(ex.: 'IME', 'POLI', 'ESALQ').",
    )
    instituto_campus: CampusDisciplina | None = Field(
        default=None,
        description="Campus da USP onde a disciplina é oferecida (ex.: 'Butantã')",
    )

    creditos_aula_min: int | None = Field(
        default=None,
        description="Número mínimo de créditos-aula da disciplina (inclusive). Se for None, não há restrição mínima.",
    )
    creditos_aula_max: int | None = Field(
        default=None,
        description="Número máximo de créditos-aula da disciplina (inclusive). Se for None, não há restrição máxima.",
    )

    creditos_trabalho_min: int | None = Field(
        default=None,
        description="Número mínimo de créditos-trabalho da disciplina (inclusive). Se for None, não há restrição mínima.",
    )
    creditos_trabalho_max: int | None = Field(
        default=None,
        description="Número máximo de créditos-trabalho da disciplina (inclusive). Se for None, não há restrição máxima.",
    )

    carga_horaria_total_min: int | None = Field(
        default=None,
        description="Carga horária total mínima da disciplina, em horas (inclusive). Se for None, não há restrição mínima.",
    )
    carga_horaria_total_max: int | None = Field(
        default=None,
        description="Carga horária total máxima da disciplina, em horas (inclusive). Se for None, não há restrição máxima.",
    )

    def montar_where(self) -> dict | None:
        """Constrói o filtro `where` do ChromaDB equivalente a estes filtros.

        Campos None são ignorados (sem restrição). Retorna None se nenhum
        filtro estiver preenchido.
        """

        condicoes = []

        if self.instituto_nome:
            condicoes.append({"instituto_nome": self.instituto_nome})
        if self.instituto_abrev:
            condicoes.append({"instituto_abrev": self.instituto_abrev})
        if self.instituto_campus:
            condicoes.append({"instituto_campus": self.instituto_campus.value})

        if self.creditos_aula_min is not None:
            condicoes.append({"creditos_aula": {"$gte": self.creditos_aula_min}})
        if self.creditos_aula_max is not None:
            condicoes.append({"creditos_aula": {"$lte": self.creditos_aula_max}})

        if self.creditos_trabalho_min is not None:
            condicoes.append({"creditos_trabalho": {"$gte": self.creditos_trabalho_min}})
        if self.creditos_trabalho_max is not None:
            condicoes.append({"creditos_trabalho": {"$lte": self.creditos_trabalho_max}})

        if self.carga_horaria_total_min is not None:
            condicoes.append({"carga_horaria_total": {"$gte": self.carga_horaria_total_min}})
        if self.carga_horaria_total_max is not None:
            condicoes.append({"carga_horaria_total": {"$lte": self.carga_horaria_total_max}})

        if not condicoes:
            return None
        if len(condicoes) == 1:
            return condicoes[0]
        return {"$and": condicoes}


@tool
def buscar_disciplinas(query: str, filtros: FiltroDisciplinas | None = None, n_resultados: Annotated[int, Field(ge=1, le=20)] = 10) -> str:
    """Busca disciplinas da USP por similaridade semântica com a query.

    Use esta tool sempre que o usuário pedir para encontrar, sugerir ou listar
    disciplinas com base em um tema, assunto ou interesse (ex.: "disciplinas sobre
    aprendizado de máquina", "matérias de introdução à economia"). A busca é feita sobre
    o conteúdo (ementa, objetivos, conteúdo programático) das disciplinas atualmente
    oferecidas na USP — não é uma busca por nome exato ou sigla.

    Os resultados vêm ordenados do mais para o menos relevante em relação à query.

    Args:
        query: Palavras-chave ou descrição do assunto de interesse, em linguagem
            natural (ex.: "algoritmos de otimização", "história da arte brasileira").
            Não é necessário usar sigla ou nome exato da disciplina.
        filtros: Filtros opcionais para restringir os resultados por instituto,
            departamento, campus, créditos ou carga horária. Omita campos que não forem
            mencionados pelo usuário — não infira valores que ele não especificou.
        n_resultados: Número máximo de disciplinas a retornar (entre 1 e 20).

    Returns:
        JSON com a lista de disciplinas encontradas (sigla, nome, instituto e ementa),
        ordenadas por relevância à query. Retorna uma lista vazia em JSON ("[]") se
        nenhuma disciplina corresponder à busca e aos filtros.
    """

    logger.info("buscar_disciplinas: '%s'", query)

    n_resultados = min(n_resultados, 20)
    collection = obter_banco_disciplinas()

    where = filtros.montar_where() if filtros else None
    logger.debug("buscar_disciplinas: filtro='%s'", where)

    res = collection.query(query_texts=[query], n_results=n_resultados, where=where)
    if not res["metadatas"] or not res["ids"][0]:
        logger.warning("buscar_disciplinas: nenhuma encontrada")
        return json.dumps([], ensure_ascii=False)

    saida = []
    for id_, metadata in zip(res["ids"][0], res["metadatas"][0]):
        item = {
            "sigla": id_,
            "nome": metadata.get("nome", ""),
            "instituto": metadata.get("instituto_abrev", ""),
            "ementa": truncar_texto(str(metadata.get("ementa", "")), 200),
        }
        saida.append(item)

    logger.debug("buscar_disciplinas: %s encontradas", len(saida))
    return json.dumps(saida, ensure_ascii=False, indent=2)


@tool
def obter_informacoes_disciplinas(siglas: list[str]) -> str:
    """Obtém todas as informações detalhadas de uma ou mais disciplinas pela sigla.

    Use esta tool quando o usuário já souber a(s) sigla(s) exata(s) da(s)
    disciplina(s) (ex.: "MAC0110", "PCS3616") ou quando quiser se aprofundar em
    disciplinas já encontradas anteriormente (por exemplo, através da tool
    `buscar_disciplinas`). Não use esta tool para buscar disciplinas por tema
    ou assunto — nesse caso, use `buscar_disciplinas`.

    Se o usuário pedir informações sobre várias disciplinas, passe todas as
    siglas de uma vez nesta única chamada, em vez de chamar a tool separadamente
    para cada uma.

    Retorna todas as informações disponíveis sobre cada disciplina: nome,
    instituto, campus, ementa, objetivos, conteúdo programático, créditos,
    carga horária, entre outros metadados. Use os campos que forem relevantes
    para responder à pergunta do usuário; não é necessário listar todos eles
    na resposta.

    Args:
        siglas: Lista com uma ou mais siglas exatas de disciplinas, no formato
            usado pela USP (ex.: ["MAC0110", "PCS3616"]). Não é case-sensitive.

    Returns:
        JSON com uma lista de objetos, um por disciplina encontrada, na mesma
        ordem das siglas informadas. Siglas não encontradas aparecem como um
        objeto com a chave "erro" no lugar dos dados, indicando qual sigla
        falhou — as demais disciplinas ainda são retornadas normalmente.
    """

    logger.info("obter_informacoes_disciplinas: %s disciplinas", len(siglas))

    siglas = [s.strip().upper() for s in siglas]
    logger.debug("obter_informacoes_disciplinas: %s", ",".join(siglas))

    collection = obter_banco_disciplinas()
    resultado = collection.get(ids=siglas, include=["metadatas", "documents"])

    if not resultado["metadatas"] or not resultado["documents"]:
        logger.warning("obter_informacoes_disciplinas: nenhuma disciplina foi encontrada")
        return json.dumps("[]", ensure_ascii=False)

    encontrados = dict(zip(resultado["ids"], resultado["metadatas"]))

    saida = []
    for sigla in siglas:
        if sigla not in encontrados:
            logger.warning("obter_informacoes_disciplinas: disciplina '%s' não foi encontrada", sigla)
            saida.append({"sigla": sigla, "erro": "Disciplina não encontrada."})
            continue
        saida.append(encontrados[sigla])

    return json.dumps(saida, ensure_ascii=False, indent=2)


def obter_agent() -> CompiledStateGraph:
    """Retorna novo agente do Hermes."""

    return create_agent(
        model=AGENT_MODEL,
        tools=[buscar_disciplinas, obter_informacoes_disciplinas],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )


def obter_resposta(agent: CompiledStateGraph, mensagem: str, conversa_id: str) -> list[dict]:
    """Envia mensagem para agente naconversa especificada, e retorna a sua resposta."""

    config: RunnableConfig = {"configurable": {"thread_id": conversa_id}}

    resultado = agent.invoke(
        {"messages": [{"role": "user", "content": mensagem}]},
        config=config,
    )
    return resultado["messages"][-1].content


if __name__ == "__main__":
    obter_banco_disciplinas()
    agent = obter_agent()
    conversa_id = str(uuid7())

    while True:
        mensagem = input(" >>> ")
        if mensagem.strip().lower() == "sair":
            break

        resposta = obter_resposta(agent, mensagem, conversa_id)
        print("\n".join([str(i["text"]) for i in resposta if i["type"] == "text"]))
        pprint(resposta)
