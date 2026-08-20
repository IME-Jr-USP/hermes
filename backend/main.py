import chromadb
# biblioteca para criaçao o agente novas
from langchain.agents import create_agent
from langchain.tools import tool 

from buscar_disciplinas import buscar_disciplinas
from db import (
    atualizar_banco_disciplinas,
    obter_banco_disciplinas,
    obter_disciplinas_jupiterweb,
)
def criar_tool_buscar_disciplinas(collection: chromadb.Collection):
    @tool
    def consultar_disciplinas(pergunta: str, limite: int = 3) -> dict:
        
        """busca disciplinas relacionadas a um tema ou interesse"""
        return buscar_disciplinas(collection, pergunta, limite=limite)

    return consultar_disciplinas

def criar_agente_hermes(collection: chromadb.Collection, model):
    ferramenta_busca = criar_tool_buscar_disciplinas(collection)

    return create_agent(
        model=model,
        tools=[ferramenta_busca],
        system_prompt=(
            "Hermes, um assistente para ajudar usuários a encontrar "
            "disciplinas, use a ferramenta consultar_disciplinas quando "
            "precisar pesquisar disciplinas no banco de dados"
        ),
    )


def hermes(collection: chromadb.Collection, pergunta: str) -> str:
    # Grupo 2 vai preparar o agente aqui, com todos tools necessários.
    # O único tool necessário agora é o buscar_disciplinas, para que o agente
    # possa buscar disciplinas.
    # Importante: instalem o langchain usando uv add langchain

    return buscar_disciplinas(collection, pergunta, limite=3)
    # aqui tem um exemplo já funcional da função de retornar a disciplina mais próxima no banco vetorial


if __name__ == "__main__":
    collection = obter_banco_disciplinas()
    atualizar_banco_disciplinas(collection, obter_disciplinas_jupiterweb(apenas_oferecidas=True))

    while True:
        pergunta = input("Faça uma pergunta para o Hermes: ")
        resposta = hermes(collection, pergunta)

        print(resposta)
