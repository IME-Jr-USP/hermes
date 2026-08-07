import jupiterweb

institutos_usp = jupiterweb.obter_institutos()
instituto = institutos_usp[37] # por enquanto estamos pegando apenas as disciplinas do IME (cod 37)

disciplinas_instituto = instituto.obter_disciplinas() # essa linha está obtendo as disciplinas toda vez que inicializa, colocar em outro arquivo


import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

#client = chromadb.Client() # para caso não queira salvar o banco de dados no seu pc

banco_disciplinas = client.get_or_create_collection(name="banco-de-disciplinas")

bancos_dados = [banco.name for banco in client.list_collections()] # pega todos os bancos de dados do seu pc e coloca o nome de cada na lista bancos_dados

if not "banco-de-disciplinas" in bancos_dados: # testa se tem o banco de dados no seu pc, se não tiver cria um.
    for disciplina in disciplinas_instituto:
        dados = disciplina.obter_dados()
        banco_disciplinas.add(
            documents=[
                dados["nome"]
            ],
            ids=[disciplina.sigla] # ids para identificar cada disciplinas.
        )
# exemplo de uma das formas de adicionar disciplinas no banco de dados vetoriais do chroma.


def formatar_disciplinas(disciplinas_desformatadas: dict):
    disciplinas_formatadas = [disciplinas for disciplinas in disciplinas_desformatadas['documents'][0]]

    resposta = ""
    
    for disciplina_requisitada in disciplinas_formatadas:
        resposta += disciplina_requisitada + "\n"

    return resposta
# função de formatação que retorna apenas o texto da disciplina, apagando todas as outras informações que o query retorna.


def buscar_disciplinas(palavra_chave: str, limite: int = 5):
    """
    Dado uma palavra-chave, faz uma busca semântica no banco de dados vetorial
    e traz as x (onde x = limite) disciplinas mais próximas da palavra-chave.
    """

    disciplinas_proximas = banco_disciplinas.query(
        query_texts=[palavra_chave],
        n_results=limite
    )
    # faz o query no banco de dados que fornecemos para encontrar, por busca semântica, a disciplina que mais se assemelha ao que o usuário quer. (dps vamos mudar o modelo de busca, por enquanto está o padrão do chroma)

    return formatar_disciplinas(disciplinas_proximas)