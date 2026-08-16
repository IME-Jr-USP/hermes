import chromadb

from buscar_disciplinas import buscar_disciplinas
from db import (
    atualizar_banco_disciplinas,
    obter_banco_disciplinas,
    obter_disciplinas_jupiterweb,
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
