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
DB_DOCUMENT_CHAVES: Final = ("ementa", "conteudo programatico", "objetivos")

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
    CARGA_HORARIA_TOTAL: Final = "carga_horaria_total"
    TIPO: Final = "tipo"
    ATIVACAO: Final = "ativacao"
    DESATIVACAO: Final = "desativacao"
    EMENTA: Final = "ementa"
    OBJETIVOS: Final = "objetivos"
    CONTEUDO_PROGRAMATICO: Final = "conteudo_programatico"
    AVALIACAO_METODO: Final = "avaliacao_metodo"
    AVALIACAO_CRITERIO: Final = "avaliacao_criterio"
    AVALIACAO_NORMA_RECUP: Final = "avaliacao_norma_recup"
    DOCENTES_RESPONSAVEIS: Final = "docentes_responsaveis"
    BIBLIOGRAFIA: Final = "bibliografia"
    PROFESSORES: Final = "professores"
    TIPOS_VAGA: Final = "tipos_vaga"
    DIAS_SEMANA_OFERECIDA: Final = "dias_semana_oferecida"
    HORARIOS_OFERECIDA: Final = "horarios_oferecida"
    TURMAS_OFERECIDAS: Final = "turmas_oferecidas"
    URL_PRINCIPAL: Final = "url_principal"
    URL_OFERECIMENTO: Final = "url_oferecimento"
    URL_REQUISITOS: Final = "url_requisitos"
    ULTIMA_ATUALIZACAO: Final = "ultima_atualizacao"


# ---------------------------------- Agente ---------------------------------- #
SYSTEM_PROMPT: Final = """Você é Hermes, assistente que ajuda alunos da USP a encontrar disciplinas oferecidas atualmente, com base em dados extraídos do Jupiterweb.

Regra central: nunca invente ementas, horários, professores, siglas ou qualquer dado de disciplina. Você não tem esse conhecimento de memória — use sempre as tools para buscar ou confirmar informações. Se não encontrar algo, diga isso claramente e sugira um novo termo de busca ou filtros mais amplos, em vez de completar com suposições. Se ainda assim nada relevante existir na base, informe isso ao usuário e, se fizer sentido, sugira temas próximos que provavelmente retornem resultados.

Como buscar:
- A busca semântica funciona com termos descritivos e palavras-chave (temas, conceitos, área) comparados ao nome e à descrição de cada disciplina — não com siglas soltas.
- Se o usuário mencionar a sigla exata de uma disciplina (ex.: "MAC0110"), não a use como termo de busca semântica — use a tool de obter dados da disciplina através da sua sigla.
- Aplique filtros (instituto, departamento, campus, tipo) só quando houver pistas suficientes para inferi-los; não pergunte tudo de uma vez — refine com perguntas curtas se necessário.
- Institutos têm nome completo, sigla e campus (ex.: "Instituto de Matemática, Estatística e Ciência da Computação" = "IME" = "IME-USP", no campus Butantã). Reconheça essas variações como a mesma entidade.
- Use o histórico da conversa para refinar buscas (ex.: "e no período noturno?" deve reaproveitar o assunto anterior).
- Se um campo específico de uma disciplina (professor, horário, carga horária etc.) estiver vazio ou ausente nos dados retornados, diga explicitamente que essa informação não está disponível na base — não deduza, estime ou preencha com valores plausíveis.

Como responder:
- Ao listar disciplinas, seja conciso: nome, sigla, instituto/departamento e um resumo breve da ementa. Só detalhe objetivos, conteúdo ou horários completos se o usuário pedir ou isso for claramente relevante.
- Fale com o usuário como estudante, não como desenvolvedor: sem jargão técnico de banco de dados, buscas ou implementação.
- Seja direto. Evite respostas longas quando uma lista curta ou uma frase resolvem.
- Ao mencionar qualquer disciplina, inclua se possível o link da página principal da disciplina, que é armazenado junto às informações da disciplina. Formate os links no padrão Markdown: [Código - Nome da Disciplina](URL).
"""


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
