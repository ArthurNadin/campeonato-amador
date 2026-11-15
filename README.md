# Campeonato Amador

Projeto final do curso de Desenvolvimento Web. Aplicação em Django para
organizar campeonatos amadores: cadastro de times e jogadores, agenda de partidas,
lançamento de placares e tabela de classificação calculada automaticamente.

## O que o projeto atende

| Requisito do projeto final | Onde está |
| --- | --- |
| Login de usuário | Cadastro, entrar e sair em `contas/`; todas as telas exigem login |
| Dados persistentes | Tabelas `Campeonato`, `Time`, `Jogador` e `Partida` em `campeonatos/models.py`, gravadas em SQLite |
| Formulários | Cadastro, login, campeonato, time, jogador e partida, todos com validação (`forms.py`) |
| Versionamento no GitHub | Uma branch por funcionalidade, integrada à `main` por Pull Request |

Cada usuário só vê e altera os próprios campeonatos.

## Modelo de dados

```
Usuário 1 ── N Campeonato 1 ── N Time 1 ── N Jogador
                          1 ── N Partida N ── 1 Time (mandante)
                                         N ── 1 Time (visitante)
```

- **Campeonato**: nome (único por usuário), modalidade, data de início.
- **Time**: nome (único dentro do campeonato), responsável, telefone.
- **Jogador**: nome (único dentro do time), número da camisa de 1 a 99 (sem
  repetir no time) e posição; número e posição são opcionais.
- **Partida**: mandante, visitante, data, local e placar. O placar fica vazio
  enquanto a partida não foi realizada.

Regras garantidas no banco: um time não joga contra ele mesmo, e o placar
tem os gols dos dois times ou de nenhum.

## Classificação

Pontos corridos: vitória vale 3 pontos e empate vale 1. O desempate segue a
ordem pontos, vitórias, saldo de gols, gols pró e nome do time. Só as
partidas com placar lançado entram na conta.

## Como rodar

No Git Bash:

```bash
python -m venv venv
source venv/Scripts/activate      # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # depois edite a SECRET_KEY
python manage.py migrate
python manage.py runserver
```

Abra http://127.0.0.1:8000 e crie uma conta em "Cadastre-se".

## Testes

```bash
python manage.py test
```

## Estrutura

```
config/        configurações e rotas principais
contas/        cadastro de usuário, login e logout
campeonatos/   modelos, formulários, telas e testes
templates/     páginas HTML
static/        CSS
```
