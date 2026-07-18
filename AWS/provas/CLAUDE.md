# AWS/provas — Provas de fim de módulo

Uma **prova por módulo**, aplicada ao final para avaliar se o aluno domina o conteúdo antes de avançar.

## O diferencial das provas: feedback por alternativa
Diferente do quiz da aula, a prova dá retorno **baseado na alternativa que o aluno escolheu**:
- se acertou → por que aquela opção está certa;
- se errou → por que a sua escolha está errada **e** qual é a correta e por quê.

Isso vem do campo `feedbacks` no `questions.json` (um texto por opção). Ver `engine/CLAUDE.md`.

## Como aplicar (conduzido pelo Claude)
```bash
python3 engine/session.py start AWS/provas/modulo-01/questions.json --id prova
python3 engine/session.py answer C --id prova
python3 engine/session.py status --id prova
```
O Claude conduz pelo chat, tira dúvidas e explica cada resultado. **Aprovação: 70%.**

## Modo solo (opcional)
```bash
python3 AWS/provas/modulo-01/prova.py
```

## Estrutura
```
provas/
├── CLAUDE.md
└── modulo-01/
    ├── prova.py          ← runner solo
    └── questions.json    ← questões da prova (com feedbacks por alternativa)
```

## Convenção
- Uma pasta `modulo-NN/` por módulo, com `questions.json` mais abrangente que o quiz da aula.
- Sempre incluir `feedbacks` em todas as alternativas — é a razão de ser da prova.
