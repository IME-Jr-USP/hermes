def formatar_disciplinas(disciplinas_desformatadas: dict) -> str:
    """Formata o resultado da busca semântica no banco de dados vetorial para uma string"""

    disciplinas_formatadas = [disciplinas for disciplinas in disciplinas_desformatadas["documents"][0]]

    resposta = ""

    for disciplina_requisitada in disciplinas_formatadas:
        resposta += disciplina_requisitada + "\n"

    return resposta
