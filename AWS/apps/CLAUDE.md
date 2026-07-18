# AWS/apps — Bancos de questões e runners solo do curso de AWS

Esta pasta guarda **conteúdo** do curso de AWS, não drivers. Os drivers (aula, quiz/prova, revisão,
reset) são **compartilhados** e vivem em `engine/` na raiz do repositório — veja `engine/CLAUDE.md`.

## O que tem aqui

```
apps/
├── CLAUDE.md
└── modulo-NN/
    ├── questions.json   ← banco de questões do quiz da aula NN (10 questões)
    └── quiz.py          ← runner do MODO SOLO (roda o quiz pelo teclado)
```

- **`questions.json`** — o banco do quiz de cada módulo. Formato documentado em `engine/CLAUDE.md`.
- **`quiz.py`** — stub que roda o quiz no modo solo: `python3 AWS/apps/modulo-NN/quiz.py`. Ele só
  importa o motor de `engine/quiz_engine.py` e aponta para o `questions.json` ao lado.

As **provas** de módulo ficam em `AWS/provas/modulo-NN/` e os **simulados de certificação** em
`AWS/certificacoes/`. O **progresso** do aluno fica em `AWS/.sessions/` (versionado no fork).

## Como isso é usado

- **Modo conduzido pelo Claude (padrão):** o driver `engine/session.py` conduz o quiz/prova a partir
  do `questions.json` — o Claude apresenta as perguntas no chat, o aluno responde em linguagem
  natural e tira dúvidas. Ex.: `python3 engine/session.py start AWS/apps/modulo-01/questions.json`.
- **Modo solo:** `python3 AWS/apps/modulo-01/quiz.py` (responde pelo teclado).

## Ao criar um módulo novo neste curso
1. Crie `apps/modulo-NN/questions.json` com as 10 questões do quiz.
2. Crie `apps/modulo-NN/quiz.py` (copie de outro módulo — muda só o docstring).
3. A prova vai em `provas/modulo-NN/` (12 questões, com `feedbacks` por alternativa).
