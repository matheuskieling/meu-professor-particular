# Módulo 07 — .NET: Async, Escalabilidade & Idempotência

Este é o fecho da trilha .NET. Aqui estão três dos temas de backend que **mais separam pleno de
sênior** numa entrevista: entender `async/await` **por dentro** (não só usar `await`), saber
**escalar uma API** (a pergunta de arquitetura clássica), e garantir **idempotência** (o que salva o
sistema quando a rede repete requests). O fio condutor: **async não deixa uma request mais rápida —
deixa o servidor mais escalável**; e num mundo distribuído, retries são inevitáveis, então suas
operações precisam ser **seguras de repetir**.

O entrevistador cobra esses temas porque eles revelam se você entende o que acontece embaixo do
`await`: thread pool, throughput, o que é `Task`, por que `.Result` trava, por que `POST` não é
idempotente. Responda ligando **causa → efeito** (o "porquê"), não repetindo definição de manual.

---

## 1. async/await e Task: o que async realmente faz

**Máquina de estados.** Quando você marca um método com `async`, o compilador C# o reescreve como uma
**máquina de estados**. Cada `await` vira um ponto onde o método pode **pausar** (retornando o
controle a quem chamou) e **retomar** depois, quando a operação aguardada terminar. Não há mágica de
threads escondida — é reescrita de código pelo compilador.

**`Task` não é `Thread`.** Uma `Task` representa uma **operação assíncrona em andamento** — uma
promessa de que um resultado vai existir no futuro. Ela **não é uma thread** e, no caso típico de
I/O, **não cria nenhuma thread** para esperar. `Thread` é um recurso do SO (caro de criar); `Task` é
uma abstração de "trabalho em andamento" que pode ou não usar uma thread.

**Async ≠ paralelismo.** Por padrão, um método `async` roda em **uma única thread**. `await` **libera
a thread durante a espera** — não executa dois trechos de código ao mesmo tempo. Paralelismo (rodar
coisas de fato simultâneas em vários núcleos) é `Task.Run` / `Parallel` / `Task.WhenAll` com trabalho
CPU. Async é sobre **não bloquear**, não sobre **fazer mais coisas ao mesmo tempo**.

**O benefício real é throughput/escalabilidade, não latência.** Uma request async **não fica mais
rápida** — ela leva o mesmo tempo (o banco responde no mesmo tempo). O que muda é que, **durante o
`await` de I/O, a thread volta para o thread pool e atende outra request**. Com as mesmas N threads, o
servidor aguenta **muito mais requests concorrentes**. Async é um multiplicador de **throughput**
(requests/segundo), não de **velocidade de uma request**.

```csharp
// I/O bound: async liberando a thread durante a espera do banco.
public async Task<Order?> GetOrderAsync(int id)
{
    // Enquanto o banco responde, ESTA thread volta pro pool e serve outra request.
    // Nenhuma thread fica bloqueada esperando o disco/rede.
    Order? order = await _dbContext.Orders.FindAsync(id);
    return order;
}
```

**Pegadinha:** "async deixa meu código mais rápido." Não. Uma request async não fica mais rápida — o
I/O leva o mesmo tempo. O ganho é o servidor **não segurar threads paradas**, então ele **escala**
(atende mais gente com o mesmo hardware).

**Como responder:** "Async não é paralelismo nem deixa a request mais rápida. `Task` é uma operação
em andamento, não uma thread. O compilador vira o método numa máquina de estados; no `await` de I/O a
thread é liberada de volta pro pool e serve outra request. Por isso async melhora **throughput e
escalabilidade** — o servidor atende mais requests concorrentes com as mesmas threads — mas a latência
de uma request individual não muda."

---

## 2. Thread pool, I/O bound vs CPU bound

**Thread pool.** Criar uma thread do SO é caro (memória de stack, agendamento). O runtime mantém um
**pool** de threads reutilizáveis: quando precisa executar trabalho, pega uma thread emprestada e a
devolve ao terminar. ASP.NET Core atende cada request numa thread do pool.

**I/O bound vs CPU bound — a distinção que a entrevista adora.**

- **I/O bound:** o gargalo é **esperar** por algo externo — rede, disco, banco, API. A CPU fica ociosa
  esperando. **Aqui async brilha:** durante a espera, a thread é liberada em vez de ficar bloqueada.
- **CPU bound:** o gargalo é **cálculo** que ocupa o processador (hash, compressão, processamento de
  imagem). **Async puro NÃO ajuda** — não há "espera" para liberar a thread; o trabalho precisa da
  CPU. Para paralelizar, aí sim `Task.Run` / `Parallel` para usar **vários núcleos**.

**Regra prática:** I/O bound → `async/await` sobre APIs async nativas (`FindAsync`, `HttpClient`
async). CPU bound → `Task.Run` (para tirar do thread da request) ou paralelismo. **Não** envolva I/O
async em `Task.Run` "pra deixar async": você já não usa thread durante o I/O; o `Task.Run` só
**desperdiça** uma thread do pool.

**Thread pool starvation (esgotamento do pool).** Se o código **bloqueia** threads — chamando
`.Result`/`.Wait()` em algo async (sync-over-async), ou fazendo I/O síncrono em muitas requests — as
threads do pool ficam **presas esperando**. O pool tenta criar novas threads, mas devagar (injeção
gradual), então requests novas ficam **na fila**, a latência dispara e a app parece "travada" sob
carga. É um dos motivos de "async all the way": **uma** chamada bloqueante no caminho já pode esgotar
o pool sob carga.

```csharp
// CPU bound: aqui sim faz sentido tirar do thread da request com Task.Run.
public async Task<string> HashSenhaAsync(string senha)
{
    // Trabalho pesado de CPU — não é I/O; async por si só não ajudaria.
    return await Task.Run(() => BCryptCaro(senha));
}
```

**Pegadinha:** envolver `await` de I/O em `Task.Run` ("pra tornar async") **não escala** — você tirou
uma thread do pool sem necessidade. I/O async **não usa thread** durante a espera; `Task.Run` reintroduz
o desperdício que você queria evitar.

**Como responder:** "I/O bound é esperar por rede/disco/banco — a CPU fica ociosa; aí async ajuda,
porque libera a thread durante a espera. CPU bound é cálculo puro — async não ajuda, aí é `Task.Run`
ou paralelismo pra usar mais núcleos. E cuidado com thread pool starvation: código que bloqueia thread
(tipo `.Result`) esgota o pool, as requests entram em fila e a latência explode."

---

## 3. Armadilhas: deadlock, async void, ConfigureAwait, "async all the way"

**Deadlock com `.Result`/`.Wait()` (sync-over-async).** É o clássico. Em ambientes com
`SynchronizationContext` (UI WinForms/WPF, ASP.NET **clássico**), o `await` por padrão tenta
**retomar no mesmo contexto** (thread de UI / thread da request). Se você **bloqueia** essa thread com
`.Result` ou `.Wait()` esperando a `Task`, essa mesma thread é a que o `await` precisa para continuar —
e ela está travada esperando a si mesma. **Deadlock.**

```csharp
// ⚠️ DEADLOCK em ASP.NET clássico / UI: NÃO faça isso.
public IActionResult Get()
{
    // .Result bloqueia a thread do contexto; o await lá dentro quer voltar
    // pra essa MESMA thread pra continuar -> ela está travada -> deadlock.
    var data = BuscarAsync().Result;
    return Ok(data);
}

// ✅ Correto: async all the way — nunca bloqueie.
public async Task<IActionResult> Get()
{
    var data = await BuscarAsync();
    return Ok(data);
}
```

> Nota .NET 8 / ASP.NET Core: o ASP.NET **Core** **não tem** `SynchronizationContext`, então esse
> deadlock específico não acontece nele. Mesmo assim, `.Result`/`.Wait()` continua ruim (thread pool
> starvation, exceções embrulhadas em `AggregateException`). A regra segue: **nunca** bloqueie.

**`async void`.** Um método `async void` é **fire-and-forget**: quem chama não pode `await`, não sabe
quando termina, e **exceções não são capturáveis** por `try/catch` de quem chamou (sobem como exceção
não tratada e podem derrubar o processo). Use `async void` **apenas em event handlers** (a assinatura
do evento exige `void`). Em qualquer outra situação, use **`async Task`** — assim dá pra `await`,
propagar exceção e testar.

**`ConfigureAwait(false)` e o `SynchronizationContext`.** O `SynchronizationContext` é o "contexto"
para onde o `await` tenta **voltar** após a operação (a thread de UI, a request do ASP.NET clássico).
`ConfigureAwait(false)` diz: **"não preciso voltar ao contexto original"** — retome em qualquer thread
do pool. Isso (a) evita o deadlock acima e (b) é mais eficiente. Era **essencial em bibliotecas** e no
ASP.NET clássico. Em **ASP.NET Core** importa menos (não há contexto pra voltar), mas ainda é boa
prática em código de biblioteca reutilizável.

**"Async all the way".** Se um método é async, **quem chama também deve ser async e usar `await`** — a
assincronia sobe por toda a pilha. Misturar `await` com `.Result`/`.Wait()` no meio do caminho é o que
causa deadlock e starvation. Não há meio-termo: ou é async ponta a ponta, ou você reintroduz bloqueio.

**Pegadinha:** "`ConfigureAwait(false)` resolve o deadlock." Ele **evita**, mas a cura de verdade é
**não bloquear** (nunca `.Result`/`.Wait`). E em ASP.NET Core nem há `SynchronizationContext` pra
deadlockar desse jeito — o problema ali vira starvation, não deadlock.

**Como responder:** "O deadlock do `.Result` é sync-over-async: em contexto com
`SynchronizationContext`, o `await` quer voltar pra thread que você bloqueou esperando a Task — ela
trava esperando a si mesma. A cura é async all the way, nunca bloquear. `async void` só em event
handler, porque engole exceção e não dá pra await. `ConfigureAwait(false)` diz 'não preciso voltar ao
contexto' — importa em biblioteca e no ASP.NET clássico; no Core, menos, porque não há contexto."

---

## 4. Escalabilidade — conceitos: vertical vs horizontal e stateless

**Escala vertical (scale up).** Colocar uma **máquina maior** — mais CPU, mais RAM. É simples (não
muda a arquitetura), mas tem **teto físico** (não existe máquina infinita), custa caro no topo e
continua sendo **um único ponto de falha** (se cair, cai tudo).

**Escala horizontal (scale out).** Colocar **mais instâncias** do serviço atrás de um **load
balancer**. É **elástica** (adiciona/remove conforme a demanda) e **resiliente** (uma instância cai, o
resto continua). É a forma como sistemas web modernos escalam — mas exige que o serviço seja
**stateless**.

**Stateless — o pré-requisito da escala horizontal.** Um serviço **stateless** **não guarda estado de
sessão na memória local do processo**. Cada request carrega o que precisa (token, ids) e **qualquer
instância consegue atender qualquer request**. É isso que permite ao load balancer mandar a próxima
request pra qualquer instância — e adicionar/remover instâncias livremente.

**Externalizar o estado.** O estado que precisa persistir entre requests (sessão, carrinho, cache)
vai para um **store compartilhado**: um **cache distribuído** (Redis), um **session store**, ou o
banco. Assim todas as instâncias enxergam o mesmo estado, e nenhuma "é dona" de um usuário.

**Sticky sessions (afinidade de sessão) = anti-pattern.** Configurar o load balancer para sempre
mandar o mesmo usuário para a **mesma** instância (porque o estado dele mora lá) é um **anti-pattern
de escala**: quebra o balanceamento (uma instância pode ficar sobrecarregada), impede escalar/reduzir
tranquilamente, e se aquela instância cair, a **sessão do usuário se perde**. A solução certa é ser
stateless + estado externalizado, não grudar o usuário na instância.

```csharp
// ❌ Estado na memória do processo: funciona com 1 instância, quebra com 2+.
private static readonly Dictionary<string, Cart> _cartsEmMemoria = new();

// ✅ Estado externalizado num cache distribuído (Redis): qualquer instância lê/escreve.
public async Task SaveCartAsync(string userId, Cart cart)
{
    await _distributedCache.SetStringAsync($"cart:{userId}", JsonSerializer.Serialize(cart));
}
```

**Pegadinha:** guardar carrinho/sessão numa `static` ou na memória do processo **funciona com 1
instância** e **quebra na hora que você escala pra 2+** — o usuário cai numa instância que não tem o
estado dele. Todo teste local passa; produção escalada falha.

**Como responder:** "Vertical é máquina maior — simples mas com teto e ponto único de falha.
Horizontal é mais instâncias atrás de um load balancer — elástico e resiliente, mas exige que o
serviço seja **stateless**: nenhuma request depende de estado na memória de uma instância específica,
então qualquer instância atende qualquer request. Estado de sessão vai pra um store compartilhado tipo
Redis. Sticky session é anti-pattern porque amarra o usuário a uma instância e derruba a sessão se ela
cair."

---

## 5. Escalabilidade — técnicas: load balancing, cache, filas, backpressure

**Load balancing.** O **load balancer** distribui as requests entre as instâncias saudáveis
(algoritmos: round-robin, least-connections). Ele faz **health check** e tira do rodízio as instâncias
que ficam unhealthy. É a peça que torna a escala horizontal transparente pro cliente.

**Caching.** Guardar resultados de operações caras (queries pesadas, dados que mudam pouco) reduz a
carga no banco e melhora a latência. Cache **distribuído** (Redis) para múltiplas instâncias
enxergarem o mesmo cache. O problema difícil de cache é sempre a **invalidação**: manter o cache
consistente com a fonte de verdade.

**Filas / mensageria (RabbitMQ, SQS, Kafka).** Uma fila **desacopla** o produtor do consumidor: a API
recebe a request, **enfileira** a tarefa e responde rápido; um **worker** consome no seu próprio
ritmo. Isso **absorve picos** — se chegam 10.000 requests num segundo, elas entram na fila e o worker
processa gradualmente, em vez de derrubar o banco. Também melhora resiliência (se o worker cai, a
mensagem fica na fila).

**Backpressure.** Quando o consumidor **não dá conta** do volume, você precisa **limitar a entrada**
em vez de aceitar tudo e derreter: **rate limiting** na API, limite de tamanho de fila, rejeitar/
adiar (HTTP 429), ou pausar o consumo. Backpressure é o mecanismo que impede que uma parte lenta do
sistema derrube o resto.

**Async é a base do throughput.** Tudo acima é multiplicado por async: como cada instância **não
segura threads em I/O**, ela aguenta muito mais requests concorrentes. Sem async, você esgota o thread
pool sob carga e nem load balancer nem fila salvam. Async é o **alicerce** do throughput por instância.

```csharp
// A API só enfileira e responde rápido; o worker processa depois (absorve pico).
public async Task<IActionResult> CriarPedido(PedidoDto dto)
{
    await _queue.PublishAsync(new ProcessarPedidoMessage(dto));
    return Accepted(); // 202: aceito, será processado de forma assíncrona
}
```

**Pegadinha:** introduzir uma fila torna o processamento **assíncrono** e, quase sempre, a entrega
vira **at-least-once** — a mesma mensagem pode ser reentregue (timeout, redelivery). Logo o
**consumidor precisa ser idempotente** (gancho direto pro próximo tópico), senão você processa o
pedido duas vezes.

**Como responder:** "Load balancer distribui entre instâncias e tira as unhealthy do ar. Cache
distribuído tira carga do banco. Fila desacopla e absorve pico: a API só enfileira e responde rápido,
o worker processa no seu ritmo. Backpressure limita a entrada quando o consumidor não dá conta. E tudo
isso repousa em async: sem segurar thread em I/O, cada instância aguenta muito mais carga. Só lembrar
que fila costuma ser at-least-once, então o consumidor tem que ser idempotente."

---

## 6. Idempotência: definição, HTTP, idempotency key e o mito do exactly-once

**Definição.** Uma operação é **idempotente** quando **repeti-la N vezes tem o mesmo efeito de
executá-la 1 vez**. Reprocessar não muda o resultado nem gera dado duplicado. Exemplo: "definir saldo
= 100" é idempotente (rodar 3x deixa 100); "somar 100 ao saldo" **não** é (rodar 3x soma 300).

**Por que importa.** Em rede real, requests **se repetem**: **retries** automáticos, **timeouts** (o
cliente não recebeu a resposta e tenta de novo, mas o servidor já processou), **duplo clique** do
usuário, e **entrega at-least-once** de filas. Se a operação não for idempotente, você **cobra duas
vezes**, **cria dois pedidos**, **envia dois e-mails**. Idempotência é o que torna **seguro repetir**.

**Métodos HTTP.** Por definição do HTTP:

- **GET** — idempotente e seguro (só lê, não muda estado).
- **PUT** — idempotente (substitui o recurso por um estado definido; repetir dá o mesmo estado).
- **DELETE** — idempotente (apagar o já apagado deixa no mesmo estado final: ausente).
- **POST** — **NÃO** idempotente (cria um recurso **novo a cada chamada**; dois POSTs = dois recursos).

Por isso um `POST` de **pagamento/criação** precisa de proteção extra pra sobreviver a retries.

**Idempotency key.** O padrão para tornar um `POST` seguro: o **cliente gera um Id único** (ex.: um
GUID) e o envia no header **`Idempotency-Key`**. O servidor **guarda** essa chave junto com o
resultado. Se a **mesma chave chegar de novo**, o servidor **devolve o resultado guardado sem
reexecutar** a operação. Assim, retries do mesmo pagamento não cobram duas vezes.

```csharp
// POST de pagamento protegido por idempotency key.
public async Task<IActionResult> Pagar([FromHeader(Name = "Idempotency-Key")] string key, PagamentoDto dto)
{
    // Já processamos essa chave? Devolve o resultado guardado (não reexecuta).
    var existente = await _idempotencyStore.GetAsync(key);
    if (existente is not null)
        return Ok(existente);

    var resultado = await _pagamentoService.CobrarAsync(dto);
    await _idempotencyStore.SaveAsync(key, resultado); // grava chave + resultado
    return Ok(resultado);
}
```

**Como implementar, no geral.** Duas abordagens comuns:
- **Dedup por chave:** manter uma tabela/cache de chaves já processadas; se a chave repetir, ignorar
  (ou devolver o resultado anterior). É o que a idempotency key faz.
- **Upsert:** modelar a operação como **inserir-ou-atualizar** por um id determinístico (o `PUT` é
  isso). Repetir só reafirma o mesmo estado. Trocar "somar" por "definir estado final" torna a
  operação naturalmente idempotente.

**Exactly-once é (quase) um mito.** Em sistemas distribuídos, **garantir que algo aconteça exatamente
uma vez** é essencialmente impossível de forma barata: falhas de rede, acks perdidos e crashes fazem
com que ou você entregue **at-most-once** (pode perder) ou **at-least-once** (pode duplicar). O padrão
viável e correto é: **at-least-once + consumidor idempotente**. A mensagem pode chegar duas vezes, mas
como processá-la duas vezes tem o mesmo efeito, o **efeito observado é exactly-once**. Idempotência é o
que compra o "exactly-once" na prática.

**Pegadinha:** "minha fila/broker garante exactly-once." Quase nunca de verdade (e quando "garante", é
caro e com ressalvas). Assuma **at-least-once** e **projete o consumidor idempotente** — é o que
sobrevive a redeliveries sem duplicar efeito.

**Como responder:** "Idempotente é: repetir a operação dá o mesmo efeito de fazê-la uma vez —
reprocessar não duplica. Importa por causa de retries, timeouts, duplo clique e filas at-least-once,
que em rede real repetem requests. No HTTP, GET/PUT/DELETE são idempotentes; POST não, porque cria
recurso novo a cada chamada — por isso pagamento usa uma idempotency key: o cliente manda um Id único,
o servidor guarda chave + resultado e, se repetir, devolve o mesmo sem reexecutar. Exactly-once é
praticamente um mito em distribuído; o padrão real é at-least-once + consumidor idempotente, que dá o
efeito de exactly-once."

---

## Glossário

- **Task:** abstração de uma operação assíncrona em andamento (uma promessa de resultado). Não é uma
  thread e, em I/O, não cria thread pra esperar.
- **Máquina de estados (async):** reescrita do método `async` pelo compilador em estados, permitindo
  pausar em cada `await` e retomar depois.
- **Throughput:** requests processadas por unidade de tempo. É o que async melhora (≠ latência).
- **Latência:** tempo de uma request individual. Async **não** melhora isso.
- **Thread pool:** conjunto de threads reutilizáveis gerenciado pelo runtime. ASP.NET Core atende
  requests com threads do pool.
- **Thread pool starvation:** esgotamento do pool quando o código bloqueia threads (ex.: `.Result`);
  requests entram em fila e a latência dispara.
- **I/O bound:** gargalo é esperar por rede/disco/banco → async ajuda.
- **CPU bound:** gargalo é cálculo → async não ajuda; use `Task.Run`/paralelismo.
- **SynchronizationContext:** contexto pra onde o `await` tenta voltar (thread de UI, request do
  ASP.NET clássico). Causa do deadlock com `.Result`. ASP.NET Core não tem.
- **ConfigureAwait(false):** "não preciso voltar ao contexto capturado"; evita deadlock e é mais
  eficiente em bibliotecas.
- **async void:** fire-and-forget que engole exceções; só em event handlers.
- **Escala vertical:** máquina maior. Teto físico, ponto único de falha.
- **Escala horizontal:** mais instâncias atrás de load balancer. Exige stateless.
- **Stateless:** serviço que não guarda estado de sessão na memória local; qualquer instância atende
  qualquer request.
- **Sticky session (afinidade):** amarrar o usuário a uma instância. Anti-pattern de escala.
- **Backpressure:** limitar a entrada quando o consumidor não dá conta, pra não derrubar o sistema.
- **Idempotência:** repetir a operação = mesmo efeito de fazê-la uma vez.
- **Idempotency key:** Id único enviado pelo cliente pra deduplicar retries de um POST.
- **At-least-once:** entrega que pode duplicar (padrão de filas). Combinada com consumidor idempotente,
  dá efeito de exactly-once.

## Checagem de entendimento

1. Por que async melhora **throughput/escalabilidade** mas **não** a latência de uma request? O que a
   thread faz durante o `await` de um I/O?
2. Qual a diferença entre **I/O bound** e **CPU bound**, e por que `Task.Run` é a ferramenta errada
   para "tornar async" uma chamada de I/O?
3. Explique a **causa exata** do deadlock com `.Result`/`.Wait()` num contexto com
   `SynchronizationContext`. Por que isso não acontece no ASP.NET Core?
4. Por que um serviço precisa ser **stateless** para escalar horizontalmente, e por que **sticky
   session** é considerado anti-pattern?
5. Quais métodos HTTP são **idempotentes** e por que **POST** não é? Como uma **idempotency key**
   protege um POST de pagamento?
6. Por que **exactly-once** é praticamente um mito, e qual é o padrão viável que produz o mesmo efeito
   na prática?
