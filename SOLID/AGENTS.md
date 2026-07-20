# Instruções para agentes — curso de SOLID

Fonte de verdade deste diretório: **`SOLID/CLAUDE.md`** (plano do curso, anatomia dos módulos, como
conduzir a aula ao vivo) e **`SOLID/README.md`** (como o aluno faz o curso). Leia-os antes de agir.
Vale para qualquer harness — os `CLAUDE.md` são a convenção do repo, não exclusividade do Claude.

Atalhos:
- Conduzir/retomar a aula: `python3 engine/aula.py status` + `current` (guia em `engine/CLAUDE.md`).
- Quiz/prova: `python3 engine/session.py start <questions.json>` (provas com `--id prova`).
- Exemplos sempre em **C#/.NET**; a prática é **refatoração conduzida no chat** (não há nuvem/custo).
- Ensine também *quando NÃO* aplicar cada princípio (dosagem > dogma; evitar over-engineering).
- Progresso do aluno: `SOLID/.sessions/` — commitado no fork/branch dele; `main` fica zerada.
