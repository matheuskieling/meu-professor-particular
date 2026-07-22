# Curso Entrevista Angular + .NET — Como fazer o curso

Preparação **intensiva** para uma **entrevista técnica** full-stack **Angular + .NET**. É um curso
curto e denso, feito para dar **base sólida de conceitos** e treinar você a **explicar cada tema em
voz alta** — do jeito que o entrevistador espera ouvir. Como os outros cursos da plataforma, é um
**one-on-one com o seu agente de IA**: ele conduz, explica aos poucos, tira dúvidas e — o diferencial
aqui — **faz o papel de entrevistador** para você treinar as respostas.

Sem custos, sem certificação. Alvo: **Angular 17+/18** (standalone, signals) e **.NET 8 / C# 12**.

---

## O que você vai treinar

| # | Módulo | Stack | O que você leva |
|---|--------|-------|-----------------|
| 01 | Fundamentos & Ciclo de Vida | Angular | Lifecycle hooks, change detection, `OnPush` |
| 02 | Signals & Reatividade | Angular | `signal`/`computed`/`effect`, Signals vs RxJS, zoneless |
| 03 | Router, Lazy Loading, DI & Interceptors | Angular | Lazy loading, guards, DI, HTTP interceptors |
| 04 | Runtime, GC & Memory | .NET | .NET Framework vs Core vs .NET 8, GC, heap/stack, boxing, vazamentos |
| 05 | IDisposable & Finalizers | .NET | Dispose pattern, `using`, `IAsyncDisposable` |
| 06 | DI, Lifetimes & Repository | .NET | `Singleton`/`Scoped`/`Transient`, Repository/UoW |
| 07 | Async, Escalabilidade & Idempotência | .NET | `async/await`, escala horizontal, idempotência |
| 08 | **Simulado geral** | Ambas | Ensaio final misturando os dois temas |

---

## Os dois jeitos de fazer cada módulo

### 🎧 Jeito 1 — Aula guiada pelo agente (recomendado)
Você **não precisa abrir nenhum arquivo**. Inicie seu harness na pasta do repositório e entre:

- **Pela skill:** **`/retomar-curso Entrevista-Angular-DotNet`** (no Claude Code);
- **Pelas palavras** (qualquer agente): *"vamos começar o curso de entrevista Angular .NET"*, *"bora
  treinar entrevista de onde paramos"*, *"me faz as perguntas de entrevista do módulo de Signals"*.

O agente segue um **roteiro**, explica um ponto por vez, para e pergunta **"posso continuar?"**, faz a
**simulação de entrevista** (ele pergunta, você responde, ele critica), depois o **quiz** e a
**prova** — e **salva onde paramos**.

### 📖 Jeito 2 — Estudar sozinho
Todo o conteúdo também está em arquivos:
- `NN-nome/teoria.md` — o conceito explicado para entrevista, com resposta-modelo.
- `NN-nome/pratica.md` — as perguntas de entrevista + respostas-modelo + erros comuns.
- `apps/modulo-NN/quiz.py` — o quiz pra responder pelo teclado.
- `provas/modulo-NN/prova.py` — a prova do módulo.
- `provas/simulado/prova.py` — o simulado geral.

---

## O fluxo de um módulo

```
  1. TEORIA    → o conceito + "por que perguntam isso" + resposta-modelo
        ↓          o agente explica e pergunta "posso continuar?"
  2. PRÁTICA   → SIMULAÇÃO DE ENTREVISTA: o agente pergunta, você responde, ele critica
        ↓
  3. QUIZ      → fixar (o agente conduz as perguntas no chat) — 10 questões
        ↓
  4. PROVA     → avaliação do módulo (feedback por alternativa, aprovação 70%) — 12 questões
        ↓
  → próximo módulo   ... e no fim, o SIMULADO GERAL (08)
```

---

## Modo véspera (pouco tempo?)

A entrevista é logo? Diga ao agente **"só me testa"**: ele pula direto para as **provas** e o
**simulado geral**, e usa seus erros para decidir o que revisar. Fale quais temas o entrevistador
provavelmente vai cobrar — o agente prioriza esses.

---

## Retomar de onde paramos

Como o **estado é salvo**, pare quando quiser. Na próxima vez, diga "vamos continuar" ou "onde
paramos?" — o agente recupera o ponto exato. Pela skill: **`/retomar-curso Entrevista-Angular-DotNet`**.

## Seu progresso: fork (ou branch) e commit

O repositório principal fica com **progresso zerado**. Pra estudar, faça um **fork** (ou uma branch
`progresso/<seu-nome>`); seu progresso fica em `Entrevista-Angular-DotNet/.sessions/` e é commitado
normalmente. Peça pro agente commitar ao fim de cada sessão — ele já sabe.

## Revisão espaçada (Anki) e reset

- **`/revisar`** (ou "me testa no que já aprendi"): mini-prova sorteando dos módulos concluídos.
- Recomeçar: `python3 engine/reset.py --curso Entrevista-Angular-DotNet`.

---

## Pronto pra começar?

Inicie seu harness na pasta do repositório e digite
**`/retomar-curso Entrevista-Angular-DotNet`** — ou diga **"vamos treinar pra entrevista de Angular
e .NET"**. 🚀 Boa sorte na entrevista!
