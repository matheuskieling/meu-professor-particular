# Prática — Simulação de entrevista (Módulo 02)

Aqui a mesa vira: **você é o candidato**. O agente faz as perguntas **uma a uma**, ouve a sua
resposta **antes** de comentar e então critica — o que faltou, o que ficou impreciso e como soar
mais sênior. As **respostas-modelo** abaixo são o "gabarito falado"; os **erros comuns** são as
armadilhas que derrubam candidato em entrevista real.

Dica de postura: comece pela **ideia central em uma frase**, depois **por que existe** e só então
detalhe. Use os termos certos (pull/push, lazy, memoização, glitch-free) — eles sinalizam senioridade.

---

### Pergunta 1 — O que são Signals e que problema eles resolvem?

**Resposta-modelo:** "Signal é um valor reativo que rastreia suas dependências no momento da
leitura — modelo **pull**, síncrono, sempre tem um valor atual. Ele existe pra permitir change
detection **granular**: em vez de o Zone.js reverificar a árvore de componentes inteira toda vez
que *algo* assíncrono acontece (porque ele não sabe o que mudou), o Angular passa a saber
**exatamente** quem dependia do signal que mudou e atualiza só isso. É a base pro zoneless."

**Erros comuns:** dizer que "é tipo um BehaviorSubject" sem qualificar (Signal é pull/síncrono, sem
subscription); descrever *o que* é sem dizer *o problema* (change detection global caro); esquecer
de citar Zone.js/granularidade.

---

### Pergunta 2 — Como eu leio e escrevo um signal? O que muda entre `set` e `update`?

**Resposta-modelo:** "Leio **chamando como função**: `count()`. Escrevo com `set(valor)` pra trocar
o valor inteiro ou `update(fn)` quando o novo valor deriva do atual, tipo
`count.update(c => c + 1)`. `signal()` retorna um `WritableSignal`. Ler dentro de computed, effect
ou template registra a dependência."

**Erros comuns:** achar que se lê por `.value` (isso é RxJS/`BehaviorSubject`); confundir `set` com
`update`; não saber que a leitura registra a dependência.

---

### Pergunta 3 — Por que `meuArray().push(x)` num signal não atualiza a tela? Como corrigir?

**Resposta-modelo:** "Porque a igualdade padrão do signal é `Object.is`. `push` **muta o array no
lugar** — a referência continua a mesma, `Object.is` dá `true`, e o signal considera que nada
mudou, então ninguém é notificado. Trato o valor como **imutável**: crio uma nova referência, tipo
`arr.update(a => [...a, x])`. Para objeto, `update(o => ({...o, campo: valor}))`."

**Erros comuns:** não saber que a comparação é referência (`Object.is`); tentar `mutate()` (foi
removido); não mencionar imutabilidade.

---

### Pergunta 4 — Explique `computed`. Quando ele recalcula?

**Resposta-modelo:** "`computed` cria um signal **derivado, somente-leitura**, a partir de outros
signals. Ele é **memoizado** (só recalcula quando uma dependência lida realmente muda, por
`Object.is`) e **lazy** (só roda quando alguém lê — se ninguém consome, nunca executa). As
dependências são **dinâmicas**: dependem de quais signals foram lidos na última execução. E é
**glitch-free**: nunca expõe estado intermediário inconsistente. Uso computed pra **estado
derivado**, sempre."

**Erros comuns:** dizer que "recalcula sempre que a dependência muda" sem o "e alguém lê" (lazy);
não citar memoização; colocar efeito colateral dentro do computed (ele deve ser puro).

---

### Pergunta 5 — `computed` vs `effect`: qual a diferença e quando usar cada um?

**Resposta-modelo:** "`computed` **produz um valor** derivado — puro, memoizado, lazy. `effect`
**executa um efeito colateral** quando dependências mudam: log, sincronizar com localStorage,
integrar com algo não-reativo. Regra de ouro: **estado derivado é computed**, nunca effect. Se eu
me pego escrevendo `effect(() => this.x.set(...))`, provavelmente devia ser um computed — inclusive
porque effect por padrão nem deixa escrever signal (precisaria de `allowSignalWrites`, que é cheiro
de design)."

**Erros comuns:** usar effect pra derivar estado; não saber que effect não escreve signal por
padrão; não conseguir dar um caso de uso legítimo pra effect.

---

### Pergunta 6 — Quando roda um `effect` e como faço limpeza?

**Resposta-modelo:** "Roda uma vez ao ser criado e depois de forma **agendada** (após a change
detection) quando uma dependência lida muda — não é síncrono a cada `set`; múltiplos sets no mesmo
tick coalescem. Pra limpeza, a função recebe um `onCleanup` onde registro o teardown (ex.:
`clearTimeout`, fechar conexão); ele roda **antes da próxima execução** e no **destroy**. Criado no
injection context, ele já se limpa no destroy do componente."

**Erros comuns:** achar que effect é síncrono a cada mudança; não conhecer `onCleanup`; não saber
que ele roda uma vez na criação.

---

### Pergunta 7 — Signals vs Observables: quando usar cada um?

**Resposta-modelo:** "Signal é **pull e síncrono** — responde 'qual é o valor agora?'. Ótimo pra
**estado** de UI e derivados. Observable é **push e assíncrono** — responde 'o que acontece ao
longo do tempo?'. Ótimo pra HTTP, debounce, cancelamento, WebSocket, coordenar múltiplos streams,
porque tem operadores (`switchMap`, `debounceTime`, `retry`). Na prática: **estado da tela em
Signals, o assíncrono/temporal em RxJS**. E eles fazem interop."

**Erros comuns:** tratar como "um substitui o outro"; não citar pull vs push; não lembrar que RxJS
tem operadores que Signals não têm.

---

### Pergunta 8 — Signals substituem o RxJS?

**Resposta-modelo:** "Não. Signals resolvem **estado síncrono** com reatividade granular; RxJS
resolve o **tempo** — streams, eventos, cancelamento, backpressure, coordenação. O Angular
inclusive dá interop oficial (`toSignal`/`toObservable`), o que mostra que a intenção é conviver, não
substituir. O que muda é que passei a usar menos RxJS pra *estado* (onde antes usava
`BehaviorSubject`), mas o RxJS continua essencial pro assíncrono."

**Erros comuns:** dizer que "sim, o RxJS vai morrer"; não conhecer a interop; não saber onde RxJS
ainda é insubstituível.

---

### Pergunta 9 — Como funciona a interop entre Signals e RxJS? Cuidados com `toSignal`?

**Resposta-modelo:** "`toSignal(obs$)` converte um Observable num signal e **desinscreve sozinho**
no destroy — dá pra passar `initialValue`, senão o signal fica `undefined` até a 1ª emissão.
`toObservable(sig)` vai no outro sentido, útil quando quero aplicar operadores RxJS a um signal —
tipo `toObservable(termo).pipe(debounceTime(300), switchMap(...))` pra uma busca. E no template o
`async pipe` continua sendo ótimo pra consumir stream com unsubscribe automático."

**Erros comuns:** esquecer o `initialValue` (signal `undefined`); não saber que `toSignal`
desinscreve sozinho; não dar um caso concreto (busca com debounce).

---

### Pergunta 10 — O que é zoneless e como Signals ajudam? Relação com OnPush?

**Resposta-modelo:** "Zoneless é rodar o Angular **sem Zone.js** —
`provideExperimentalZonelessChangeDetection()` (ainda experimental). Sem o monkey-patch global, o
que dispara a atualização passa a ser a **mudança de signal** (mais alguns gatilhos de template),
não 'qualquer coisa assíncrona'. Signals viabilizam isso porque o framework sabe **o que** mudou e
**quem** depende. Isso casa com **OnPush**: ler um signal no template marca o componente pra
checagem quando ele muda, reduzindo `markForCheck()` manual."

**Erros comuns:** achar que zoneless já é o padrão estável; não ligar Signals ao gatilho da
atualização; não saber a relação com OnPush.

---

### Pergunta 11 — Com Signals, ainda preciso me preocupar com unsubscribe? Por quê?

**Resposta-modelo:** "Sim, sempre que uso RxJS. Signal não tem subscription, então não vaza; mas
HTTP, WebSocket, `interval`, `valueChanges` continuam sendo Observables. Se eu inscrever manualmente
um stream de **vida longa** e não desinscrever, vaza memória. Prefiro `async pipe` no template ou
`takeUntilDestroyed()`, que desinscrevem sozinhos. Request HTTP pontual não vaza porque **completa**
após 1 emissão, mas stream contínuo sim."

**Erros comuns:** dizer que "Signals eliminam o problema de unsubscribe"; não distinguir stream
pontual (HTTP) de vida longa; não conhecer `takeUntilDestroyed`.

---

### Pergunta 12 — Signal inputs: o que muda em relação a `@Input()` e `ngOnChanges`?

**Resposta-modelo:** "Com `input()` o input vira um **signal read-only** no filho —
`input.required<T>()` pra obrigatório. Reajo a mudanças de input com `computed`/`effect` **sem
precisar de `ngOnChanges`**. `output()` substitui `@Output()`/`EventEmitter` com API mais enxuta, e
`model()` é two-way (input + output) pra usar com `[(x)]`. Combinado, deixa o componente reativo por
padrão e sem lifecycle boilerplate."

**Erros comuns:** achar que signal input é gravável no filho (é read-only); não saber que dispensa
`ngOnChanges`; confundir `model()` com `output()`.
