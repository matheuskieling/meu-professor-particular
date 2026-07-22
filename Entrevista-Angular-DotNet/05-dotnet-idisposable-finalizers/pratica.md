# Prática — Simulação de entrevista (Módulo 05)

Aqui o agente vira o **entrevistador**. Faz uma pergunta por vez, ouve a resposta do aluno em
voz alta (texto) e **critica**: o que faltou, o que foi impreciso, como soar mais sênior. As
perguntas vão da mais comum à pegadinha. Cada uma traz a **resposta-modelo** (o que um sênior
diria) e os **erros comuns** que derrubam o candidato.

> Dica de condução: se o aluno travar, **não** apenas dê a resposta e siga — vire uma mini-aula
> ali (explique o conceito, dê a resposta-modelo, cheque se entendeu) e só então retome.

---

### Pergunta 1 — O que é `IDisposable` e quando você implementa?

**Resposta-modelo:** "`IDisposable` é uma interface com um único método, `Dispose()`. É o
contrato de liberação **determinística** de recursos: quando termino de usar, chamo `Dispose`
e o recurso é liberado na hora, sem esperar o GC. Implemento quando minha classe detém um
**recurso não gerenciado** (file handle, socket, conexão de banco, ponteiro nativo) ou quando
ela detém como campo **outro `IDisposable`**, do qual sou responsável por dar `Dispose`. Se a
classe só tem campos gerenciados triviais, não implemento — não há o que liberar."

**Erros comuns:** dizer que `IDisposable` "libera memória" (não — memória é do GC; `Dispose`
libera recursos não gerenciados); implementar em toda classe "por segurança"; não saber que o
gatilho é *deter um recurso não gerenciado ou um `IDisposable`*.

---

### Pergunta 2 — Por que o Garbage Collector sozinho não resolve? Se ele coleta tudo, por que preciso de `Dispose`?

**Resposta-modelo:** "O GC gerencia **memória gerenciada** e faz isso de forma **não
determinística** — não sei quando vai coletar. Recursos não gerenciados (arquivos, sockets,
conexões de banco) vivem fora do heap do GC, e ele **não sabe** fechá-los: ele conhece
memória, não 'devolva esta conexão ao pool'. Além disso esses recursos são **escassos** —
segurar 500 conexões esperando o GC esgota o pool. `Dispose` me dá liberação determinística: eu
libero exatamente quando termino."

**Erros comuns:** achar que o GC fecha handles; confundir "o objeto será coletado" (memória)
com "o recurso será liberado" (só via `Dispose`/finalizer); não mencionar determinismo nem
escassez.

---

### Pergunta 3 — O que o `using` faz por baixo dos panos?

**Resposta-modelo:** "O `using` é açúcar sintático. O compilador expande `using (var x = ...)
{ ... }` para um `try/finally`, onde o `finally` chama `x?.Dispose()`. É esse `finally` que
garante o `Dispose` **mesmo se o bloco lançar exceção** — por isso `using` é seguro. O `using
var` do C# 8 faz a mesma coisa, só que o `Dispose` acontece no fim do **escopo** (a chave que
fecha o método/bloco), sem indentação extra. Com vários recursos, o descarte é em ordem
inversa, LIFO."

**Erros comuns:** dizer só "chama Dispose no fim" sem citar o `try/finally`; não saber que o
`finally` cobre o caso de exceção; confundir o escopo do `using var`.

---

### Pergunta 4 — Me explique o Dispose Pattern completo. Por que `Dispose(bool disposing)` recebe um parâmetro?

**Resposta-modelo:** "O padrão tem quatro peças: um `Dispose()` público, que chama
`Dispose(true)` e depois `GC.SuppressFinalize(this)`; um `protected virtual void Dispose(bool
disposing)`, que é o coração e é `virtual` pra herança poder estender; um campo `_disposed`
que guarda contra double-dispose; e, **se houver recurso não gerenciado direto**, um finalizer
`~Classe()` que chama `Dispose(false)`.

O parâmetro `disposing` diz **de onde** veio a chamada. Se `true`, veio do `Dispose()` do
usuário: é seguro tocar em objetos **gerenciados** (dar `Dispose` em outros `IDisposable`),
porque eles ainda existem. Se `false`, veio do **finalizer**: os objetos gerenciados que eu
referencio **podem já ter sido coletados** pelo GC (a ordem de finalização não é garantida),
então eu **só** libero os não gerenciados."

**Erros comuns:** esquecer o `SuppressFinalize`; não saber explicar o `disposing`; achar que
todo `IDisposable` precisa de finalizer (só quem tem recurso não gerenciado direto precisa);
não mencionar o `_disposed`.

---

### Pergunta 5 — Qual a diferença entre `Dispose` e um finalizer?

**Resposta-modelo:** "`Dispose` é **determinístico e explícito**: eu chamo (via `using`), e o
recurso é liberado na hora. O finalizer (`~Classe()`) é **não determinístico**: quem chama é o
GC, num momento que eu não controlo, numa thread de finalização separada. O finalizer é só uma
**rede de segurança** — se o usuário esquecer o `Dispose`, ele ainda libera o recurso não
gerenciado. E é **caro**: o objeto entra na fila de finalização, sobrevive à primeira coleta e
é promovido de geração. Por isso a prática é: implemento `Dispose`, e uso finalizer só como
fallback pra recurso não gerenciado — hoje, quase sempre substituído por `SafeHandle`."

**Erros comuns:** dizer que são a mesma coisa; achar que o finalizer roda "quando eu quero";
não mencionar o custo (fila + promoção de geração); não saber que o `Dispose` é chamado por
você e o finalizer pelo GC.

---

### Pergunta 6 — Para que serve `GC.SuppressFinalize(this)`?

**Resposta-modelo:** "Quando o usuário chama `Dispose()`, eu já liberei tudo — inclusive os
recursos não gerenciados. `GC.SuppressFinalize(this)` **remove o objeto da fila de
finalização**, dizendo ao GC 'não precisa rodar meu finalizer'. Isso evita o custo do
finalizer: sem ele, o objeto seria finalizado à toa, sobrevivendo a uma coleta e sendo
promovido de geração desnecessariamente. Ou seja: descarte explícito → `SuppressFinalize` → o
GC me trata como um objeto normal."

**Erros comuns:** não saber o que é a fila de finalização; achar que `SuppressFinalize` "chama
o finalizer" (é o contrário — ele impede); usá-lo numa classe que nem tem finalizer (aí é
inofensivo mas denota confusão).

---

### Pergunta 7 — Por que você NÃO deveria dar `new HttpClient()` a cada requisição?

**Resposta-modelo:** "Porque `HttpClient`, apesar de ser `IDisposable`, foi feito pra ser
**reutilizado**. Quando eu dou `Dispose` nele, o socket subjacente não fecha na hora — ele fica
em `TIME_WAIT`. Criar e descartar um por requisição, em volume, esgota as **portas TCP** —
*socket/port exhaustion*, dá `SocketException`. Um singleton na mão resolveria o socket, mas
cacheia o **DNS** e não vê mudanças de endereço. A solução idiomática é `IHttpClientFactory`
(`AddHttpClient`): ele mantém um pool de `HttpMessageHandler` reutilizados e os rotaciona pra
lidar com o DNS. E eu **não** dou `Dispose` nesse `HttpClient` — o factory cuida do ciclo de
vida."

**Erros comuns:** envolver `HttpClient` num `using` a cada chamada (o erro clássico); não saber
o termo *socket exhaustion*/`TIME_WAIT`; conhecer o problema mas não saber a solução
(`IHttpClientFactory`); esquecer o detalhe do DNS *stale* do singleton na mão.

---

### Pergunta 8 — Quando um recurso precisa ser liberado de forma assíncrona? Como você faz isso?

**Resposta-modelo:** "Quando a limpeza envolve I/O — dar *flush* de um stream para a rede,
fechar uma conexão com handshake, um `DbContext` do EF Core. Fazer isso síncrono com
`.Wait()`/`.Result` bloquearia a thread e arrisca deadlock. Aí implemento `IAsyncDisposable`,
com `DisposeAsync` retornando `ValueTask`, e consumo com `await using var x = ...` — o
compilador chama e **aguarda** o `DisposeAsync` no fim do escopo, sem bloquear. Se a classe
implementa os dois, prefiro `DisposeAsync` no caminho async, e não faço `.Wait()` dentro dele."

**Erros comuns:** não conhecer `IAsyncDisposable`/`await using`; achar que dá pra bloquear com
`.Result` no `Dispose` "e tá tudo bem"; não citar um caso real (EF `DbContext`).

---

### Pergunta 9 — O que acontece se você chamar `Dispose()` duas vezes? E se esquecer de chamar?

**Resposta-modelo:** "Chamar `Dispose()` duas vezes deve ser **no-op** — o padrão exige
idempotência, e é o campo `_disposed` que protege (`if (_disposed) return;`). Um `Dispose` que
explode na segunda chamada é um bug. Se eu **esquecer** de chamar: se a classe tem finalizer, o
recurso não gerenciado vaza até o GC finalizar — mais tarde e mais caro; se não tem finalizer,
vaza até o processo morrer. Por isso a regra é usar `using` sempre que possível — ele garante o
`Dispose` deterministicamente."

**Erros comuns:** achar que double-dispose "sempre lança"; não saber a diferença entre esquecer
com e sem finalizer; não relacionar com o campo `_disposed`.

---

### Pergunta 10 — O que é `SafeHandle` e por que ele é a alternativa moderna a escrever um finalizer?

**Resposta-modelo:** "`SafeHandle` é um wrapper para um handle **não gerenciado** (ex.:
`SafeFileHandle`). Ele **já tem** um finalizer crítico próprio, é robusto contra falhas
parciais e resiste a *handle recycling attacks*. Com ele, minha classe **não precisa** de um
`~destrutor`: eu guardo um `SafeHandle` em vez de um `IntPtr` cru, implemento só `IDisposable`
e dou `Dispose` no `SafeHandle`. É mais seguro e mais simples do que escrever o finalizer na
mão — por isso, na prática, quase nunca escrevo um `~destrutor`."

**Erros comuns:** não conhecer `SafeHandle`; achar que sempre preciso escrever finalizer pra
recurso não gerenciado; não saber que o `SafeHandle` traz o finalizer crítico embutido.

---

### Pergunta 11 (pegadinha) — Você tem `using var conexao = ...` dentro de um `foreach`. Cada iteração fecha a conexão?

**Resposta-modelo:** "Não! `using var` dispõe no fim do **escopo do método**, não no fim de
cada iteração. Dentro de um loop, isso acumula recursos abertos até o método terminar. Se eu
quero liberar **a cada volta**, tenho que usar um bloco `using (...) { }` explícito dentro do
loop — aí o `Dispose` acontece no fim de cada iteração."

**Erros comuns:** afirmar que fecha a cada iteração; não perceber que o escopo do `using var` é
o método; não saber corrigir com o bloco explícito.

---

### Pergunta 12 (pegadinha / raciocínio) — Um colega escreveu um `Dispose` que faz `try { Flush(); } catch { }` engolindo a exceção. Que problema você aponta?

**Resposta-modelo:** "Engolir a exceção **esconde falhas importantes** — se o `Flush`/commit
não completou, os dados podem ter se perdido e ninguém fica sabendo. Por outro lado, **lançar**
do `Dispose` também é arriscado: quando ele roda no `finally` de um `using`, uma exceção do
`Dispose` pode **mascarar a exceção original** do bloco. A regra prática é: `Dispose` deve ser
barato e não lançar em condições normais; se há uma operação que pode falhar de verdade (flush,
commit), eu a faço **explicitamente antes** — `FlushAsync()`, `SaveChangesAsync()` — e não
escondida dentro do `Dispose`."

**Erros comuns:** só dizer "engolir exceção é ruim" sem explicar o trade-off de lançar no
`finally`; não sugerir mover a operação crítica pra fora do `Dispose`.
