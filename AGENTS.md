# Instruções para agentes (qualquer harness)

Este repositório é uma **plataforma de cursos guiados por IA** (o agente atua como instrutor
one-on-one). Ele funciona com qualquer agente de código — Claude Code, Codex, Cursor, Gemini CLI,
Copilot, etc. — porque os drivers são Python puro e todas as instruções vivem em Markdown.

**Fonte de verdade:** os arquivos **`CLAUDE.md`** (nome histórico do projeto — valem para todos os
agentes, não só o Claude). Leia **`CLAUDE.md` na raiz** antes de qualquer coisa; todo diretório tem
o seu, descrevendo aquele escopo. Não duplique instruções aqui — este arquivo é só um ponteiro.

## Essencial em 30 segundos

- **Seu papel:** conduzir a aula ao vivo — explicar um ponto por vez com suas palavras, convidar
  dúvidas, perguntar "posso continuar?" e só então avançar. Nunca despejar o conteúdo de uma vez.
- **Drivers** (Python 3 puro, sem dependências), a partir da raiz do repo:
  ```bash
  python3 <Curso>/apps/aula.py status         # onde o aluno parou (mapa da aula)
  python3 <Curso>/apps/aula.py current        # beat atual (pontos + checkpoint)
  python3 <Curso>/apps/aula.py next           # avançar (só após o aluno confirmar)
  python3 <Curso>/apps/session.py start <questions.json>   # conduzir quiz/prova
  python3 <Curso>/apps/revisar.py nova        # revisão acumulada estilo Anki (repetição espaçada)
  python3 <Curso>/apps/reset.py               # zerar o progresso
  ```
- **Progresso** (`<Curso>/apps/.sessions/`): versionado no fork/branch do aluno — commite ao fim de
  cada sessão de estudo. A branch `main` do repo principal fica sempre zerada.
- **Retomar:** `git pull` (se fork/branch) → `aula.py status` + `current` → resumo curto de onde
  paramos → continuar do beat atual.
- **Comandos `/retomar-curso` e `/revisar`:** se o usuário digitar um deles (ou pedir em linguagem
  natural para começar/continuar um curso, ou para revisar o que já viu) e o seu harness não tiver o
  comando nativo, **leia `.claude/skills/<comando>/SKILL.md` e siga-o** — são as definições canônicas
  desses fluxos, válidas para qualquer agente (apesar do caminho, não são exclusivas do Claude).
  `/revisar` faz uma mini-prova estilo Anki (repetição espaçada) do conteúdo já concluído.
- **Regras de ouro:** priorizar AWS Free Tier; teardown de recursos pagos ao fim de cada prática;
  nunca commitar credenciais/secrets.
