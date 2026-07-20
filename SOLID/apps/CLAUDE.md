# SOLID/apps — Bancos de questões e runners solo do curso de SOLID

Esta pasta guarda **conteúdo** do curso de SOLID, não drivers. Os drivers (aula, quiz/prova, revisão,
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
  Neste curso, muitas questões mostram um trecho de **C#** e perguntam qual princípio é violado.
- **`quiz.py`** — stub que roda o quiz no modo solo: `python3 SOLID/apps/modulo-NN/quiz.py`. Só
  importa o motor de `engine/quiz_engine.py` e aponta para o `questions.json` ao lado.

As **provas** de módulo ficam em `SOLID/provas/modulo-NN/`. O **progresso** do aluno fica em
`SOLID/.sessions/` (versionado no fork/branch).

## Como isso é usado

- **Modo conduzido pelo Claude (padrão):** `engine/session.py` conduz o quiz a partir do
  `questions.json` — o Claude apresenta as perguntas no chat, o aluno responde em linguagem natural e
  tira dúvidas. Ex.: `python3 engine/session.py start SOLID/apps/modulo-01/questions.json`.
- **Modo solo:** `python3 SOLID/apps/modulo-01/quiz.py` (responde pelo teclado).

## Ao criar/editar um módulo neste curso
1. Crie `apps/modulo-NN/questions.json` com as 10 questões do quiz.
2. Crie `apps/modulo-NN/quiz.py` (copie de outro módulo — muda só o docstring).
3. A prova vai em `provas/modulo-NN/` (12 questões, com `feedbacks` por alternativa).
