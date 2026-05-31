from buscar_disciplinas import buscar_disciplinas


def hermes(pergunta):
    # Grupo 2 vai preparar o agente aqui, com todos tools necessários.
    # O único tool necessário agora é o buscar_disciplinas, para que o agente
    # possa buscar disciplinas.
    # Importante: instalem o langchain usando uv add langchain

    resposta = "..."
    return resposta


if __name__ == "__main__":
    while True:
        pergunta = input("Faça uma pergunta para o Hermes: ")
        resposta = hermes(pergunta)
