import chromadb
from jupiterweb import Disciplina


def formatar_disciplinas(disciplinas_desformatadas: dict) -> str:
    """Formata o resultado da busca semântica no banco de dados vetorial para uma string"""

    disciplinas_formatadas = [disciplinas for disciplinas in disciplinas_desformatadas["documents"][0]]

    resposta = ""

    for disciplina_requisitada in disciplinas_formatadas:
        resposta += disciplina_requisitada + "\n"

    return resposta


def buscar_disciplinas(collection: chromadb.Collection, palavra_chave: str, limite: int = 5) -> list[Disciplina]:
    """
    Dado uma palavra-chave, faz uma busca semântica no banco de dados vetorial
    e traz as x (onde x = limite) disciplinas mais próximas da palavra-chave.
    """

    return collection.query(query_texts=[palavra_chave], n_results=limite)
