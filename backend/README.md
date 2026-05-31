# Hermes Backend

Este projeto é o backend do Hermes. Ele está em Python e usa o `uv` para cuidar
do ambiente virtual, da versão do Python e das dependencias.

Se voce está começando, pense no `uv` como uma ferramenta que substitui boa
parte do trabalho manual de criar `venv`, instalar pacotes com `pip` e manter um
arquivo de lock atualizado.

Documentacao oficial do `uv`: https://docs.astral.sh/uv/

## O que existe neste projeto

- `main.py`: arquivo principal do projeto. É o ponto de entrada para executar o
  Hermes.
- `buscar_disciplinas.py`: arquivo onde fica a função que busca disciplinas.
- `pyproject.toml`: arquivo que declara o nome do projeto, a versão do Python e
  as dependencias.
- `uv.lock`: arquivo gerado pelo `uv` com as versões exatas das dependencias.
- `.python-version`: arquivo que indica a versão de Python esperada pelo projeto.

Hoje o projeto usa Python `3.12` e já tem `chromadb` como dependencia.

## 1. Instalar o uv

O primeiro passo e instalar o `uv` no seu computador.

### Linux ou macOS

No terminal, execute:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Depois feche e abra o terminal novamente. Em seguida, confira se instalou:

```bash
uv --version
```

Se aparecer uma versão, por exemplo `uv 0.x.x`, a instalação funcionou.

### Windows

No PowerShell, execute:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Depois feche e abra o PowerShell novamente. Em seguida, confira:

```powershell
uv --version
```

## 2. Entrar na pasta do projeto

Abra o terminal na pasta do backend:

```bash
cd /caminho/para/hermes/backend
```

Se voce clonou o repositorio inteiro, normalmente o caminho sera algo parecido
com:

```bash
cd hermes/backend
```

## 3. Instalar a versao correta do Python

Este projeto espera Python `3.12`.

Com o `uv`, voce pode instalar essa versao assim:

```bash
uv python install 3.12
```

Esse comando baixa o Python 3.12 caso ele ainda nao exista no seu computador.

## 4. Sincronizar o projeto

Depois de instalar o `uv` e o Python, sincronize o ambiente:

```bash
uv sync
```

Esse comando faz algumas coisas importantes:

- cria a pasta `.venv`, que e o ambiente virtual do projeto;
- instala as dependencias listadas no `pyproject.toml`;
- usa o `uv.lock` para instalar as mesmas versoes em todos os computadores.

Na pratica, sempre que voce baixar o projeto pela primeira vez ou quando alguem
adicionar uma dependencia nova, rode:

```bash
uv sync
```

## 5. Executar o arquivo principal

O arquivo principal e o `main.py`.

Para executar:

```bash
uv run python main.py
```

O comando `uv run` executa o Python dentro do ambiente do projeto. Isso evita o
problema comum de instalar uma dependencia em um Python e executar o projeto com
outro Python.

Ao rodar o comando, o programa vai pedir uma pergunta:

```text
Faça uma pergunta para o Hermes:
```

Digite uma pergunta e pressione `Enter`.

Por enquanto, o agente ainda esta em construcao. A funcao `hermes()` retorna
`"..."`, e o arquivo `main.py` ainda nao imprime essa resposta na tela. Mesmo
assim, esse e o comando correto para iniciar o programa.

Para parar a execucao, pressione:

```text
Ctrl + C
```

## 6. Executar comandos rapidos em Python

Voce tambem pode testar uma funcao diretamente pelo terminal.

Exemplo:

```bash
uv run python -c "from main import hermes; print(hermes('quais disciplinas falam de IA?'))"
```

Esse comando importa a funcao `hermes`, chama a funcao com uma pergunta e imprime
o retorno.

## 7. Adicionar uma dependencia

Quando precisar instalar uma biblioteca nova, use `uv add`.

Exemplo com `langchain`:

```bash
uv add langchain
```

Isso atualiza automaticamente:

- `pyproject.toml`, adicionando a dependencia;
- `uv.lock`, registrando a versao exata instalada.

Depois disso, outras pessoas do projeto so precisam rodar:

```bash
uv sync
```

para receber a mesma dependencia.

## 8. Adicionar uma dependencia de desenvolvimento

Dependencias de desenvolvimento sao ferramentas usadas para programar, testar ou
formatar o codigo, mas que normalmente nao fazem parte da aplicacao final.

Exemplo:

```bash
uv add --dev pytest
```

Use esse tipo de dependencia para ferramentas como testes, formatadores e linters.

## 9. Remover uma dependencia

Para remover uma biblioteca:

```bash
uv remove nome-da-dependencia
```

Exemplo:

```bash
uv remove langchain
```

Assim como no `uv add`, o `uv` tambem atualiza o `pyproject.toml` e o `uv.lock`.

## 10. Ver as dependencias instaladas

Para ver a arvore de dependencias:

```bash
uv tree
```

Isso ajuda a entender quais pacotes foram instalados diretamente e quais vieram
como dependencia de outros pacotes.

## 11. Ativar o ambiente virtual manualmente

Na maioria dos casos, voce nao precisa ativar o ambiente virtual. Usar `uv run`
ja e suficiente:

```bash
uv run python main.py
```

Mas, se quiser ativar o ambiente manualmente:

### Linux ou macOS

```bash
source .venv/bin/activate
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

Depois de ativar, o terminal passa a usar o Python da pasta `.venv`.

Para sair do ambiente virtual:

```bash
deactivate
```

## 12. Fluxo recomendado no dia a dia

Quando abrir o projeto para trabalhar:

```bash
cd hermes/backend
uv sync
uv run python main.py
```

Quando precisar adicionar uma biblioteca:

```bash
uv add nome-da-biblioteca
```

Quando outra pessoa adicionar ou atualizar dependencias:

```bash
uv sync
```

## 13. Problemas comuns

### O comando `uv` nao foi encontrado

Feche e abra o terminal novamente. Se ainda nao funcionar, reinstale o `uv` e
confira com:

```bash
uv --version
```

### A dependencia foi instalada, mas o Python nao encontra

Confira se voce esta executando com `uv run`:

```bash
uv run python main.py
```

Evite rodar apenas:

```bash
python main.py
```

porque esse comando pode usar o Python global do seu computador, fora do ambiente
do projeto.

### O ambiente parece desatualizado

Rode novamente:

```bash
uv sync
```

Esse e o comando que deixa o ambiente local igual ao que esta definido no
projeto.
