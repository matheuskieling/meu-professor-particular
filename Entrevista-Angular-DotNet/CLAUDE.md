# Curso 3 — Entrevista Angular + .NET (intensivo rápido)

Curso **intensivo e enxuto** de preparação para **entrevista técnica** de desenvolvedor(a)
full-stack **Angular + .NET**. Diferente dos outros cursos da plataforma, este nasceu com um
**prazo real**: uma entrevista marcada. O objetivo não é formar do zero — é **firmar uma base
sólida de conceitos** e treinar a **articulação das respostas** (falar como numa entrevista).

O foco são os temas que caem em entrevista de nível pleno/sênior nessas duas stacks, com **provas
em formato de perguntas de entrevista** (o candidato precisa saber *explicar*, não só marcar a
alternativa certa).

## Público-alvo e premissas

Desenvolvedor(a) que **já programa** em Angular e/ou .NET e vai para uma entrevista. Não é curso de
sintaxe básica: assume-se que a pessoa já viu componentes, services, classes e C#. O que este curso
faz é **consolidar os conceitos que o entrevistador cobra** e ensinar a **respondê-los com clareza**.

**Curso dependente de linguagem, mas SEM escolha:** é *sobre* duas stacks específicas. Angular →
exemplos em **TypeScript**; .NET → exemplos em **C#**. Não há `preferencias.json` nem pergunta de
linguagem (isso é só para cursos agnósticos como o SOLID). Alinhe os exemplos a **Angular 17+/18**
(standalone, signals, `@if`/`@for`) e **.NET 8 / C# 12**, mas mencione como era antes quando o
entrevistador provavelmente perguntar (ex.: NgModules, `*ngIf`).

## Objetivos de aprendizado

Ao final, o(a) candidato(a) deve conseguir **explicar em voz alta, com exemplo**:

**Angular**
- O ciclo de vida de um componente (todos os hooks, quando cada um dispara, `OnPush`).
- Change detection: Zone.js, `OnPush`, e o caminho para **zoneless**.
- **Signals**: `signal`/`computed`/`effect`, e como se comparam a RxJS/`Observable`.
- **Lazy loading** de rotas, guards, resolvers e o ganho de bundle.
- **Injeção de dependência** do Angular e **HTTP Interceptors** (auth, log, retry, erro).

**.NET**
- **Garbage Collector**: gerações, managed vs unmanaged, stack vs heap, boxing, LOH, `Span<T>`.
- **Gerenciamento de memória** e vazamentos comuns (eventos, `static`, `IDisposable` esquecido).
- **`IDisposable`** / `using` / o Dispose pattern / finalizers / `IAsyncDisposable`.
- **Injeção de dependência** no .NET e os **service lifetimes** (`Singleton`/`Scoped`/`Transient`)
  — incluindo as armadilhas (captured dependency, `Scoped` dentro de `Singleton`).
- **Repository Pattern** (e Unit of Work) — o quê, por quê e quando NÃO usar.
- **`async`/`await`**, thread pool, **escalabilidade** (stateless, escala horizontal) e
  **idempotência** de APIs.

---

## O formato do curso: aula ao vivo (one-on-one) + treino de entrevista

Idêntico ao padrão da plataforma (ver `../CLAUDE.md` e `../engine/CLAUDE.md`). O agente **conduz**:
explica um ponto por vez, com as próprias palavras, convida dúvidas e pergunta **"posso continuar?"**
antes de avançar. O estado (onde paramos) é salvo em `Entrevista-Angular-DotNet/.sessions/`.

Operado pelo driver **`engine/aula.py`**, que lê o **`roteiro.json`** de cada módulo.

**A "prática" deste curso é uma SIMULAÇÃO DE ENTREVISTA.** Não há nuvem nem refatoração de arquivos:
na fase `pratica`, o agente **vira o entrevistador** — faz a pergunta como cairia numa entrevista,
deixa o aluno responder em voz alta (texto), e então **critica a resposta**: o que faltou, o que
diria a mais, como soar mais sênior. É treino de articulação, não de digitar código.

**Como o agente conduz uma aula:**
1. `python3 engine/aula.py current` (ou `start Entrevista-Angular-DotNet/NN-nome/roteiro.json` na 1ª vez).
2. Lê os `pontos` e **narra com as próprias palavras** — nunca cola os bullets crus.
3. No `checkpoint`, pausa: convida dúvidas e pergunta se pode seguir.
4. Ao "pode seguir", `aula.py next`. Dúvida relevante vira `aula.py note "..."`.
5. Em beats `pratica`, faz o papel de **entrevistador** (pergunta → resposta do aluno → crítica).
6. Em beats `quiz`/`prova`, dispara o `session.py` correspondente.
7. Para retomar: `aula.py current` volta ao ponto salvo.

> **Modo turbo (véspera da entrevista).** Se o aluno pedir "só me testa" ou estiver com pouco tempo,
> o agente pode pular direto para as **provas** e o **simulado geral** (`08-simulado`), usando os
> erros para decidir o que revisar na teoria. Priorize os temas que o aluno disser que o colega citou.

> **As provas devem SOAR como entrevista real — não como um teste do material.** O entrevistador não
> se limita ao que "foi estudado": ele puxa temas vizinhos, pede comparações, pergunta "e se...",
> "quando você NÃO usaria isso?", "já teve um problema desses em produção?". Portanto, as provas e o
> simulado podem (e devem) incluir perguntas que exigem raciocínio além da teoria literal do módulo —
> desde que na mesma vizinhança conceitual. O objetivo não é decorar o `teoria.md`, é **estar pronto
> pra conversa real**.

> **Quando o aluno travar numa pergunta, PARE e ensine junto — não só marque "errou".** Este é um
> pedido explícito do aluno: se ele não souber responder (na simulação de entrevista, no quiz ou na
> prova), o agente não deve apenas dar a resposta certa e seguir. Deve **transformar aquilo numa
> mini-aula ali na hora**: explicar o conceito, dar a resposta-modelo, checar se entendeu, e só então
> retomar. "Aprender juntos no ponto de dor" é parte do método deste curso.

## Como cada módulo funciona (anatomia)

Mesma anatomia da plataforma, adaptada a um curso de **conceitos + entrevista**:

### 0. Roteiro da aula — `NN-nome/roteiro.json`
Os "beats" ordenados (teoria → simulação de entrevista → quiz → prova → fechamento). Formato no
cabeçalho de `engine/aula.py`.

### 1. Teoria — `NN-nome/teoria.md`
O **conceito** explicado para entrevista: definição precisa, **por que** o entrevistador pergunta,
exemplo de código (TypeScript p/ Angular, C# p/ .NET), armadilhas/pegadinhas comuns, e um bloco
**"como responder numa entrevista"** com uma resposta-modelo curta. Glossário e checagem ao final.

### 2. Prática = simulação de entrevista — `NN-nome/pratica.md`
Um roteiro de **perguntas de entrevista** sobre o módulo (da mais comum à pegadinha), cada uma com:
a pergunta, uma **resposta-modelo** (o que um sênior diria) e os **erros comuns** que derrubam o
candidato. O agente usa isso para simular o entrevistador no chat.

### 3. Quiz da aula — `apps/modulo-NN/questions.json` (10 questões)
Reforça a aula. Conduzido pelo agente no chat (`engine/session.py`) ou solo (`quiz.py`). Foco em
**fixar o conceito** (múltipla escolha objetiva).

### 4. Prova do módulo — `provas/modulo-NN/questions.json` (12 questões)
Avaliação de fim de módulo com **feedback por alternativa** (`feedbacks`). Aprovação **70%**.
Cenários de entrevista ("o entrevistador pergunta X; qual resposta está correta?").

### 5. Simulado geral — `provas/simulado/questions.json` (~20 questões)
Módulo `08-simulado`: mistura Angular + .NET, no formato do dia da entrevista. É o ensaio final.

> **Fluxo de um módulo:** teoria (conceito p/ entrevista) → prática (simular entrevista no chat) →
> quiz (fixar) → prova (avaliar, 70%). Tudo Python puro no motor, **sem dependências**. Formato do
> `questions.json` em `engine/CLAUDE.md`.

---

## Plano completo do curso

**Legenda:** ✅ pronto · 🔜 próximo · ⬜ planejado.

| # | Módulo | Stack | O que leva | Status |
|---|--------|-------|------------|--------|
| 01 | Fundamentos & Ciclo de Vida | Angular | Componentes, change detection, todos os lifecycle hooks, `OnPush` | ✅ |
| 02 | Signals & Reatividade | Angular | `signal`/`computed`/`effect`, Signals vs RxJS, zoneless, `async` pipe | ✅ |
| 03 | Router, Lazy Loading, DI & Interceptors | Angular | Lazy loading, guards/resolvers, DI do Angular, HTTP interceptors | ✅ |
| 04 | Runtime, GC & Memory Management | .NET | CLR, stack vs heap, gerações do GC, boxing, LOH, `Span<T>`, vazamentos | ✅ |
| 05 | IDisposable, `using` & Finalizers | .NET | Dispose pattern, recursos não gerenciados, `IAsyncDisposable` | ✅ |
| 06 | DI, Service Lifetimes & Repository | .NET | Container DI, `Singleton`/`Scoped`/`Transient` + armadilhas, Repository/UoW | ✅ |
| 07 | Async, Escalabilidade & Idempotência | .NET | `async/await`, thread pool, escala horizontal/stateless, idempotência | ✅ |
| 08 | **Simulado geral** | Ambas | Ensaio final misturando os dois temas (~20 questões) | ✅ |

> Ordem sugerida na véspera: se o tempo for curto, faça as **provas** de cada módulo direto e caia no
> **simulado** — volte à teoria só nos temas que errar. Se houver tempo, siga 01 → 07 em ordem.

---

## Estrutura de arquivos

Os **drivers** são compartilhados e ficam em **`engine/`** na raiz (ver `engine/CLAUDE.md`); este
curso é só conteúdo.

```
Entrevista-Angular-DotNet/
├── README.md                 ← como fazer o curso (para o aluno)
├── CLAUDE.md                 ← este arquivo
├── AGENTS.md                 ← ponteiro para este CLAUDE.md (outros harnesses)
├── .sessions/                ← progresso do aluno (versionado no fork/branch; zerado na main)
├── 01-angular-fundamentos-ciclo-vida/
│   ├── roteiro.json          ← roteiro da aula ao vivo (o agente conduz)
│   ├── teoria.md
│   └── pratica.md            ← perguntas de entrevista + respostas-modelo
├── 02-... 07-...             ← mesmo formato
├── 08-simulado/roteiro.json  ← só dispara o simulado geral
├── apps/                     ← bancos do quiz + runners solo (SEM drivers)
│   ├── CLAUDE.md
│   └── modulo-NN/{questions.json, quiz.py}
└── provas/                   ← provas de fim de módulo + simulado geral
    ├── CLAUDE.md
    ├── modulo-NN/{questions.json, prova.py}
    └── simulado/{questions.json, prova.py}
```

## Convenções específicas deste curso

- **Duas linguagens, sem escolha.** Angular → **TypeScript**; .NET → **C#**. Não há mecanismo de
  preferência de linguagem (isso é só para cursos agnósticos). Alvo: **Angular 17+/18** e **.NET 8**.
- **Foco em entrevista.** Todo conceito deve vir com o "**por que perguntam isso**" e uma
  **resposta-modelo** curta. A prática é **simulação de entrevista falada**, não código rodando.
- **Sem custos, sem teardown, sem certificação oficial.** Não há camada `certificacoes/`.
- **Precisão técnica.** É prep de entrevista — nada de meia-verdade. Quando um tema tiver nuance
  (ex.: "o GC roda em toda geração ao mesmo tempo?"), explique a nuance, que é onde o candidato brilha.
- **Progresso** em `Entrevista-Angular-DotNet/.sessions/` — versionado no fork/branch; `main` zerada.

## Estado atual

- ✅ **Curso completo:** 7 módulos + simulado geral, cada módulo com roteiro + teoria + prática
  (simulação de entrevista) + quiz (10) + prova (12 com feedback por alternativa).
- 🎓 Começar/retomar: `/retomar-curso Entrevista-Angular-DotNet` (ou "vamos fazer o curso de
  entrevista Angular .NET").
