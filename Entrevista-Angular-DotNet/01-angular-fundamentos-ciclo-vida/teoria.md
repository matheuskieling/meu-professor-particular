# Módulo 01 — Angular: Fundamentos & Ciclo de Vida

Este módulo é o alicerce de qualquer entrevista de Angular. Ciclo de vida e change detection
aparecem em praticamente toda entrevista de nível pleno/sênior porque separam quem apenas *usa*
o framework de quem entende o **motor por dentro**. O entrevistador quase nunca quer a definição
decorada — quer o **porquê**: por que `ngOnInit` e não o constructor, por que `OnPush` é mais
rápido, por que um Observable esquecido vaza memória. Domine os "porquês" abaixo e você responde
com segurança de sênior.

Alvo: Angular 17+/18 — standalone components, novo control flow (`@if`/`@for`/`@switch`),
`inject()`, `DestroyRef`/`takeUntilDestroyed`.

---

## 1. Componente standalone: anatomia e constructor vs ngOnInit

Um componente é uma classe TypeScript decorada com `@Component`. A partir do Angular 17, o padrão
é **standalone** (`standalone: true` é o default no 19; nos 17/18 se declara explicitamente): o
componente traz seus próprios `imports` e dispensa `NgModule`.

```typescript
@Component({
  selector: 'app-user-card',
  standalone: true,
  imports: [CommonModule, RouterLink],   // o que o TEMPLATE usa
  template: `
    @if (user) {
      <h2>{{ user.name }}</h2>
    }
  `,
})
export class UserCardComponent implements OnInit {
  @Input() userId!: string;
  private readonly http = inject(HttpClient);   // DI moderna via inject()
  user?: User;

  constructor() {
    // Só DI e init trivial. NÃO acesse @Input aqui — ainda é undefined.
  }

  ngOnInit(): void {
    // Aqui os @Input já chegaram: lugar certo pra buscar dados.
    this.http.get<User>(`/api/users/${this.userId}`).subscribe(u => this.user = u);
  }
}
```

**Como o Angular renderiza:** ao encontrar o `selector` no template de um pai, o Angular (1)
instancia a classe resolvendo as dependências do constructor, (2) faz o binding dos `@Input`,
(3) chama os hooks de ciclo de vida (`ngOnChanges` → `ngOnInit` ...), (4) cria os nós no DOM e (5)
mantém a view sincronizada via change detection.

A diferença crucial: **no momento do constructor os `@Input` ainda não foram setados** — só existem
a partir do primeiro `ngOnChanges`/`ngOnInit`. Por isso o constructor serve só pra injeção de
dependência e inicialização trivial de campos; **qualquer lógica de inicialização de verdade
(HTTP, leitura de input, timers) vai no `ngOnInit`**.

**Pegadinha:** Fazer chamada HTTP ou lógica pesada no constructor. Além de rodar antes dos inputs
existirem, acopla o efeito colateral à *construção* do objeto, o que torna o componente difícil de
instanciar em testes e viola a expectativa de que o constructor só monta o objeto.

**Como responder:** "O constructor é pra injeção de dependência e init trivial; nesse momento os
`@Input` ainda são undefined. Coloco a inicialização de verdade — HTTP, timers, uso de input — no
`ngOnInit`, que roda depois do Angular preencher os inputs e deixa o componente testável."

---

## 2. Data binding e o essencial de @Input/@Output

Data binding é como o template e a classe conversam. São quatro formas:

| Sintaxe | Nome | Direção |
|---|---|---|
| `{{ valor }}` | Interpolação | classe → view |
| `[prop]="valor"` | Property binding | classe → view |
| `(evento)="handler()"` | Event binding | view → classe |
| `[(prop)]="valor"` | Two-way binding | classe ↔ view |

```typescript
// filho
@Component({ selector: 'app-child', standalone: true, template: `<button (click)="save()">Salvar</button>` })
export class ChildComponent {
  @Input() title = '';                       // pai → filho (entra dado)
  @Output() saved = new EventEmitter<void>(); // filho → pai (sai evento)
  save() { this.saved.emit(); }
}
```
```html
<!-- pai -->
<app-child [title]="pageTitle" (saved)="onSaved()"></app-child>
```

`@Input` **entra** dado no componente; `@Output` (um `EventEmitter`) **emite** evento pro pai. O
two-way `[(x)]` é só açúcar de `[x]` + `(xChange)` — por isso `[(ngModel)]` funciona.

O ponto que liga isso ao ciclo de vida: **toda mudança de referência num `@Input` dispara
`ngOnChanges`**, com um objeto `SimpleChanges` descrevendo o antes/depois. Na primeira vez,
`ngOnChanges` roda **antes** do `ngOnInit`.

**Pegadinha:** Achar que mutar o objeto passado no `@Input` dispara `ngOnChanges`. `ngOnChanges`
só reage a **troca de referência** do input — mutar propriedades internas do mesmo objeto não
dispara o hook.

**Como responder:** "`@Input` recebe dado do pai, `@Output` emite evento via `EventEmitter`.
Two-way é açúcar de property + event binding. Mudança de *referência* de um `@Input` dispara
`ngOnChanges` com o `SimpleChanges`, e na primeira vez ele roda antes do `ngOnInit`."

---

## 3. Change detection e o papel do Zone.js

**Change detection (CD)** é o processo pelo qual o Angular mantém o **DOM sincronizado com o
estado** do componente. Depois de algo que *pode* ter mudado o estado, o Angular percorre a
**árvore de componentes de cima pra baixo** (do root pras folhas), reavalia as expressões dos
bindings de cada componente e, se o valor mudou desde a última checagem, atualiza o DOM.

O que dispara um ciclo de CD? Basicamente **operações assíncronas**: eventos do DOM (click, input),
`setTimeout`/`setInterval`, `Promise`, chamadas HTTP (XHR). É aí que entra o **Zone.js**.

**Zone.js** faz *monkey-patch* dessas APIs assíncronas do browser — envolve `addEventListener`,
`setTimeout`, `Promise.then`, XHR etc. Assim, sempre que uma dessas tarefas async termina, o
Zone.js **avisa o Angular** "uma tarefa async completou, o estado pode ter mudado, rode a change
detection". O Angular então dispara um ciclo de CD na árvore inteira.

```typescript
// Ao clicar, o Zone.js intercepta o evento e, ao final do handler,
// aciona um ciclo de change detection automaticamente.
@Component({ standalone: true, template: `<button (click)="count++">{{ count }}</button>` })
export class CounterComponent { count = 0; }
```

Dois papéis distintos, e o entrevistador adora essa separação:
- **Zone.js diz QUANDO** rodar a CD (detecta que algo async aconteceu).
- **Change detection diz O QUE** atualizar (compara bindings e mexe no DOM).

Com a estratégia padrão (`Default`, também chamada `CheckAlways`), o Angular checa **todos** os
componentes da árvore a cada ciclo — daí a importância do `OnPush`.

**Pegadinha:** Dizer que "o Zone.js faz a change detection". Não: o Zone.js só *notifica*. E
também: mudar estado **fora** da zona do Angular (ex.: `ngZone.runOutsideAngular` ou um callback
não patchado) **não** dispara CD, e a view não atualiza.

**Como responder:** "Change detection é o Angular sincronizando o DOM com o estado, percorrendo a
árvore de componentes de cima pra baixo. O Zone.js faz monkey-patch das APIs async e avisa o
Angular quando *rodar* essa checagem — Zone.js diz *quando*, a change detection diz *o quê*."

---

## 4. ChangeDetectionStrategy.OnPush

Por padrão o Angular checa todo componente a cada ciclo. Com `changeDetection:
ChangeDetectionStrategy.OnPush`, o componente é **pulado** na checagem, exceto quando um destes
gatilhos ocorre:

1. **Mudança de referência** de um `@Input` (comparação por `===`, não por conteúdo).
2. Um **evento originado no próprio componente** (ou num filho) — click, input etc.
3. Um **`async` pipe** no template emite um novo valor.
4. Chamada manual de `markForCheck()` / `detectChanges()`.

```typescript
@Component({
  selector: 'app-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `@for (item of items; track item.id) { <li>{{ item.name }}</li> }`,
})
export class ListComponent {
  @Input() items: Item[] = [];
}
```

Isso **exige imutabilidade**: pra atualizar a view, você troca a **referência** do input, não muta
o objeto/array existente.

```typescript
// ERRADO com OnPush: mesma referência, a view não atualiza
this.items.push(novoItem);

// CERTO: nova referência, dispara o gatilho de @Input
this.items = [...this.items, novoItem];
```

**Ganho de performance:** ao marcar componentes "estáveis" como `OnPush`, o Angular **poda
subárvores inteiras** da checagem, reduzindo drasticamente o trabalho por ciclo em apps grandes.

**`markForCheck` vs `detectChanges`:**
- `ChangeDetectorRef.markForCheck()` — **marca** o componente (e ancestrais) pra serem checados no
  **próximo** ciclo de CD. Não checa agora; é o que você usa quando mudou estado fora de um dos
  gatilhos (ex.: dentro de um callback não rastreado).
- `ChangeDetectorRef.detectChanges()` — **roda a checagem imediatamente** nesse componente e nos
  filhos, de forma síncrona.

**Pegadinha:** Com `OnPush`, `array.push()` / `obj.prop = x` não atualizam a view — falta trocar a
referência. E confundir `markForCheck` (agenda pro próximo ciclo) com `detectChanges` (executa
agora).

**Como responder:** "`OnPush` faz o componente ser checado só quando muda a *referência* de um
`@Input`, quando há evento no componente, ou quando um `async` pipe emite. Por isso trabalho com
imutabilidade. Se preciso forçar, uso `markForCheck` pra agendar a checagem no próximo ciclo ou
`detectChanges` pra rodar na hora."

---

## 5. Ciclo de vida completo na ordem certa

O Angular chama os hooks nesta ordem:

| # | Hook | Quando dispara | O que fazer nele |
|---|---|---|---|
| 1 | `ngOnChanges(changes: SimpleChanges)` | Antes do `ngOnInit` e **a cada mudança de referência** de `@Input` | Reagir a mudança de input |
| 2 | `ngOnInit()` | Uma vez, após o 1º `ngOnChanges` | Inicialização (HTTP, setup) |
| 3 | `ngDoCheck()` | A **cada** ciclo de CD | Detecção customizada de mudança (usar com parcimônia) |
| 4 | `ngAfterContentInit()` | Uma vez, após projetar o **conteúdo** (`ng-content`) | Usar `@ContentChild` |
| 5 | `ngAfterContentChecked()` | Após cada checagem do conteúdo projetado | Reagir a mudança no conteúdo |
| 6 | `ngAfterViewInit()` | Uma vez, após criar a **view** do componente e filhos | Usar `@ViewChild`, medir/DOM |
| 7 | `ngAfterViewChecked()` | Após cada checagem da view | Reagir a mudança na view |
| 8 | `ngOnDestroy()` | Uma vez, ao destruir o componente | Limpeza (unsubscribe, timers) |

`ngOnChanges` recebe um `SimpleChanges`, um mapa `nomeDoInput → SimpleChange` com
`previousValue`, `currentValue` e `firstChange`:

```typescript
ngOnChanges(changes: SimpleChanges): void {
  if (changes['userId'] && !changes['userId'].firstChange) {
    this.reload(changes['userId'].currentValue);
  }
}
```

**Content vs View** (fonte de confusão em entrevista):
- **Content** = o que o **pai projeta** dentro do componente via `<ng-content>` — pronto no
  `ngAfterContentInit`, e é aí que `@ContentChild` fica disponível.
- **View** = o **template do próprio** componente e seus filhos — pronto no `ngAfterViewInit`, onde
  `@ViewChild` fica disponível.

```typescript
@ViewChild('input') inputRef!: ElementRef;

ngOnInit() { console.log(this.inputRef); }        // undefined — view ainda não existe
ngAfterViewInit() { this.inputRef.nativeElement.focus(); } // ok, disponível aqui
```

**Pegadinha:**
- Ler `@ViewChild` no `ngOnInit` → vem `undefined` (só existe a partir do `ngAfterViewInit`).
- **Alterar um binding dentro do `ngAfterViewInit`** → em dev, dá
  `ExpressionChangedAfterItHasBeenCheckedError`, porque o valor mudou depois de a view já ter sido
  checada. Solução: adiar (`setTimeout`/`Promise.resolve`) ou repensar onde o valor é setado.

**Como responder:** "A ordem é `ngOnChanges` → `ngOnInit` → `ngDoCheck` → `ngAfterContentInit` →
`ngAfterContentChecked` → `ngAfterViewInit` → `ngAfterViewChecked` → `ngOnDestroy`. `@ContentChild`
está pronto no `ngAfterContentInit` e `@ViewChild` no `ngAfterViewInit`. `ngOnChanges` traz o
`SimpleChanges` com previous/current e dispara antes do `ngOnInit`."

---

## 6. ngOnDestroy e vazamento de memória

`ngOnDestroy` roda **uma vez, quando o componente é destruído** (ex.: navegação, `@if` que fecha,
item removido de uma lista). É o lugar de limpar tudo que **sobreviveria** ao componente e o
manteria vivo na memória.

O leak clássico: **um Observable de vida longa sem unsubscribe**. A subscription mantém uma
referência ao callback do componente destruído; o garbage collector não recolhe, e a cada
navegação você acumula listeners que ainda reagem — vazamento e, muitas vezes, comportamento
duplicado.

**Formas de resolver (da mais moderna à clássica):**

```typescript
// 1. takeUntilDestroyed — Angular 16+ (mais idiomático)
export class LiveComponent {
  private readonly svc = inject(DataService);
  constructor() {
    this.svc.stream$
      .pipe(takeUntilDestroyed())   // no field initializer/constructor, pega o DestroyRef via inject
      .subscribe(v => this.handle(v));
  }
}

// 2. DestroyRef explícito
export class TimerComponent {
  private readonly destroyRef = inject(DestroyRef);
  ngOnInit() {
    const id = setInterval(() => this.tick(), 1000);
    this.destroyRef.onDestroy(() => clearInterval(id));
  }
}

// 3. Padrão clássico takeUntil + Subject
export class LegacyComponent implements OnDestroy {
  private destroy$ = new Subject<void>();
  ngOnInit() { this.svc.stream$.pipe(takeUntil(this.destroy$)).subscribe(); }
  ngOnDestroy() { this.destroy$.next(); this.destroy$.complete(); }
}
```

**O `async` pipe faz unsubscribe automático** ao destruir o componente — sempre que der, prefira
`{{ data$ | async }}` a subscrever na classe.

Além de Observables, também limpar no `ngOnDestroy`: `setInterval`/`setTimeout`,
`addEventListener` manual (`removeEventListener`), conexões WebSocket, e qualquer callback
registrado fora do Angular.

**Pegadinha:** Achar que **todo** Observable precisa de unsubscribe. HTTP do `HttpClient`
**completa** sozinho após emitir, então não vaza — o risco são streams **contínuos** (eventos,
`interval`, WebSocket, subjects compartilhados). E esquecer que o `async` pipe já resolve o
unsubscribe.

**Como responder:** "No `ngOnDestroy` limpo o que sobrevive ao componente: unsubscribe de streams
contínuos, `clearInterval`, `removeEventListener`. Hoje uso `takeUntilDestroyed` ou o `DestroyRef`;
o padrão antigo é `takeUntil` com um `Subject`. Streams que completam sozinhos, como HTTP, e o
`async` pipe não precisam de unsubscribe manual."

---

## Glossário

- **Standalone component** — componente que declara os próprios `imports` e dispensa `NgModule`.
- **Data binding** — sincronização entre classe e template (interpolação, property, event, two-way).
- **@Input / @Output** — entrada de dado / saída de evento (`EventEmitter`) entre pai e filho.
- **Change detection** — processo que sincroniza o DOM com o estado, percorrendo a árvore de componentes.
- **Zone.js** — biblioteca que faz monkey-patch de APIs async e avisa o Angular quando rodar a CD.
- **ChangeDetectionStrategy.OnPush** — estratégia que só checa o componente sob gatilhos específicos.
- **markForCheck** — marca o componente pra checagem no próximo ciclo de CD.
- **detectChanges** — força a checagem de CD imediatamente.
- **SimpleChanges** — objeto passado ao `ngOnChanges` com previousValue/currentValue/firstChange.
- **@ViewChild / @ContentChild** — referência a elemento da view / do conteúdo projetado.
- **DestroyRef / takeUntilDestroyed** — mecanismos modernos (Angular 16+) de limpeza no destroy.
- **Memory leak** — recurso (subscription, timer) que não é liberado e mantém objetos vivos na memória.

## Checagem de entendimento

1. Por que HTTP no constructor é um problema, e onde essa lógica deveria ficar?
2. Qual a diferença entre o papel do Zone.js e o da change detection?
3. Quais são os gatilhos que fazem um componente `OnPush` ser checado, e por que ele exige imutabilidade?
4. Diga a ordem completa dos 8 hooks de ciclo de vida e em qual deles `@ViewChild` já está disponível.
5. Qual a diferença entre `markForCheck` e `detectChanges`?
6. Quando um Observable precisa de unsubscribe e quando não precisa? Cite a forma moderna de fazê-lo.
