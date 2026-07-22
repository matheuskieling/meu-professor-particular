# 🎯 REVISAR antes da entrevista — diagnóstico do simulado

Resultado honesto do 1º simulado (não o 20/20 do motor — o que você **sabia de fato**).

> ✅ **RE-DRILL FEITO: os 10 tópicos 🔴 abaixo foram TODOS reperguntados e acertados na 2ª passada.**
> Considerar fixados. Resíduos de vocabulário a não escorregar na entrevista:
> - O padrão de injetar Scoped no Singleton chama-se **"captured dependency"**.
> - Um `signal` muda só no `.set()`/`.update()` — **ler não altera**; quem recalcula na leitura é o `computed`.
> - IL/JIT sempre existiram (até no Framework Windows-only); o **cross-platform veio da CLR (CoreCLR) portada** pra Linux/macOS, não do IL sozinho.
> - LOH ≥ ~85 KB e **não é compactada** por padrão.

## 🔴 Não sabia no 1º simulado → ✅ fixado no re-drill

**1. Signal vs Observable**
> Signal é um valor síncrono sempre disponível (modelo *pull*), ideal pra estado. Observable é um fluxo assíncrono de eventos ao longo do tempo (*push*), ideal pra async/composição (HTTP, eventos). Se complementam: `toSignal()` / `toObservable()`. Signals NÃO substituem o RxJS.

**2. Gerações do GC**
> Objetos nascem na Gen 0. Como a maioria morre jovem, o GC coleta Gen 0 com frequência e barato; sobreviventes sobem pra Gen 1 e Gen 2 (raramente coletada). Evita varrer o heap inteiro toda hora. Coletar Gen 2 = full GC (coleta 0,1,2). Objetos grandes (~85KB+) vão pra LOH, tratada como Gen 2 e não compactada.

**3. Captured dependency**
> Injetar Scoped num Singleton: o Singleton segura a instância Scoped pra sempre, furando o ciclo de vida — perigoso com DbContext (não é thread-safe e nunca seria descartado). O ASP.NET Core detecta na validação de escopo e lança erro. Solução: injetar `IServiceScopeFactory` e criar um scope sob demanda. Regra da escada: só injeta pra baixo (Singleton→Singleton; Scoped→Scoped/Singleton; Transient→qualquer).

**4. IL / JIT**
> C# compila pra IL (bytecode independente de plataforma); em runtime, o JIT da CLR traduz esse IL pra código nativo da CPU, método a método. Por isso a mesma DLL roda em qualquer OS. (AOT compila antes; CLR = Common Language Runtime.)

**5. OnPush + imutabilidade**
> OnPush só re-renderiza em: nova REFERÊNCIA de @Input, evento local, async pipe, ou markForCheck(). `push()` muta sem trocar a referência → não dispara. Corrijo criando novo array (`[...itens, x]`) ou usando signals.

**6. Lazy loading**
> Divide o bundle em chunks carregados sob demanda via `import()` dinâmico no `loadComponent`/`loadChildren`. Reduz o bundle inicial → app carrega mais rápido; o código da rota só é baixado ao navegar. Combina com `CanMatch` (barra antes de baixar o chunk) e preloading.

**7. Memory leak em .NET**
> O GC coleta o inalcançável. Leak clássico = algo de vida longa (event handler não desinscrito `+=` sem `-=`, static, cache sem limite, captured dependency) segurando referência a objetos que já deveriam morrer, impedindo a coleta. Nº 1: eventos não desinscritos.

**8. .NET Framework vs Core vs .NET 8**
> Framework (até 4.8) = Windows-only, legado, congelado. Core = reescrita cross-platform e open source. Do .NET 5 em diante unificou sob o nome ".NET" — .NET 8 é a LTS atual. Migra-se por Linux/containers, performance e porque o Framework não recebe features novas.

**9. Boxing**
> Empacotar um value type (int, struct) dentro de um `object` na heap — envolve alocação e cópia. Custa por pressão no GC, especialmente em laços. Evita-se com generics (`List<int>` em vez de `ArrayList`).

**10. Zoneless**
> Remove o Zone.js (que via monkey-patch avisava QUANDO rodar a change detection). A change detection continua — passa a ser acionada de forma precisa por signals, eventos e async pipe. Dá bundle menor e mais performance. Signals é o que torna isso viável.

## 🟡 Acertou, mas ajustar o raciocínio
- **Repository**: o DbContext do EF Core já é UoW + repositórios → envolver pode ser redundante. Use quando agrega valor (testes, queries de domínio, trocar ORM).
- **Dispose**: libera **recurso** (handle/conexão), NÃO a memória (memória é do GC). `using` = try/finally. `GC.SuppressFinalize` no Dispose.
- **constructor vs ngOnInit**: constructor = só DI, @Input ainda não chegou. ngOnInit = inputs prontos, faz HTTP aqui. A view/DOM só existe no ngAfterViewInit (NÃO no ngOnInit).
- **IAsyncDisposable**: quando a liberação faz I/O assíncrono (flush de stream). `await using`. Complementa, não substitui IDisposable.
- **Resolver**: pré-carrega dados ANTES da rota ativar (componente nasce com dados prontos). Guard = "pode entrar?"; resolver = "busca os dados".

## 📌 Sessão 2 (re-drill + mistura) — novos pontos a fixar

**async void** (🔴 novo) — retorna nada, não dá pra `await` nem capturar exceção (falha derruba o processo). Só aceitável em **event handlers** (assinatura exige void). Resto: sempre `async Task`.

**CanActivate vs CanMatch** (🔴 novo) — CanActivate decide se ativa a rota já casada (chunk pode já ter baixado). **CanMatch** decide se a rota **casa**, roda **antes de baixar o chunk lazy** → melhor pra lazy loading (barra sem baixar código, permite fallback no mesmo path).

**StringBuilder** (🟡) — string é imutável → concatenar em laço cria N strings novas (pressão no GC). StringBuilder é buffer mutável (`.Append`), materializa no `.ToString()`. Use em laços/muitas concatenações.

**inject() vs construtor** (🟡) — NÃO é lazy vs eager; resolvem no mesmo momento. `inject()` é mais flexível: funciona fora de construtores (guards/interceptors funcionais). `providedIn:'root'` = singleton global + tree-shakable.

**Deadlock do .Result** (🟡) — bloqueia a thread; em contexto com SynchronizationContext (UI, ASP.NET clássico) a continuation precisa da thread travada → deadlock. **ASP.NET Core não tem esse contexto → não é deadlock, é thread pool starvation.** `ConfigureAwait(false)` ou async all the way.

**Promise vs Observable** (🟢) — Promise: 1 valor, eager, não cancelável. Observable: N valores no tempo, lazy, cancelável, com operadores.

**value vs reference** (🟢, precisão) — o que define value type é a **semântica de cópia**, NÃO "ficar na stack" (campo de classe/boxed vai pra heap). Passar struct = cópia; class = mesma referência (mutar afeta fora; reatribuir não, sem `ref`).

## 🟢 Já domina (confie)
- Idempotência (com idempotency key; GET/PUT/DELETE idempotentes, POST não; at-least-once + idempotência > exactly-once).
- Lifetimes DI (+ a história real: DbContext Transient estourou conexões → Scoped resolveu). **CONTE ESSA HISTÓRIA NA ENTREVISTA.**
- async/await melhora **throughput/escalabilidade** (thread volta ao pool no I/O), não a latência de 1 request. Bloquear com `.Result` = thread pool starvation.
- HTTP Interceptor (clona a request imutável, adiciona header; serve auth, erro, retry, logging).
- computed (deriva estado, lazy+memoizado) vs effect (efeito colateral; nunca pra derivar estado).
