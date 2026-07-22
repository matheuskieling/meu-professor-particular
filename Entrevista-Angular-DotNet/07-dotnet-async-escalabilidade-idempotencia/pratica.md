# Prática — Simulação de entrevista (Módulo 07)

Aqui o agente vira **entrevistador**. Faz cada pergunta como cairia numa entrevista de backend .NET
pleno/sênior, ouve a resposta do aluno **em voz alta (texto)** e então **critica**: o que faltou, o
que ficou impreciso, como soar mais sênior. Ordem da mais comum à pegadinha. O aluno responde **sem
olhar a teoria** — é treino de recall sob pressão.

> Dica de condução: se o aluno travar, **pare e ensine junto** (mini-aula ali na hora), depois retome.

---

### Pergunta 1 — O que `async/await` faz e por que ele melhora escalabilidade?

**Resposta-modelo:** "O compilador transforma o método async numa máquina de estados; cada `await` é
um ponto onde ele pausa e retoma depois. O ponto-chave: durante um `await` de I/O, a **thread é
liberada de volta pro thread pool** e atende outra request, em vez de ficar bloqueada esperando o
banco responder. Por isso async melhora **throughput/escalabilidade** — o servidor atende mais
requests concorrentes com as mesmas threads — mas **não** deixa uma request individual mais rápida: a
latência é a mesma, o banco leva o mesmo tempo."

**Erros comuns:**
- Dizer que async "deixa o código mais rápido" (confunde throughput com latência).
- Achar que async cria threads / roda em paralelo por baixo.
- Não mencionar o thread pool nem a liberação da thread durante o I/O — que é o "porquê" real.

---

### Pergunta 2 — Async é o mesmo que multithreading / paralelismo?

**Resposta-modelo:** "Não. Async é sobre **não bloquear** enquanto espera algo (I/O); por padrão roda
numa thread só e o `await` libera a thread durante a espera. Multithreading/paralelismo é rodar
trabalho de fato **ao mesmo tempo** em vários núcleos — isso é `Task.Run`, `Parallel`, `Task.WhenAll`
com trabalho de CPU. `Task` também não é `Thread`: é uma operação em andamento, uma promessa de
resultado, que em I/O nem usa thread pra esperar."

**Erros comuns:**
- Tratar `async` e `Task.Run` como sinônimos.
- Dizer que `await` "roda em outra thread" (pode retomar em outra, mas não é o objetivo nem garante
  paralelismo).
- Confundir `Task` com `Thread`.

---

### Pergunta 3 — Qual a diferença entre trabalho I/O bound e CPU bound? Quando usar `Task.Run`?

**Resposta-modelo:** "I/O bound é esperar por algo externo — rede, disco, banco; a CPU fica ociosa.
Aí async ajuda, porque libera a thread durante a espera. CPU bound é cálculo puro que ocupa o
processador — não há espera pra liberar thread, então async por si só não ajuda; aí uso `Task.Run` ou
paralelismo pra usar mais núcleos e tirar o trabalho do thread da request. Regra: I/O → `async/await`
sobre APIs async nativas; CPU pesado → `Task.Run`. E **não** envolvo I/O async em `Task.Run`, porque
isso só desperdiça uma thread do pool."

**Erros comuns:**
- Usar `Task.Run` pra "tornar async" uma chamada de banco/HTTP (desperdiça thread).
- Achar que async acelera cálculo de CPU.
- Não saber dar um exemplo concreto de cada tipo.

---

### Pergunta 4 — O que é thread pool starvation e o que costuma causar?

**Resposta-modelo:** "É o esgotamento do thread pool: quando o código **bloqueia** threads em vez de
liberá-las, elas ficam presas e o pool acaba. Requests novas entram em fila, a latência dispara e a
app parece travada sob carga. A causa clássica é **sync-over-async** — chamar `.Result` ou `.Wait()`
em algo async — e também I/O síncrono em muitas requests. É um dos motivos de 'async all the way':
uma chamada bloqueante no caminho já pode esgotar o pool sob carga."

**Erros comuns:**
- Confundir starvation com deadlock (são coisas diferentes, embora `.Result` cause os dois em
  contextos distintos).
- Não ligar starvation ao bloqueio de threads.

---

### Pergunta 5 — O que causa o deadlock com `.Result` / `.Wait()`?

**Resposta-modelo:** "É sync-over-async. Em ambientes com `SynchronizationContext` — UI ou ASP.NET
clássico — o `await` por padrão tenta **retomar na mesma thread** do contexto (a thread de UI, a
thread da request). Se eu **bloqueio** essa thread com `.Result` esperando a `Task`, essa mesma thread
é a que o `await` precisa pra continuar — ela está travada esperando a si mesma. Deadlock. A cura de
verdade é **async all the way**, nunca bloquear. Detalhe importante: o **ASP.NET Core não tem
`SynchronizationContext`**, então esse deadlock específico não acontece nele — mas `.Result` continua
ruim ali por causa de starvation."

**Erros comuns:**
- Dizer que `.Result` "sempre" deadlocka (no ASP.NET Core não).
- Dizer que `ConfigureAwait(false)` "resolve" — ele evita, mas a cura é não bloquear.
- Não explicar a mecânica ("a thread espera a si mesma").

---

### Pergunta 6 — Para que serve `ConfigureAwait(false)` e quando é `async void` aceitável?

**Resposta-modelo:** "`ConfigureAwait(false)` diz ao `await`: 'não preciso voltar ao
`SynchronizationContext` capturado — retome em qualquer thread do pool'. Isso evita o deadlock do
`.Result` e é mais eficiente; era essencial em **bibliotecas** e no ASP.NET clássico. No ASP.NET Core
importa menos porque não há contexto pra voltar. Já `async void` é fire-and-forget: quem chama não
pode `await` e as exceções não são capturáveis por quem chamou — sobem como exceção não tratada. Por
isso só uso `async void` em **event handlers**, onde a assinatura exige `void`; em qualquer outro
lugar, `async Task`."

**Erros comuns:**
- Achar que `ConfigureAwait(false)` muda o comportamento em ASP.NET Core do mesmo jeito que no
  clássico.
- Usar `async void` em lógica de negócio (perde a exceção, não dá pra await nem testar).

---

### Pergunta 7 — Como você escala uma API horizontalmente? O que significa ser stateless?

**Resposta-modelo:** "Escala horizontal é colocar **mais instâncias** atrás de um **load balancer**,
em vez de uma máquina maior. Pra isso funcionar, o serviço precisa ser **stateless**: nenhuma request
pode depender de estado guardado na memória de uma instância específica — assim **qualquer instância
atende qualquer request** e o load balancer distribui livremente. O estado que precisa persistir
(sessão, carrinho, cache) vai pra um **store compartilhado**, tipo Redis. Com isso dá pra
adicionar/remover instâncias conforme a carga e sobreviver à queda de uma delas."

**Erros comuns:**
- Responder só "boto uma máquina maior" (isso é vertical, tem teto e ponto único de falha).
- Não mencionar stateless como pré-requisito.
- Não dizer onde o estado vai morar (Redis / store compartilhado).

---

### Pergunta 8 — Por que sticky sessions são um anti-pattern? Vertical vs horizontal.

**Resposta-modelo:** "Sticky session é o load balancer sempre mandar o mesmo usuário pra **mesma
instância**, porque o estado dele mora lá. É anti-pattern de escala: quebra o balanceamento (uma
instância pode ficar sobrecarregada), atrapalha escalar/reduzir, e se aquela instância cair, a
**sessão do usuário se perde**. O certo é ser stateless com estado externalizado. Sobre escala:
**vertical** é máquina maior — simples mas com teto físico e ponto único de falha; **horizontal** é
mais instâncias — elástico e resiliente, mas exige stateless."

**Erros comuns:**
- Não saber o que é sticky session.
- Achar que sticky session "resolve" o problema de estado (ela só esconde o design errado).

---

### Pergunta 9 — Como filas ajudam na escalabilidade? O que é backpressure?

**Resposta-modelo:** "Uma fila **desacopla** produtor e consumidor: a API recebe a request, enfileira
a tarefa e responde rápido (ex.: 202 Accepted); um worker consome no seu ritmo. Isso **absorve pico** —
se chegam 10 mil requests num segundo, elas entram na fila e o worker processa gradualmente, sem
derrubar o banco. **Backpressure** é o mecanismo de **limitar a entrada** quando o consumidor não dá
conta — rate limiting, limite de tamanho de fila, rejeitar com 429 — pra uma parte lenta não derrubar
o sistema todo. E lembrando: fila costuma ser **at-least-once**, então o consumidor precisa ser
idempotente."

**Erros comuns:**
- Não explicar o desacoplamento nem o "absorve pico".
- Não saber o que é backpressure.
- Esquecer a ligação fila → at-least-once → consumidor idempotente.

---

### Pergunta 10 — O que é idempotência e por que ela importa?

**Resposta-modelo:** "Idempotente é: **repetir a operação N vezes tem o mesmo efeito de fazê-la uma
vez** — reprocessar não muda o resultado nem duplica dado. 'Definir saldo = 100' é idempotente; 'somar
100' não é. Importa porque em rede real as requests **se repetem**: retries automáticos, timeouts (o
cliente não recebeu a resposta e tenta de novo, mas o servidor já processou), duplo clique do usuário,
e filas at-least-once. Sem idempotência, você cobra duas vezes ou cria dois pedidos. É o que torna
**seguro repetir** — essencial em qualquer sistema com retries."

**Erros comuns:**
- Dar só a definição de dicionário sem citar **por que** (retries, timeouts, duplo clique).
- Não dar exemplo de operação idempotente vs não idempotente.

---

### Pergunta 11 — Quais métodos HTTP são idempotentes e por que POST não é?

**Resposta-modelo:** "GET, PUT e DELETE são idempotentes. GET só lê. PUT substitui o recurso por um
estado definido — repetir dá o mesmo estado. DELETE apagar o já apagado deixa no mesmo estado final:
ausente. **POST não é** idempotente porque **cria um recurso novo a cada chamada** — dois POSTs viram
dois recursos. Por isso um POST de pagamento ou criação precisa de proteção pra sobreviver a retries:
a **idempotency key** — o cliente manda um Id único no header, o servidor guarda chave + resultado e,
se a mesma chave chegar de novo, devolve o resultado guardado **sem reexecutar**."

**Erros comuns:**
- Confundir idempotente com 'seguro' (GET é ambos; PUT/DELETE são idempotentes mas não seguros).
- Dizer que POST é idempotente.
- Não saber explicar a idempotency key como solução.

---

### Pergunta 12 — Exactly-once existe? Como você garante processamento único numa fila?

**Resposta-modelo:** "Exactly-once é praticamente um **mito** em sistemas distribuídos — garantir que
algo aconteça exatamente uma vez, de forma barata, é essencialmente impossível por causa de falhas de
rede, acks perdidos e crashes. Ou você tem at-most-once (pode perder) ou at-least-once (pode duplicar).
O padrão viável é **at-least-once + consumidor idempotente**: a mensagem pode chegar duas vezes, mas
como processá-la duas vezes tem o mesmo efeito, o **efeito observado é exactly-once**. Na prática eu
dedup por chave (guardo os ids já processados) ou modelo a operação como upsert. Nunca confio num
broker que 'promete' exactly-once — assumo at-least-once e projeto o consumidor idempotente."

**Erros comuns:**
- Afirmar que a fila/broker garante exactly-once e parar aí.
- Não conhecer o padrão at-least-once + idempotência.
- Não citar dedup por chave ou upsert como implementação.
