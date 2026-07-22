# Módulo 02 — Angular: Signals & Reatividade

Signals são o modelo de reatividade primária do Angular a partir da v16/17. Este módulo te
prepara pra pergunta que quase sempre cai em entrevista de Angular hoje: **"o que são Signals,
que problema resolvem e como se comparam ao RxJS e ao Zone.js?"**. A ideia é você não só saber
a resposta certa, mas conseguir **explicar em voz alta** com os termos corretos (pull vs push,
lazy, memoização, glitch-free) e defender os trade-offs como um dev sênior.

---

## 1. O que são Signals e por que existem

Um **Signal** é um "container reativo" de um valor: além de guardar o valor, ele sabe **quem
depende dele**. Quando o valor muda, o Angular consegue atualizar **exatamente** os consumidores
que leram aquele signal — isso é **reatividade granular**.

O modelo é **pull**: o consumidor **lê** o valor quando precisa (`count()`), e o framework
rastreia essa leitura pra saber a dependência. O valor não é "empurrado" no tempo como num
stream — ele está sempre disponível de forma síncrona.

O problema que resolvem é o do **change detection global via Zone.js**. Hoje (modo padrão),
o Zone.js faz *monkey-patch* de APIs assíncronas do browser (eventos, `setTimeout`, XHR/fetch,
Promises). Quando qualquer uma dispara, o Zone.js avisa o Angular, que **reverifica a árvore de
componentes inteira** (respeitando `OnPush`), porque ele **não sabe o que mudou** — só sabe que
*algo* aconteceu. Isso é caro e impreciso.

Signals invertem isso: como a leitura registra a dependência, o Angular sabe **cirurgicamente**
o que reavaliar/re-renderizar. É a base pro futuro **zoneless** (sem Zone.js).

```typescript
import { signal } from '@angular/core';

const count = signal(0);   // cria o signal
count();                   // LÊ o valor (chamando como função) → 0
count.set(1);              // escreve → consumidores que leram count() são notificados
```

**Pegadinha:** dizer que "Signal é igual a `BehaviorSubject`". Ambos têm um valor atual, mas
`BehaviorSubject` é **push/assíncrono** (você se inscreve e recebe emissões no tempo, e precisa
desinscrever); Signal é **pull/síncrono** e não tem subscription pra vazar.

**Como responder:** "Signal é um valor reativo que rastreia suas dependências na leitura. O
modelo é pull e síncrono. Ele existe pra permitir change detection granular — em vez de o
Zone.js reverificar a árvore toda porque *algo* mudou, o Angular sabe exatamente quem dependia
do signal que mudou. É o caminho pro zoneless."

---

## 2. signal(): criar, ler, set(), update(), imutabilidade

`signal(inicial)` retorna um **`WritableSignal<T>`**. Você **lê chamando como função** (`s()`),
e escreve com dois métodos:

- **`set(valor)`** — troca o valor inteiro.
- **`update(fn)`** — deriva o novo valor do atual: `s.update(v => v + 1)`.

Ler um signal **dentro de um contexto reativo** (`computed`, `effect`, ou o template) **registra
a dependência**. Ler fora desses contextos só devolve o valor, sem rastreamento.

A igualdade padrão é **`Object.is`**. Isso torna a **imutabilidade** essencial: se você **mutar
um objeto/array no lugar**, a referência não muda, `Object.is` dá `true` e **ninguém é
notificado**. Sempre crie uma **nova referência**.

```typescript
const user = signal({ nome: 'Ana', tags: ['a'] });

// ERRADO — muta no lugar, mesma referência, NÃO notifica:
user().tags.push('b');

// CERTO — nova referência:
user.update(u => ({ ...u, tags: [...u.tags, 'b'] }));

// dá pra customizar a igualdade:
const p = signal({ id: 1 }, { equal: (a, b) => a.id === b.id });
```

Obs.: o método `mutate()` foi **removido** justamente pra reforçar o modelo imutável — hoje se
usa `set`/`update` com nova referência.

**Pegadinha:** "por que meu `@for` não atualiza depois do `push`?" — porque a referência do array
não mudou; o signal não considera que houve mudança.

**Como responder:** "Leio chamando como função e escrevo com `set` ou `update`. A igualdade é
`Object.is`, então trato o valor como imutável: pra objeto/array eu crio uma nova referência com
spread, senão a mudança não é detectada."

---

## 3. computed(): sinais derivados, memoização, lazy, glitch-free

`computed(() => ...)` cria um **signal derivado, somente-leitura**, a partir de outros signals
lidos dentro da função. É a ferramenta pra **estado derivado**.

Propriedades-chave:

- **Memoizado:** só **recalcula** quando uma das dependências lidas **realmente muda** (`Object.is`).
  Leituras repetidas sem mudança devolvem o valor em cache.
- **Lazy:** só executa quando **alguém lê** o computed. Se ninguém consome (nem template, nem
  effect, nem outro computed), ele **nunca roda**.
- **Dependências dinâmicas:** as dependências são **as que foram lidas na última execução**. Se
  um `if` fez você ler `a` mas não `b`, mudar `b` não recalcula.
- **Glitch-free:** o Angular nunca expõe um estado intermediário inconsistente; ao ser lido, o
  valor já reflete todas as dependências de forma coerente (sem "piscar" valores errados).

```typescript
const preco = signal(100);
const qtd = signal(2);
const total = computed(() => preco() * qtd());  // derivado

total();       // 200 (calcula agora, na 1ª leitura)
qtd.set(3);
total();       // 300 (recalcula porque qtd mudou)
preco.set(100);
total();       // set pro MESMO valor → Object.is true → não recalcula
```

**Pegadinha:** achar que computed roda "sempre que uma dependência muda". Ele é **lazy**: só
recalcula quando muda **E** alguém lê. Outra pegadinha: colocar **efeito colateral** (log, HTTP)
dentro de computed — computed deve ser **puro**.

**Como responder:** "computed é um signal derivado, memoizado e lazy. Ele recalcula só quando uma
dependência lida muda e alguém consome o valor. É glitch-free, então nunca expõe estado
intermediário. Estado derivado sempre vai em computed, não em effect."

---

## 4. effect(): efeitos colaterais, cleanup, allowSignalWrites

`effect(() => ...)` roda a função sempre que qualquer signal lido dentro dela muda. Serve pra
**efeitos colaterais** — não pra derivar valor.

- **Quando roda:** uma vez ao ser criado, e depois de forma **agendada** (após a change
  detection), quando uma dependência muda. **Não** é síncrono a cada `set` — múltiplos sets no
  mesmo tick coalescem em uma execução.
- **Cleanup:** a função recebe um `onCleanup` pra registrar limpeza, executada **antes da próxima
  rodada** e no **destroy** — ideal pra `clearTimeout`, cancelar assinaturas, etc.
- **Escrita em signals:** por padrão um effect **não pode** escrever em signals (evita loops). Pra
  isso existe `allowSignalWrites`, mas precisar dele costuma ser **cheiro de design** — quase
  sempre o certo é `computed`.
- **Contexto:** normalmente é criado no construtor/campo (injection context), com cleanup
  automático no destroy.

```typescript
const query = signal('');

effect((onCleanup) => {
  const q = query();                 // dependência
  const id = setTimeout(() => console.log('buscar', q), 300);
  onCleanup(() => clearTimeout(id)); // roda antes da próxima e no destroy
});

// sincronizar com localStorage:
const tema = signal<'claro' | 'escuro'>('claro');
effect(() => localStorage.setItem('tema', tema()));
```

Casos legítimos: **log/analytics**, **sincronizar com `localStorage`**, integrar com APIs
**não-reativas** (canvas, biblioteca de chart, DOM de terceiro).

**Pegadinha:** usar `effect` pra **derivar estado** (`effect(() => this.total.set(a()*b()))`).
Isso duplica estado, arrisca loop e precisa de `allowSignalWrites` — o certo é
`total = computed(() => a()*b())`.

**Como responder:** "effect é pra efeito colateral reativo: log, sync com localStorage, integrar
com algo não-reativo. Roda ao criar e quando uma dependência muda, de forma agendada, e tem
cleanup via `onCleanup`. Nunca uso pra derivar estado — isso é computed; se preciso escrever
signal num effect (`allowSignalWrites`), geralmente errei o design."

---

## 5. Signals vs RxJS/Observables

Não é "um substitui o outro" — resolvem problemas diferentes.

| | **Signal** | **Observable (RxJS)** |
|---|---|---|
| Modelo | **Pull** (você lê) | **Push** (emite pra você) |
| Tempo | **Síncrono** — sempre tem "valor atual" | **Assíncrono / stream** no tempo |
| Bom pra | **Estado** de UI, valores derivados | Eventos, HTTP, debounce, retry, cancelamento |
| Operadores | Não tem (é só valor) | `switchMap`, `debounceTime`, `retry`… |
| Unsubscribe | Não existe (sem vazamento) | Precisa desinscrever (ou async pipe) |

Signal responde "**qual é o valor agora?**". Observable responde "**o que acontece ao longo do
tempo?**". Buscas com debounce, cancelamento de request anterior, WebSocket, coordenação de
múltiplos streams — isso é RxJS. Estado de tela (contador, filtro, item selecionado, derivados) —
isso é Signal.

**Interop** (os dois convivem):

```typescript
import { toSignal, toObservable } from '@angular/core/rxjs-interop';

// Observable → Signal (desinscreve sozinho no destroy):
readonly usuario = toSignal(this.http.get<User>('/api/me'), { initialValue: null });

// Signal → Observable (pra usar operadores):
readonly termo = signal('');
readonly resultados$ = toObservable(this.termo).pipe(
  debounceTime(300),
  switchMap(t => this.api.buscar(t))
);
```

E o **`async pipe`** continua sendo a melhor forma de consumir stream no template — ele inscreve e
desinscreve por você.

**Pegadinha:** dizer que "Signals vão matar o RxJS". Não — RxJS continua essencial pro que é
assíncrono/temporal. Outra: usar `toSignal` sem `initialValue` num stream que emite depois (o
signal fica `undefined` até a 1ª emissão).

**Como responder:** "Signal é pull e síncrono, ótimo pra estado; Observable é push e assíncrono,
ótimo pra streams e coordenação no tempo. Uso Signals pro estado da tela e RxJS pra HTTP, debounce
e cancelamento. Eles fazem interop com `toSignal`/`toObservable`. RxJS não vai embora."

---

## 6. Signals em componentes: inputs, outputs, model, zoneless

A partir da v17.1+, inputs/outputs também são baseados em signal:

```typescript
import { Component, input, output, model, computed } from '@angular/core';

@Component({
  selector: 'app-card',
  standalone: true,
  template: `
    <h3>{{ titulo() }}</h3>
    @if (temSubtitulo()) { <p>{{ subtitulo() }}</p> }
    <button (click)="fechar.emit()">x</button>
  `,
})
export class CardComponent {
  titulo = input.required<string>();          // input obrigatório, como signal
  subtitulo = input('');                       // input opcional com default
  temSubtitulo = computed(() => this.subtitulo().length > 0);  // derivado do input
  fechar = output<void>();                     // substitui @Output/EventEmitter
  aberto = model(true);                        // two-way: input + output ([(aberto)])
}
```

- **`input()`** cria input como **signal** (read-only no filho); `input.required<T>()` exige o
  valor. Reage a mudanças **sem `ngOnChanges`** — dá pra combinar com `computed`/`effect`.
- **`output()`** substitui `@Output()`/`EventEmitter` com API mais enxuta.
- **`model()`** é **two-way** (input + output juntos), pra usar com `[(x)]`.

**Zoneless:** `provideExperimentalZonelessChangeDetection()` liga o modo **sem Zone.js**. Sem o
patch global, o que dispara a atualização passa a ser a **mudança de signal** (mais alguns
gatilhos como eventos de template e `markForCheck`), não mais "qualquer coisa assíncrona".
Signals são o que torna zoneless viável, porque o framework sabe o que mudou.

**Relação com OnPush:** ler um signal no template **marca o componente pra checagem** quando ele
muda. Isso combina lindamente com `ChangeDetectionStrategy.OnPush` e reduz a necessidade de
`ChangeDetectorRef.markForCheck()` manual — o signal já sinaliza sozinho.

**Pegadinha:** achar que zoneless já é padrão/estável — hoje ainda é **experimental**
(`provideExperimental…`). E dizer que signal input "muda no filho": ele é **read-only** no filho.

**Como responder:** "Com signal inputs (`input()`/`input.required()`), `output()` e `model()`, o
componente fica reativo sem `ngOnChanges`. Signals marcam o componente pra checar quando mudam, o
que casa com OnPush e abre caminho pro zoneless (`provideExperimentalZonelessChangeDetection`),
onde a mudança de signal é o gatilho da atualização em vez do Zone.js."

---

## 7. Gerência de subscriptions com RxJS (por que ainda importa)

Mesmo com Signals, se você **inscreve** um Observable manualmente e **não desinscreve**, você
**vaza memória** (o callback segura referências e continua rodando após o componente sumir).

Formas de evitar (da melhor pra pior):

1. **`async pipe`** no template — inscreve e desinscreve automaticamente com o ciclo de vida.
2. **`takeUntilDestroyed()`** — operador que completa o stream quando o componente é destruído
   (usa o `DestroyRef`); sem precisar de `ngOnDestroy`.
3. **`takeUntil(destroy$)`** (padrão antigo) — um `Subject` emitido no `ngOnDestroy`.
4. **Guardar `Subscription` e chamar `unsubscribe()`** no `ngOnDestroy` (verboso, fácil esquecer).

```typescript
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

@Component({ /* ... */ })
export class BuscaComponent {
  constructor(private api: Api) {
    this.api.stream$
      .pipe(takeUntilDestroyed())   // completa no destroy — sem vazamento
      .subscribe(x => /* ... */);
  }
}
```

Detalhe: `HttpClient` **completa após 1 emissão**, então uma request pontual não vaza mesmo sem
desinscrever. O risco real é em **streams de vida longa** (WebSocket, `interval`, `fromEvent`,
`valueChanges`). E `toSignal`/`async pipe` cuidam do unsubscribe — é parte do apelo de consumir
reativo no template.

**Pegadinha:** dizer que "com Signals não preciso mais me preocupar com unsubscribe". Você ainda
usa RxJS pra HTTP/streams; se inscrever manualmente um stream de vida longa, precisa gerenciar.

**Como responder:** "Prefiro `async pipe` ou `takeUntilDestroyed`, que desinscrevem sozinhos.
Subscribe manual sem unsubscribe em stream de vida longa vaza memória. Request HTTP não vaza
porque completa, mas WebSocket/interval sim. Signals no template ajudam porque não têm
subscription, mas RxJS continua no jogo pro assíncrono."

---

## Glossário

- **Signal:** valor reativo que rastreia dependências na leitura. Pull, síncrono.
- **WritableSignal:** signal que aceita `set`/`update` (o que `signal()` retorna).
- **Pull vs Push:** pull = consumidor lê quando quer (Signal); push = fonte emite no tempo (Observable).
- **computed:** signal derivado, **memoizado**, **lazy**, **glitch-free**, somente-leitura.
- **effect:** efeito colateral reativo; roda ao criar e quando dependências mudam (agendado); tem `onCleanup`.
- **Memoização:** cache do resultado; só recalcula quando uma dependência muda.
- **Lazy:** só executa quando alguém lê (computed pode nunca rodar).
- **Glitch-free:** nunca expõe estado intermediário inconsistente.
- **allowSignalWrites:** flag que permite escrever signal dentro de effect (geralmente cheiro).
- **Zone.js:** lib que faz monkey-patch de APIs async pra disparar change detection global.
- **Zoneless:** modo sem Zone.js (`provideExperimentalZonelessChangeDetection`), disparado por signals.
- **toSignal / toObservable:** interop RxJS ↔ Signals.
- **async pipe:** consome Observable no template, com unsubscribe automático.
- **takeUntilDestroyed:** operador que completa o stream no destroy do componente.
- **input()/output()/model():** APIs de I/O de componente baseadas em signal (model = two-way).

## Checagem de entendimento

1. Explique com suas palavras a diferença entre reatividade **granular** (Signals) e change
   detection **global** (Zone.js).
2. Por que `array().push(x)` dentro de um signal não dispara atualização, e como corrigir?
3. O que significa dizer que `computed` é **lazy** e **memoizado**? Dê um caso em que ele nunca roda.
4. Quando você usaria `effect` e quando isso seria um erro? O que é `allowSignalWrites` e por que
   costuma indicar problema de design?
5. Dê dois cenários em que você escolheria **RxJS** mesmo com Signals disponíveis, e como faria a
   interop nesse componente.
6. O que é **zoneless**, como os Signals viabilizam esse modo, e qual a relação com `OnPush`?
