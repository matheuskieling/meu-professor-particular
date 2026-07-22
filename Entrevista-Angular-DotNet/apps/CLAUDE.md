# Entrevista-Angular-DotNet/apps — Bancos de questões e runners solo

Esta pasta guarda **conteúdo** do curso (bancos de quiz), não drivers. Os drivers (aula, quiz/prova,
revisão, reset) são **compartilhados** e vivem em `engine/` na raiz — veja `engine/CLAUDE.md`.

## O que tem aqui

```
apps/
├── CLAUDE.md
└── modulo-NN/
    ├── questions.json   ← banco do quiz da aula NN (10 questões)
    └── quiz.py          ← runner do MODO SOLO (roda o quiz pelo teclado)
```

- **`questions.json`** — banco do quiz de cada módulo. Formato em `engine/CLAUDE.md`. Aqui as questões
  reforçam conceitos de **entrevista** (Angular em TypeScript, .NET em C#).
- **`quiz.py`** — stub que roda o quiz solo: `python3 Entrevista-Angular-DotNet/apps/modulo-NN/quiz.py`.

As **provas** de módulo e o **simulado geral** ficam em `Entrevista-Angular-DotNet/provas/`. O
**progresso** do aluno fica em `Entrevista-Angular-DotNet/.sessions/`.

## Como isso é usado

- **Conduzido pelo agente (padrão):** `python3 engine/session.py start Entrevista-Angular-DotNet/apps/modulo-01/questions.json`.
- **Solo:** `python3 Entrevista-Angular-DotNet/apps/modulo-01/quiz.py`.
