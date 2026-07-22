# ☀️ RESUMO PARA AMANHÃ — revisão da manhã antes da entrevista (22/07, 18h)

> Consolidado de tudo o que treinamos hoje (3 sessões: simulado + 2 rodadas mistas).
> Organizado por tema. Leia uma vez de manhã. As **frases prontas** são o que falar em voz alta.

---

## ⚡ Antes de tudo — 3 coisas que te destacam
1. **Conte a história real:** "já tive esgotamento de pool de conexões porque o **DbContext estava Transient**; troquei pra **Scoped** e resolveu." (mostra experiência).
2. **Puxe você mesmo as nuances** antes do entrevistador: "o DbContext já é UoW+repositório", "async melhora throughput, não latência".
3. **Não escorregue nestas 4:**
   - value type **não** está "sempre na stack" (é semântica de cópia; campo/boxed vai pra heap).
   - `signal` muda no **`.set()`**, não ao ser lido (quem recalcula na leitura é o `computed`).
   - IL/JIT sempre existiram; o cross-platform veio da **CLR portada (CoreCLR)**.
   - `.Result` no ASP.NET **Core** não dá deadlock (não tem contexto) → é **starvation**.

---

## 🅰️ ANGULAR

### Ciclo de vida (ordem + papel)
`constructor` (só DI, `@Input` ainda `undefined`) → **`ngOnChanges`** (recebe `SimpleChanges`; roda antes do OnInit e a cada mudança de input) → **`ngOnInit`** (inputs prontos → **faz HTTP aqui**) → **`ngAfterViewInit`** (view/DOM pronta → **`@ViewChild` disponível aqui**) → **`ngOnDestroy`** (cleanup/unsubscribe).
> *"constructor é só DI e roda antes dos inputs; ngOnInit já tem os inputs, é onde inicializo/faço HTTP; @ViewChild só existe no ngAfterViewInit."*

### Change detection, Zone.js, OnPush
- **Zone.js** faz monkey-patch de APIs async pra avisar "re-verifica" (global, impreciso).
- **OnPush** só re-renderiza em: nova **referência** de `@Input`, evento local, `async` pipe, `markForCheck()`. `push()` muta sem trocar referência → **não atualiza**; corrige com `[...itens, x]` ou signals. Exige **imutabilidade**.
- **Zoneless**: tira o Zone.js; a CD continua, disparada por **signals/eventos/async pipe**.

### Signals
- `signal` = caixa de **estado** (muda no `.set/.update`, leitura síncrona = *pull*).
- `computed` = **deriva** estado (lazy + memoizado, recalcula na leitura).
- `effect` = **efeito colateral** (nunca pra derivar estado).
- **Signals vs Observable:** signal = valor síncrono atual (*pull*, estado); Observable = fluxo async ao longo do tempo (*push*, eventos). **Complementam, não substituem RxJS.**

### RxJS
- **Promise vs Observable:** Promise = 1 valor, eager, não cancelável. Observable = N valores, lazy, cancelável, com operadores.
- **Flattening:** `switchMap` cancela o anterior (**autocomplete**), `mergeMap` paralelo, `concatMap` fila em ordem, `exhaustMap` ignora novos.
- **Evitar leak de subscribe:** `async` pipe (auto) › `takeUntilDestroyed()` › `takeUntil`+Subject › unsubscribe manual. HttpClient completa sozinho.

### Router / DI / Interceptors
- **Lazy loading** = code splitting via `import()` dinâmico (`loadComponent`/`loadChildren`) → bundle inicial menor. Preloading opcional.
- **`CanActivate`** (ativa rota já casada) vs **`CanMatch`** (decide o match **antes de baixar o chunk** → melhor pra lazy). **Resolver** pré-carrega dados antes de ativar.
- **DI:** `inject()` e construtor resolvem no mesmo momento; `inject()` é mais flexível (guards/interceptors funcionais). `providedIn:'root'` = singleton global + tree-shakable.
- **HTTP Interceptor:** clona a request imutável (`req.clone({ setHeaders: { Authorization }})`), chama `next`. Serve auth, erro global, retry, logging.
- **`@for ... track`** = identidade do item → reusa DOM (obrigatório no 17+).
- **Standalone vs NgModules:** standalone declara deps via `imports`, sem módulo. Padrão no 17+.
- **`@defer`** = lazy loading no template (gatilhos viewport/interaction/idle; placeholder/loading/error).

---

## #️⃣ .NET

### Ecossistema, runtime
- **.NET Framework** (Windows, legado, 4.8 congelado) → **.NET Core** (reescrita cross-platform, open source) → **.NET 5+/8** (unificação, "Core" saiu, LTS). Migrar: Linux/containers, performance, features novas.
- **IL/JIT:** C# → **IL** (bytecode agnóstico) no build; **JIT** traduz pra nativo em runtime. AOT compila antes.

### Memória
- **Value vs reference:** value = semântica de **cópia** (struct/int); reference = **referência** (class/string/array). Passar struct = cópia; class = mesma referência (mutar afeta fora, reatribuir não sem `ref`).
- **Boxing:** value type embrulhado em `object` na heap (alocação + cópia) → pressão no GC em laços. Evita com **generics** (`List<int>`, não `ArrayList`).
- **GC gerações:** nascem na **Gen 0** (barata/frequente); sobreviventes → Gen 1 → **Gen 2** (rara). Coletar Gen 2 = full GC. **LOH** (≥~85KB) tratada como Gen 2, **não compactada**.
- **Memory leak:** GC coleta o **inalcançável**; leak = algo de vida longa segurando referência (evento sem `-=` #1, static, cache, captured dependency).

### IDisposable / recursos
- **Dispose** = liberação **determinística de RECURSO** (não memória). **`using`** = `try/finally`. **Finalizer** = não determinístico, tem custo (sobrevive 1 coleta extra), só rede de segurança → `GC.SuppressFinalize`; moderno = `SafeHandle`.
- **`IAsyncDisposable`/`await using`** quando a liberação faz I/O async.
- **HttpClient:** não `new`/dispose por request → `IHttpClientFactory`.

### DI, lifetimes, Repository
- **Transient** (nova a cada resolução) · **Scoped** (por request; **DbContext**) · **Singleton** (app inteira).
- **Captured dependency:** Scoped dentro de Singleton fura o lifetime (DbContext não thread-safe, nunca descartado). Validação de escopo lança. Solução: `IServiceScopeFactory`. Escada: **injeta pra baixo**.
- **Repository/UoW:** abstrai dados / coordena transação. O **DbContext já é UoW + repositórios** → usar só quando agrega (mock em testes, queries de domínio, trocar ORM).

### Async, escala, idempotência
- **async/await** libera a thread do pool no I/O → melhora **throughput/escalabilidade** (não a latência de 1 request). `async void` só em event handlers.
- **`.Result`/`.Wait()`:** deadlock no contexto (UI/ASP.NET clássico) / **starvation** no ASP.NET Core. `ConfigureAwait(false)`, async all the way.
- **Thread pool starvation:** threads bloqueadas drenam o pool (que cresce devagar) → enfileira → timeout.
- **Escalabilidade:** serviço **stateless** → escala horizontal; externalizar estado (Redis); load balancing, cache, filas.
- **Idempotência:** repetir = mesmo efeito. **Idempotency key** (gerada no clique; servidor guarda e não reprocessa). GET/PUT/DELETE idempotentes, **POST não**. Sistemas distribuídos = at-least-once → precisa de idempotência (exactly-once é mito).

### Extras C#
- **IEnumerable vs IQueryable:** IQueryable → expression tree → **SQL (filtro no banco)**; IEnumerable → **memória**. Ambos deferred. Perigo: virar IEnumerable cedo puxa a tabela toda.
- **record vs class:** record = **igualdade por valor**, imutável, `with`, ToString → DTOs/value objects. class = identidade + estado mutável.
- **`CancellationToken`:** cancelamento **cooperativo** (código precisa checar/repassar). Em ASP.NET Core vem do `RequestAborted`; passa pro `ToListAsync(ct)`.
- **abstract class vs interface:** abstract = estado + implementação, herança única (is-a). interface = contrato sem estado, múltipla (can-do). Interface pra compor vários contratos / DIP.

---

## ✅ Você já domina (entre confiante)
Idempotência · lifetimes DI (+história do DbContext) · async/escalabilidade · interceptors · computed vs effect · abstract vs interface · CancellationToken.

## 🎯 Reforçar de manhã (os que mais precisaram de ajuda)
Signals/computed · gerações do GC · boxing · OnPush/imutabilidade · lazy loading · .NET Framework vs Core · captured dependency · switchMap · standalone vs NgModules.

**Rotina sugerida:** ler este resumo 1x → reler só a seção "🎯 Reforçar" → respirar. Você está pronto. 🚀
