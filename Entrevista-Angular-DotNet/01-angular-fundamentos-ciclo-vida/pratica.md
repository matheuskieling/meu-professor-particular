# Prática — Simulação de entrevista (Módulo 01)

Banco de perguntas de entrevista sobre fundamentos e ciclo de vida do Angular, da mais comum à
pegadinha. O agente faz uma por vez, ouve a resposta do aluno e critica: o que faltou, o que foi
impreciso e como soar mais sênior. As respostas-modelo abaixo são o alvo — o aluno não precisa
recitá-las palavra por palavra, mas deve cobrir os pontos-chave.

---

### Pergunta 1 — Qual a diferença entre o constructor e o ngOnInit? Por que não colocar lógica pesada no constructor?

**Resposta-modelo:** O constructor é do JavaScript/TypeScript e roda quando o Angular instancia a
classe — nesse momento o único trabalho apropriado é injeção de dependência e init trivial de
campos. Os `@Input` **ainda não foram setados** no constructor. O `ngOnInit` é um hook do Angular
que roda depois de os inputs estarem preenchidos, então é onde vai a inicialização de verdade: HTTP,
setup de streams, uso de inputs. Não coloco lógica pesada no constructor porque (a) roda antes dos
inputs existirem e (b) acopla efeito colateral à construção do objeto, prejudicando testabilidade.

**Erros comuns:** Dizer que "tanto faz"; achar que os `@Input` já estão disponíveis no constructor;
não mencionar testabilidade nem a ordem inputs → ngOnInit.

---

### Pergunta 2 — O que é change detection no Angular?

**Resposta-modelo:** É o processo pelo qual o Angular mantém o DOM sincronizado com o estado dos
componentes. Depois de algo que pode ter mudado o estado, o Angular percorre a árvore de componentes
de cima pra baixo, reavalia as expressões dos bindings de cada componente e, se mudaram, atualiza o
DOM. Na estratégia padrão, ele checa todos os componentes a cada ciclo.

**Erros comuns:** Confundir com o Zone.js; dizer que o Angular "sabe exatamente o que mudou" (ele
reavalia e compara); não mencionar a árvore de componentes.

---

### Pergunta 3 — O que é o Zone.js e qual o papel dele?

**Resposta-modelo:** O Zone.js faz monkey-patch das APIs assíncronas do browser — eventos do DOM,
`setTimeout`, `Promise`, XHR. Assim, quando uma dessas tarefas async termina, ele avisa o Angular
que o estado pode ter mudado e que é hora de rodar a change detection. O ponto-chave: o Zone.js diz
*quando* rodar a CD; a change detection é que decide *o que* atualizar. São coisas separadas.

**Erros comuns:** Dizer que o Zone.js "faz a change detection"; não saber que ele patcha APIs async;
não separar "quando" (Zone) de "o quê" (CD).

---

### Pergunta 4 — Explique o ciclo de vida completo de um componente Angular, na ordem.

**Resposta-modelo:** A ordem é `ngOnChanges` → `ngOnInit` → `ngDoCheck` → `ngAfterContentInit` →
`ngAfterContentChecked` → `ngAfterViewInit` → `ngAfterViewChecked` → `ngOnDestroy`. O `ngOnChanges`
recebe o `SimpleChanges` e dispara antes do `ngOnInit` e a cada mudança de referência de input. O
`ngOnInit` é a inicialização, roda uma vez. Os hooks de *Content* dizem respeito ao conteúdo
projetado via `ng-content` (`@ContentChild` pronto no `ngAfterContentInit`); os de *View* ao
template do próprio componente (`@ViewChild` pronto no `ngAfterViewInit`). O `ngOnDestroy` é a
limpeza.

**Erros comuns:** Trocar a ordem de Content e View; achar que `@ViewChild` já existe no `ngOnInit`;
esquecer o `ngDoCheck`; não citar o `SimpleChanges`.

---

### Pergunta 5 — Qual a diferença entre ngAfterContentInit e ngAfterViewInit?

**Resposta-modelo:** *Content* é o conteúdo que o pai projeta dentro do componente via
`<ng-content>` — está pronto no `ngAfterContentInit`, e é aí que `@ContentChild` fica disponível.
*View* é o template do próprio componente e seus filhos — pronto no `ngAfterViewInit`, onde
`@ViewChild` fica disponível. Content vem "de fora" (do pai), View é "o que o componente renderiza".

**Erros comuns:** Inverter os dois; não distinguir conteúdo projetado de template próprio.

---

### Pergunta 6 — Quando você usaria ChangeDetectionStrategy.OnPush?

**Resposta-modelo:** Uso `OnPush` em componentes cujos dados chegam por `@Input` e que trabalham
com imutabilidade — componentes "de apresentação". Com `OnPush`, o Angular só checa o componente
quando muda a *referência* de um `@Input`, quando há um evento originado no componente, ou quando um
`async` pipe emite. Isso poda subárvores inteiras da checagem e melhora performance em apps grandes.
A contrapartida é disciplina de imutabilidade: pra atualizar preciso trocar a referência, não mutar
o objeto.

**Erros comuns:** Não citar os gatilhos; esquecer a exigência de imutabilidade; achar que `OnPush`
"desliga" a change detection de vez.

---

### Pergunta 7 — Com OnPush, por que às vezes a view não atualiza mesmo eu tendo mudado os dados?

**Resposta-modelo:** Porque provavelmente mutei o objeto/array sem trocar a referência —
`array.push(...)` ou `obj.prop = x` mantêm a mesma referência, e o `OnPush` compara `@Input` por
`===`, então não vê mudança. A correção é imutabilidade: `this.items = [...this.items, novo]`. Se
por algum motivo eu não puder trocar a referência, forço com `markForCheck()` no `ChangeDetectorRef`.

**Erros comuns:** Não perceber que é problema de referência; sugerir só `detectChanges` sem entender
a causa; não saber a alternativa imutável.

---

### Pergunta 8 — Qual a diferença entre markForCheck e detectChanges?

**Resposta-modelo:** `markForCheck()` marca o componente e seus ancestrais pra serem checados no
*próximo* ciclo de change detection — não checa na hora; é o que uso quando mudei estado fora de um
gatilho do `OnPush`. `detectChanges()` roda a checagem imediatamente, de forma síncrona, nesse
componente e nos filhos. Um agenda, o outro executa agora.

**Erros comuns:** Trocar os dois; dizer que `markForCheck` checa imediatamente.

---

### Pergunta 9 — Por que e como fazer unsubscribe no ngOnDestroy?

**Resposta-modelo:** Streams contínuos (eventos, `interval`, WebSocket, subjects compartilhados) que
eu subscrevo mantêm uma referência ao callback do componente. Se eu não faço unsubscribe ao destruir
o componente, a subscription continua viva — memory leak e, muitas vezes, lógica duplicada a cada
navegação. Hoje eu uso `takeUntilDestroyed()` (Angular 16+) ou o `DestroyRef` pra registrar a
limpeza; o padrão clássico é `takeUntil(destroy$)` com um `Subject` que eu emito no `ngOnDestroy`.
Além disso, também limpo `setInterval`/`setTimeout` e listeners manuais.

**Erros comuns:** Não saber a forma moderna (`takeUntilDestroyed`/`DestroyRef`); não citar timers e
listeners; achar que todo Observable precisa de unsubscribe.

---

### Pergunta 10 — Todo Observable precisa de unsubscribe? (pegadinha)

**Resposta-modelo:** Não. Observables que **completam** sozinhos após emitir — como as requisições
do `HttpClient` — não vazam, porque a subscription encerra sozinha. O risco são os streams
**contínuos** que nunca completam. E o `async` pipe faz o unsubscribe automaticamente ao destruir o
componente, então quando dá eu prefiro ele a subscrever na classe.

**Erros comuns:** Responder "sim, todo Observable precisa"; não saber que o HTTP completa; esquecer
que o `async` pipe resolve o unsubscribe.

---

### Pergunta 11 — O que é o erro ExpressionChangedAfterItHasBeenCheckedError e por que aparece? (pegadinha)

**Resposta-modelo:** É um erro que aparece só em modo de desenvolvimento, quando um valor usado num
binding muda *depois* de o Angular já ter checado aquela view no ciclo atual. O caso clássico é
alterar um binding dentro do `ngAfterViewInit`. O Angular faz uma segunda verificação em dev pra
garantir que a view ficou estável após a checagem; se o valor mudou, ele avisa. Resolvo movendo a
mudança pra antes (ex.: `ngOnInit`) ou adiando com `Promise.resolve().then(...)`/`setTimeout` pra
cair no próximo ciclo.

**Erros comuns:** Não saber que é só em dev; não relacionar com o timing dos hooks; "resolver"
suprimindo em vez de entender a causa.

---

### Pergunta 12 — O que muda num componente standalone em relação ao modelo com NgModule?

**Resposta-modelo:** Um componente standalone declara os próprios `imports` no `@Component` e não
precisa ser declarado num `NgModule`. Isso simplifica a árvore de dependências: cada componente é
autocontido, o que facilita lazy loading, tree-shaking e testes. No Angular 17/18 o standalone é o
caminho recomendado, com `bootstrapApplication` em vez de `NgModule` raiz, e casa bem com `inject()`
pra DI e o novo control flow `@if`/`@for`/`@switch`.

**Erros comuns:** Não saber o que vai em `imports`; achar que standalone "não tem DI"; não citar
`bootstrapApplication` nem os ganhos (lazy load, tree-shaking).
