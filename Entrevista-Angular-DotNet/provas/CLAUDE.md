# Entrevista-Angular-DotNet/provas — Provas de módulo + simulado geral

Uma **prova por módulo** (12 questões) e um **simulado geral** (~20 questões, misturando Angular +
.NET) para o ensaio final.

## O diferencial das provas: feedback por alternativa
Diferente do quiz da aula, a prova dá retorno **baseado na alternativa escolhida**:
- se acertou → por que aquela opção está certa;
- se errou → por que a sua escolha está errada **e** qual é a correta e por quê.

Isso vem do campo `feedbacks` no `questions.json` (um texto por opção). Ver `engine/CLAUDE.md`.

## Como aplicar (conduzido pelo agente)
```bash
python3 engine/session.py start Entrevista-Angular-DotNet/provas/modulo-01/questions.json --id prova
python3 engine/session.py start Entrevista-Angular-DotNet/provas/simulado/questions.json --id simulado
```
O agente conduz pelo chat, tira dúvidas e explica cada resultado. **Aprovação: 70%.**

## Modo solo (opcional)
```bash
python3 Entrevista-Angular-DotNet/provas/modulo-01/prova.py
python3 Entrevista-Angular-DotNet/provas/simulado/prova.py
```

## Estrutura
```
provas/
├── CLAUDE.md
├── modulo-NN/{prova.py, questions.json}   ← prova do módulo (12 questões, com feedbacks)
└── simulado/{prova.py, questions.json}     ← simulado geral (~20 questões, Angular + .NET)
```

## Convenção
- Uma pasta `modulo-NN/` por módulo, com `questions.json` mais abrangente que o quiz da aula.
- Sempre incluir `feedbacks` em todas as alternativas — é a razão de ser da prova.
- Cenários realistas de **entrevista**: "o entrevistador pergunta X; qual resposta está correta?".
