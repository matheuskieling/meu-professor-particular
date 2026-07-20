# Curso 2 — SOLID (Princípios de Design Orientado a Objetos)

Curso focado nos **cinco princípios SOLID** de design orientado a objetos, do fundamento à
aplicação prática. O objetivo é dar ao desenvolvedor **critério** para escrever código que resiste
à mudança: reconhecer quando um design está apodrecendo, saber qual princípio corrige o quê, e
refatorar com segurança — sem cair no exagero de aplicar princípio por princípio.

Curso **menor e mais denso** que o de AWS: **7 módulos**, sem custos, sem certificação oficial
(SOLID não tem exame). A "prática" aqui não é infraestrutura na nuvem — é **refatoração de código**.

## Público-alvo

Desenvolvedor que já programa em OO e quer parar de escrever código que quebra a cada mudança. Não é
um curso de sintaxe: é sobre **decisões de design** — onde colocar a fronteira entre classes, quando
criar uma abstração, quando NÃO criar.

**SOLID é agnóstico de linguagem** (vale para C#, Java, TypeScript, Python, Kotlin, PHP...). Por isso
o curso **pergunta ao aluno, no início, em qual linguagem ele quer os exemplos** e adapta tudo a ela —
ver "Linguagem dos exemplos (agnóstico)" abaixo. Os arquivos de conteúdo trazem os exemplos em **C#**
como *referência-base*; o agente **traduz ao vivo** para a linguagem escolhida ao conduzir.

## Objetivos de aprendizado

Ao final, o aluno deve ser capaz de:
- Explicar **por que** SOLID existe: acoplamento, coesão, os sintomas de um design ruim (rigidez,
  fragilidade, imobilidade).
- Reconhecer e nomear cada um dos 5 princípios, e o **code smell** que cada um ataca.
- **SRP** — separar responsabilidades por "ator"/razão de mudança, sem estilhaçar em micro-classes.
- **OCP** — estender comportamento sem editar código existente, via polimorfismo/abstração.
- **LSP** — desenhar hierarquias em que o subtipo realmente substitui o supertipo (contratos).
- **ISP** — quebrar interfaces "gordas" para que ninguém dependa do que não usa.
- **DIP** — inverter dependências para abstrações, e ligar isso à **injeção de dependência** do
  ecossistema da linguagem escolhida (container do .NET, Spring, NestJS, etc.).
- Refatorar um sistema pequeno aplicando os cinco juntos, sabendo **dosar** (evitar over-engineering)
  e enxergar a ponte para **Design Patterns**.

---

## O formato do curso: aula ao vivo (one-on-one)

Idêntico ao padrão da plataforma (ver `../CLAUDE.md` e `../engine/CLAUDE.md`). O Claude **conduz** a
aula: explica um ponto por vez, com as próprias palavras, convida dúvidas e pergunta **"posso
continuar?"** antes de avançar. O estado (onde paramos) é salvo em `SOLID/.sessions/`, então dá pra
parar e retomar.

Operado pelo driver **`engine/aula.py`**, que lê o **`roteiro.json`** do módulo. Os `.md`
(teoria/prática) continuam existindo para estudo solo.

**Como o Claude conduz uma aula:**
1. `python3 engine/aula.py current` (ou `start SOLID/NN-nome/roteiro.json` na primeira vez).
2. Lê os `pontos` e **narra com as próprias palavras** — nunca cola os bullets crus.
3. No `checkpoint`, pausa: convida dúvidas e pergunta se pode seguir.
4. Ao "pode seguir", `aula.py next`. Dúvida relevante vira `aula.py note "..."`.
5. Em beats de fase `quiz`/`prova`, dispara o `session.py` correspondente.
6. Para retomar: `aula.py current` volta ao ponto salvo.

## Linguagem dos exemplos (agnóstico)

SOLID é sobre **design**, não sobre sintaxe — então a linguagem dos exemplos é uma **preferência do
aluno**, não uma característica do curso. O agente NÃO precisa que o aluno edite arquivo nenhum: a
escolha é uma pergunta no começo e o resto é automático.

**Fonte da verdade da escolha:** `SOLID/.sessions/preferencias.json` →
`{ "linguagem": "<nome>" }` (versionado no fork/branch, como o resto do progresso; some no `reset`).

**Como o agente conduz (no beat `intro` de QUALQUER módulo):**
1. **Lê** `SOLID/.sessions/preferencias.json`.
   - **Não existe** → pergunta: *"Em qual linguagem você quer os exemplos? (C#, Java, TypeScript,
     Python, Go, Kotlin, PHP...)"*, e **grava** a resposta no arquivo (crie o `.sessions/` se preciso).
   - **Existe** → confirma rápido: *"Vou usar **<linguagem>** nos exemplos — é só avisar se quiser
     trocar."* Se o aluno pedir pra trocar, reescreve o arquivo.
2. **Ao longo de todo o módulo** (teoria narrada, prática, quiz e prova conduzidos no chat), **traduz
   os exemplos para a linguagem escolhida**: código, tipos, e as convenções idiomáticas dela
   (ex.: `record` do C# ↔ `data class`/`@dataclass`/`interface`; propriedades ↔ getters; o container de
   DI do .NET ↔ Spring/NestJS/etc. no módulo DIP). Os **conceitos e os nomes dos exemplos**
   (`OrderProcessor`, `Employee`, atores/razões-para-mudar) permanecem — muda só o sotaque.
3. Os arquivos (`teoria.md`, `pratica.md`, os `questions.json`) ficam em **C# como referência-base** e
   **não são reescritos** por conta da escolha — a adaptação é **ao vivo**, na fala do agente. Quem
   estuda **solo** pelos `.md` lê em C# (a base).

> Regra: sempre que for **mostrar código ou citar um nome de tipo/recurso**, use a linguagem do
> `preferencias.json`. Na dúvida sobre um idioma específico, priorize deixar o **princípio de design**
> claro — a sintaxe é só o veículo.

## Como cada módulo funciona (anatomia)

Mesma anatomia da plataforma, adaptada a um curso de **código** (não de infra):

### 0. Roteiro da aula — `NN-nome/roteiro.json`
Os "beats" ordenados (teoria → prática → quiz → prova → fechamento). Formato no cabeçalho de
`engine/aula.py`.

### 1. Teoria — `NN-nome/teoria.md`
O **quê** e o **porquê** do princípio, com exemplos de código (**C# como referência-base**, traduzidos
ao vivo para a linguagem do aluno): o "antes" (código com o cheiro) e o "depois" (refatorado).
Analogias, armadilhas comuns (inclusive **over-engineering**), glossário e uma **checagem de
entendimento** ao final.

### 2. Prática guiada — `NN-nome/pratica.md`
**Refatoração guiada no chat** (não há nuvem/custo/teardown aqui). O Claude apresenta um trecho de
código com o cheiro do módulo — **na linguagem escolhida pelo aluno** (partindo do C# de referência do
`.md`); o aluno propõe a refatoração e o Claude conduz/critica passo a passo. O `.md` traz o código de
partida, dicas progressivas e uma solução de referência comentada.

### 3. Quiz da aula — `apps/modulo-NN/questions.json` (10 questões)
Reforça a aula. Conduzido pelo Claude no chat (`engine/session.py`), ou solo (`quiz.py`). Foco em
**reconhecer o princípio e o smell** — muitas questões mostram um trecho e perguntam "qual princípio
está sendo violado?".

### 4. Prova do módulo — `provas/modulo-NN/questions.json` (12 questões)
Avaliação de fim de módulo com **feedback por alternativa** (`feedbacks`). Aprovação **70%**.
Cenários mais realistas ("dado este design, qual mudança respeita o princípio sem violar outro?").

> **Fluxo de um módulo:** teoria (o porquê + antes/depois na linguagem do aluno) → prática (refatorar no chat) →
> quiz (fixar) → prova (avaliar, 70%). Tudo Python puro no motor, **sem dependências**. Formato do
> `questions.json` em `engine/CLAUDE.md`.

---

## Plano completo do curso

**Legenda:** ✅ pronto · 🔜 próximo · ⬜ planejado.

| # | Módulo | Objetivo | Status |
|---|--------|----------|--------|
| 01 | Fundamentos de Design | Por que SOLID existe: acoplamento x coesão, os sintomas do design podre (rigidez, fragilidade, imobilidade), code smells, origem (Uncle Bob). | ✅ |
| 02 | **S**RP — Responsabilidade Única | "Uma única razão para mudar"; responsabilidade por ator; separar sem estilhaçar. | ✅ |
| 03 | **O**CP — Aberto/Fechado | Aberto para extensão, fechado para modificação; polimorfismo e Strategy; o `switch` que cresce. | ✅ |
| 04 | **L**SP — Substituição de Liskov | Subtipos substituíveis; Retângulo/Quadrado; pré/pós-condições e invariantes; herança x composição. | ✅ |
| 05 | **I**SP — Segregação de Interfaces | Interfaces enxutas; não forçar implementar o que não se usa; "fat interfaces". | ✅ |
| 06 | **D**IP — Inversão de Dependência | Depender de abstrações; DI e o container do .NET; a diferença DI x DIP x IoC. | ✅ |
| 07 | Capstone — SOLID na prática | Refatorar um sistema pequeno aplicando os 5; dosar (evitar over-engineering); ponte para Design Patterns. | ✅ |

> Ordem recomendada: 01 → 07 em sequência. O 01 dá o vocabulário (acoplamento/coesão/smells) que os
> demais usam; o 07 costura tudo. Dá pra estudar um princípio isolado, mas o capstone assume os 5.

---

## Estrutura de arquivos

Os **drivers** são compartilhados e ficam em **`engine/`** na raiz (ver `engine/CLAUDE.md`); este
curso é só conteúdo.

```
SOLID/
├── README.md                 ← como fazer o curso (para o aluno)
├── CLAUDE.md                 ← este arquivo
├── AGENTS.md                 ← ponteiro para este CLAUDE.md (outros harnesses)
├── .sessions/                ← progresso do aluno (versionado no fork/branch; zerado na main)
├── 01-fundamentos/
│   ├── roteiro.json          ← roteiro da aula ao vivo (o Claude conduz)
│   ├── teoria.md
│   └── pratica.md
├── 02-srp/ ... 07-capstone/  ← mesmo formato
├── apps/                     ← bancos do quiz + runners solo (SEM drivers)
│   ├── CLAUDE.md
│   └── modulo-NN/{questions.json, quiz.py}
└── provas/                   ← provas de fim de módulo (feedback por alternativa)
    ├── CLAUDE.md
    └── modulo-NN/{questions.json, prova.py}
```

## Convenções específicas deste curso

- **Linguagem escolhida pelo aluno (agnóstico).** SOLID vale para qualquer linguagem OO; o curso
  pergunta a linguagem no início e salva em `SOLID/.sessions/preferencias.json` — ver seção "Linguagem
  dos exemplos (agnóstico)" acima e a convenção geral da plataforma em `../CLAUDE.md`. Use o **idioma
  idiomático** da linguagem escolhida (ex.: em C#, `record`/interfaces/DI do
  `Microsoft.Extensions.DependencyInjection`; noutra, o equivalente). Os `.md` guardam C# como
  referência-base. Sem necessidade de rodar código — a prática é raciocínio de design no chat.
- **Dosagem > dogma.** SOLID mal aplicado vira over-engineering. Todo módulo deve mostrar também
  *quando NÃO* aplicar o princípio à risca. Isso é parte do conteúdo, não um detalhe.
- **Sem custos, sem teardown, sem certificação.** Não há a camada `certificacoes/` da AWS.
- **Progresso** em `SOLID/.sessions/` — versionado no fork/branch do aluno; `main` fica zerada.

## Estado atual

- ✅ **Curso completo:** 7 módulos, cada um com roteiro + teoria + prática + quiz (10) + prova (12
  com feedback por alternativa).
- 🎓 Começar/retomar: `/retomar-curso SOLID` (ou "vamos começar o curso de SOLID").
