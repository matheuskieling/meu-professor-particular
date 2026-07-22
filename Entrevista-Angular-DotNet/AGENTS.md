# Instruções para agentes — curso Entrevista Angular + .NET

Fonte de verdade deste diretório: **`Entrevista-Angular-DotNet/CLAUDE.md`** (plano do curso, anatomia
dos módulos, como conduzir a aula) e **`Entrevista-Angular-DotNet/README.md`** (como o aluno faz o
curso). Leia-os antes de agir. Vale para qualquer harness — os `CLAUDE.md` são a convenção do repo.

Atalhos:
- Conduzir/retomar a aula: `python3 engine/aula.py status` + `current` (guia em `engine/CLAUDE.md`).
- Quiz/prova: `python3 engine/session.py start <questions.json>` (provas com `--id prova`).
- Exemplos: **TypeScript** para Angular, **C#** para .NET (alvo Angular 17+/18 e .NET 8). Sem escolha
  de linguagem — este curso é *sobre* essas stacks.
- A **prática é simulação de entrevista**: o agente vira entrevistador, pergunta, ouve a resposta do
  aluno e critica (o que faltou, como soar mais sênior). Não há código rodando nem nuvem.
- Todo conceito vem com o "**por que perguntam isso**" e uma **resposta-modelo** curta.
- Prazo real: é prep de entrevista. Se o aluno pedir, pule para provas/simulado e revise só os erros.
- As provas devem SOAR como entrevista real: podem puxar temas vizinhos e perguntas "e se...", não só
  o material literal do módulo. O alvo é estar pronto pra conversa, não decorar o teoria.md.
- Quando o aluno TRAVAR numa pergunta, PARE e ensine junto (mini-aula na hora) — pedido explícito do
  aluno; nunca só marcar "errou" e seguir.
- Progresso do aluno: `Entrevista-Angular-DotNet/.sessions/` — commitado no fork/branch; `main` zerada.
