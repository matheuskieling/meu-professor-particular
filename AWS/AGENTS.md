# Instruções para agentes — curso de AWS

Fonte de verdade deste diretório: **`AWS/CLAUDE.md`** (plano do curso, anatomia dos módulos, como
conduzir a aula ao vivo) e **`AWS/README.md`** (como o aluno faz o curso). Leia-os antes de agir.
Vale para qualquer harness — os `CLAUDE.md` são a convenção do repo, não exclusividade do Claude.

Atalhos:
- Conduzir/retomar a aula: `python3 engine/aula.py status` + `current` (guia em `engine/CLAUDE.md`).
- Quiz/prova/simulado: `python3 engine/session.py start <questions.json>` (provas com `--id prova`,
  certificações com `--id cert`).
- Portões de prontidão para certificações: `AWS/certificacoes/CLAUDE.md`.
- Progresso do aluno: `AWS/.sessions/` — commitado no fork/branch dele; `main` fica zerada.
