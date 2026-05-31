# Hermes

Este repositorio contem o projeto Hermes.

Ele esta dividido em duas partes principais:

- `backend`: codigo do backend do Hermes.
- `frontend`: codigo do frontend do Hermes.

Cada parte pode ter instrucoes especificas no seu proprio `README.md`. Este
arquivo explica o fluxo basico para baixar o repositorio e trabalhar com Git no
dia a dia.

## 1. Instalar o Git

Antes de clonar o repositorio, confira se o Git esta instalado:

```bash
git --version
```

Se aparecer uma versao, por exemplo `git version 2.x.x`, o Git ja esta
instalado.

Se o comando nao funcionar, instale o Git pelo site oficial:

https://git-scm.com/downloads

## 2. Clonar o repositorio

Para baixar o projeto no seu computador, execute:

```bash
git clone https://github.com/IME-Jr-USP/hermes.git
```

Depois entre na pasta do projeto:

```bash
cd hermes
```

## 3. Conferir a branch atual

Para ver em qual branch voce esta:

```bash
git branch
```

A branch atual aparece com um `*` antes do nome.

Voce tambem pode usar:

```bash
git branch --show-current
```

Normalmente, a branch principal do projeto e a `main`.

## 4. Atualizar o projeto antes de trabalhar

Antes de criar uma branch nova ou comecar uma alteracao, atualize sua copia
local:

```bash
git checkout main
git pull origin main
```

O `git pull` baixa as alteracoes mais recentes do GitHub para o seu computador.

## 5. Criar uma branch nova

Cada tarefa deve ser feita em uma branch propria. Isso evita misturar alteracoes
diferentes na mesma branch.

Para criar e entrar em uma branch nova:

```bash
git checkout -b nome-da-sua-branch
```

Exemplos de nomes:

```bash
git checkout -b adicionar-readme
git checkout -b corrigir-busca-disciplinas
git checkout -b criar-tela-login
```

Use nomes curtos, claros e relacionados ao que voce esta fazendo.

## 6. Ver arquivos alterados

Depois de editar arquivos, veja o que mudou:

```bash
git status
```

Esse comando mostra:

- arquivos modificados;
- arquivos novos;
- arquivos removidos;
- arquivos que ainda nao foram adicionados ao commit.

## 7. Ver o conteudo das alteracoes

Para ver exatamente o que mudou nos arquivos:

```bash
git diff
```

Esse comando ajuda a revisar suas proprias alteracoes antes de criar um commit.

## 8. Adicionar arquivos ao commit

Para adicionar todos os arquivos alterados:

```bash
git add .
```

Se quiser adicionar apenas um arquivo especifico:

```bash
git add caminho/do/arquivo
```

Exemplo:

```bash
git add README.md
```

## 9. Criar um commit

Depois de adicionar os arquivos, crie um commit com uma mensagem clara:

```bash
git commit -m "Adiciona instrucoes de Git no README"
```

A mensagem deve explicar o que mudou. Prefira mensagens curtas e objetivas.

Bons exemplos:

```bash
git commit -m "Cria README inicial do projeto"
git commit -m "Corrige busca de disciplinas"
git commit -m "Adiciona tela de login"
```

Evite mensagens genericas como:

```bash
git commit -m "mudancas"
git commit -m "ajustes"
git commit -m "teste"
```

## 10. Enviar a branch para o GitHub

Na primeira vez que voce enviar uma branch nova:

```bash
git push -u origin nome-da-sua-branch
```

Exemplo:

```bash
git push -u origin adicionar-readme
```

Depois disso, enquanto estiver na mesma branch, voce pode usar apenas:

```bash
git push
```

## 11. Abrir um Pull Request

Depois de enviar a branch para o GitHub, abra um Pull Request.

No Pull Request, explique de forma simples:

- o que foi alterado;
- por que a alteracao foi feita;
- como testar, quando fizer sentido.

Antes de pedir revisao, confira se o codigo roda e se os arquivos alterados sao
apenas os que fazem parte da tarefa.

## 12. Atualizar sua branch com a main

Se a `main` recebeu alteracoes enquanto voce trabalhava, atualize sua branch:

```bash
git checkout main
git pull origin main
git checkout nome-da-sua-branch
git merge main
```

Se aparecer conflito, o Git vai indicar quais arquivos precisam ser resolvidos.
Depois de resolver os conflitos:

```bash
git add .
git commit -m "Resolve conflitos com main"
```

Em seguida, envie a branch atualizada:

```bash
git push
```

## 13. Fluxo recomendado no dia a dia

Quando for comecar uma tarefa nova:

```bash
git checkout main
git pull origin main
git checkout -b nome-da-sua-branch
```

Durante o trabalho:

```bash
git status
git diff
git add .
git commit -m "Mensagem clara do commit"
```

Quando terminar:

```bash
git push -u origin nome-da-sua-branch
```

Depois disso, abra um Pull Request no GitHub.

## 14. Problemas comuns

### Fiz alteracoes na branch errada

Confira primeiro o estado atual:

```bash
git status
```

Se voce ainda nao fez commit, crie a branch correta a partir do ponto atual:

```bash
git checkout -b nome-da-branch-correta
```

As alteracoes vao junto para a branch nova.

### O Git pediu usuario e email

Configure seu nome:

```bash
git config --global user.name "Seu Nome"
```

Configure seu email:

```bash
git config --global user.email "seu-email@example.com"
```

Use o mesmo email associado a sua conta do GitHub.

### O push falhou porque a branch nao existe no GitHub

Use o comando com `-u`:

```bash
git push -u origin nome-da-sua-branch
```

Isso cria a branch no GitHub e conecta sua branch local com a branch remota.

### A branch local esta desatualizada

Atualize a `main` e depois traga as alteracoes para sua branch:

```bash
git checkout main
git pull origin main
git checkout nome-da-sua-branch
git merge main
```

Se houver conflitos, resolva os arquivos indicados pelo Git antes de continuar.
Depois disso:

```bash
git add .
git commit -m "Resolve conflitos com main"
git push
```
