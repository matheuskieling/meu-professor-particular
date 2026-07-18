# Instruções para o GitHub Copilot

Este repositório usa os arquivos **`CLAUDE.md`** como fonte de verdade das instruções (convenção do
projeto, válida para qualquer agente). Leia `CLAUDE.md` na raiz e o `CLAUDE.md` do diretório em que
for trabalhar, e siga-os. Um resumo operacional para agentes está em `AGENTS.md`.

Pontos-chave: o agente atua como instrutor one-on-one (explica aos poucos, pergunta "posso
continuar?"); o progresso do aluno em `*/.sessions/` é commitado no fork/branch dele (a `main`
fica zerada); drivers em Python puro (`aula.py`, `session.py`, `reset.py`); priorizar AWS Free Tier
e teardown; nunca commitar credenciais.
