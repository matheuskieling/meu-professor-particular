# Módulo 05 — .NET: IDisposable, using & Finalizers

Este módulo é sobre **liberação determinística de recursos** — um dos temas favoritos de
entrevista .NET pleno/sênior, porque expõe se o candidato entende os limites do Garbage
Collector. A pergunta por trás de tudo é: *"o GC gerencia memória; então quem gerencia o
resto?"*. A resposta é `IDisposable`, o `using`, o Dispose Pattern e (raramente) os
finalizers.

O entrevistador quase nunca quer que você recite código. Ele quer ouvir o **porquê**: por que
o GC sozinho não basta, por que `Dispose(bool disposing)` recebe um parâmetro, por que
`GC.SuppressFinalize(this)`, e por que você **não** deve dar `new HttpClient()` a cada
requisição. Este documento cobre cada ponto com a explicação precisa, o exemplo em C# (.NET 8
/ C# 12), a **pegadinha** clássica e o **como responder** curto.

---

## 1. Recursos gerenciados vs não gerenciados: por que o GC não basta

O **Garbage Collector** gerencia **memória gerenciada** — objetos no heap do CLR. Ele descobre
quando um objeto não tem mais referências e libera essa memória. Mas ele faz isso de forma
**não determinística**: você não controla *quando* a coleta acontece.

**Recursos gerenciados** são objetos .NET normais (uma `List<T>`, uma `string`). O GC cuida
deles sozinho.

**Recursos não gerenciados** vivem **fora** do heap do GC e representam algo do sistema
operacional ou nativo:

- File handles (arquivos abertos)
- Sockets / conexões de rede
- Conexões de banco de dados (que vêm de um *pool* limitado)
- Handles de OS (mutex, semáforo, janelas GDI+)
- Ponteiros nativos / memória alocada por código não gerenciado

O GC **não sabe** o que esses handles significam. Ele conhece *memória*, não "feche este
arquivo" ou "devolva esta conexão ao pool". Além disso, esses recursos costumam ser
**escassos**: se você segurar 500 conexões abertas esperando o GC coletar "quando der",
esgota o pool e a aplicação trava.

Por isso existe **liberação determinística**: `IDisposable` permite dizer *exatamente* quando
liberar o recurso (no fim do `using`), sem esperar o humor do GC.

```csharp
// SqlConnection detém um recurso não gerenciado (a conexão do pool).
// Sem Dispose, a conexão fica "presa" até o GC coletar — pode esgotar o pool.
using var conexao = new SqlConnection(connectionString);
conexao.Open();
// ... usa ...
// Dispose (fecha e devolve ao pool) acontece no fim do escopo, deterministicamente.
```

**Pegadinha:** "mas o GC não vai coletar meu objeto?". Vai — a *memória* do wrapper .NET. Só
que o recurso não gerenciado (o handle) só é liberado pelo `Dispose` (ou por um finalizer de
rede de segurança). Memória e recurso são coisas diferentes.

**Como responder:** "O GC só gerencia memória gerenciada, e de forma não determinística. File
handles, sockets e conexões de banco são recursos não gerenciados e escassos — o GC não sabe
fechá-los na hora certa. `IDisposable` dá liberação determinística: eu libero exatamente
quando termino de usar."

---

## 2. IDisposable e Dispose(): o contrato e quando implementar

`IDisposable` é uma interface com **um único método**:

```csharp
public interface IDisposable
{
    void Dispose();
}
```

O contrato é: *"quando você terminar de me usar, chame `Dispose()` e eu libero meus recursos
agora"*. É a base da liberação determinística.

**Quando implementar `IDisposable`:**

1. Sua classe **detém diretamente** um recurso não gerenciado (um handle, ponteiro nativo).
2. Sua classe **detém como campo** outro objeto `IDisposable` (ex.: um `HttpClient`, um
   `SqlConnection`, um `Stream`) — você é responsável por dar `Dispose` nele.

Se sua classe só tem campos gerenciados triviais (`int`, `string`, `List<T>`), **não**
implemente `IDisposable` — é over-engineering.

Regras do bom `Dispose`:

- **Idempotente:** chamar `Dispose()` duas vezes não pode explodir (double-dispose seguro).
- Depois de disposto, usar o objeto deve lançar `ObjectDisposedException` — ele está "morto".

```csharp
public sealed class LeitorDeArquivo : IDisposable
{
    private readonly FileStream _stream;   // FileStream é IDisposable
    private bool _disposed;

    public LeitorDeArquivo(string caminho) => _stream = File.OpenRead(caminho);

    public byte[] LerTudo()
    {
        ObjectDisposedException.ThrowIf(_disposed, this); // C# 8+/.NET 7+ helper
        using var ms = new MemoryStream();
        _stream.CopyTo(ms);
        return ms.ToArray();
    }

    public void Dispose()
    {
        if (_disposed) return;   // double-dispose seguro
        _stream.Dispose();       // libero o IDisposable que eu detenho
        _disposed = true;
    }
}
```

> Observação: quando a classe é `sealed` e só detém *outros* `IDisposable` (nada não
> gerenciado direto), este `Dispose` simples basta — **não precisa** de finalizer nem do
> padrão completo. O padrão completo (seção 4) é para quem detém recurso não gerenciado direto
> e/ou pode ser herdado.

**Pegadinha:** implementar `IDisposable` "por precaução" numa classe sem nada a liberar. Só
implemente se há de fato um recurso (não gerenciado ou um `IDisposable` interno) para liberar.

**Como responder:** "Implemento `IDisposable` quando minha classe detém um recurso não
gerenciado ou detém outro `IDisposable`. `Dispose` libera na hora, tem que ser idempotente, e
usar o objeto depois de disposto deve lançar `ObjectDisposedException`."

---

## 3. using: statement, using declaration e o que o compilador gera

O `using` é o jeito idiomático de garantir o `Dispose` — inclusive quando dá exceção.

### using statement (clássico)

```csharp
using (var stream = File.OpenRead("dados.txt"))
{
    // usa o stream
} // Dispose() chamado aqui
```

O compilador **expande isso para um `try/finally`**:

```csharp
FileStream stream = File.OpenRead("dados.txt");
try
{
    // usa o stream
}
finally
{
    if (stream != null) stream.Dispose();  // roda mesmo se der exceção no try
}
```

É o `finally` que torna o `using` seguro: **o `Dispose` acontece mesmo se o bloco lançar
exceção**.

### using declaration (C# 8 — `using var`)

Sem indentação extra: o `Dispose` é chamado no fim do **escopo** (a chave que fecha o
método/bloco).

```csharp
public byte[] Ler(string caminho)
{
    using var stream = File.OpenRead(caminho);
    return LerTudo(stream);
} // stream.Dispose() chamado aqui, no fim do método
```

### Múltiplos recursos

Você pode empilhar `using`s; o descarte acontece em **ordem inversa (LIFO)**:

```csharp
using var conexao = new SqlConnection(cs);
using var comando = conexao.CreateCommand();
// no fim do escopo: comando.Dispose() primeiro, depois conexao.Dispose()
```

**Pegadinha:** `using var` **dentro de um loop** só dispõe no fim do método, não a cada
iteração. Se você quer liberar o recurso *a cada volta* do loop, use um bloco `using (...) {
}` explícito dentro do loop — senão você acumula recursos abertos.

```csharp
foreach (var caminho in caminhos)
{
    using (var s = File.OpenRead(caminho)) // dispõe a cada iteração
    {
        Processar(s);
    }
}
```

**Como responder:** "`using` é açúcar sintático para `try/finally` com `Dispose` no `finally`
— por isso ele libera mesmo com exceção. O `using var` do C# 8 dispõe no fim do escopo. E
cuidado com `using var` dentro de loop: ele só libera no fim do método."

---

## 4. O Dispose Pattern completo

Quando a classe detém um **recurso não gerenciado direto** e/ou pode ser **herdada**, usa-se o
Dispose Pattern completo. Ele coordena o descarte manual (`Dispose`) com o de rede de
segurança (finalizer).

```csharp
public class RecursoNativo : IDisposable
{
    private IntPtr _handle;   // recurso NÃO gerenciado (ex.: handle do OS)
    private FileStream? _stream; // recurso GERENCIADO (outro IDisposable)
    private bool _disposed;

    // 1) Dispose() público — o que o usuário chama
    public void Dispose()
    {
        Dispose(disposing: true);
        GC.SuppressFinalize(this); // já limpei; GC não precisa me finalizar
    }

    // 2) O coração do padrão — virtual pra herança poder estender
    protected virtual void Dispose(bool disposing)
    {
        if (_disposed) return; // guarda contra double-dispose

        if (disposing)
        {
            // Veio do Dispose() do usuário: é SEGURO tocar em objetos gerenciados
            _stream?.Dispose();
        }

        // Sempre libere os NÃO gerenciados (tanto no Dispose quanto no finalizer)
        if (_handle != IntPtr.Zero)
        {
            LiberarHandleNativo(_handle);
            _handle = IntPtr.Zero;
        }

        _disposed = true;
    }

    // 3) Finalizer — rede de segurança, SÓ se houver recurso não gerenciado direto
    ~RecursoNativo() => Dispose(disposing: false);

    private static void LiberarHandleNativo(IntPtr h) { /* P/Invoke CloseHandle etc. */ }
}
```

**Por que o parâmetro `bool disposing`?** Ele diz *de onde* o `Dispose(bool)` foi chamado:

- `disposing == true` → veio do `Dispose()` **do usuário**. É seguro tocar em campos
  gerenciados (outros `IDisposable`), porque eles ainda existem. Libera **gerenciados e não
  gerenciados**.
- `disposing == false` → veio do **finalizer**. Nesse momento os objetos gerenciados que sua
  classe referencia **podem já ter sido coletados** pelo GC (a ordem de finalização não é
  garantida). Então você **não toca** neles — libera **só os não gerenciados**.

**Por que `GC.SuppressFinalize(this)`?** Se o usuário chamou `Dispose()`, você já limpou tudo.
`SuppressFinalize` remove o objeto da **fila de finalização** — assim o GC **não** precisa
rodar o finalizer depois, o que evita o custo (ver seção 5). Sem isso, o objeto seria
finalizado à toa mesmo já tendo sido limpo.

**Herança:** a classe base declara `protected virtual void Dispose(bool)`; a derivada faz
`override`, libera *seus* recursos e no fim chama `base.Dispose(disposing)`.

**Como responder:** "O `Dispose()` público chama `Dispose(true)` e `GC.SuppressFinalize(this)`.
O `Dispose(bool disposing)` é virtual pra herança. O `disposing` distingue quem chamou: se
`true`, veio do usuário e posso liberar recursos gerenciados; se `false`, veio do finalizer e
só toco nos não gerenciados, porque os gerenciados podem já ter sido coletados. O
`SuppressFinalize` evita o custo do finalizer quando o descarte já foi explícito."

---

## 5. Finalizers (~Destrutor): custo e por que raramente escrever um

Um **finalizer** é escrito como `~NomeDaClasse()`. O compilador o transforma no método
`Finalize()`, que o **GC** chama antes de coletar o objeto — de forma **não determinística**
(você não sabe quando, nem se rodará antes do processo terminar).

```csharp
public class ComFinalizer
{
    ~ComFinalizer()
    {
        // roda numa thread de finalização, em momento indeterminado
    }
}
```

**O custo é alto:**

1. Objeto com finalizer vai para a **fila de finalização** ao ser alocado.
2. Na primeira coleta, ele **não é liberado** — em vez disso é movido para a fila "pronto pra
   finalizar" e **sobrevive** a essa coleta. Isso o **promove de geração** (gen 0 → gen 1+),
   ou seja, ele vive mais tempo e ocupa memória mais cara de coletar.
3. O finalizer roda numa **thread de finalização separada**, sem ordem garantida entre
   objetos.
4. Só num **ciclo posterior** do GC o objeto é de fato liberado.

Ou seja: um objeto com finalizer precisa de **pelo menos duas coletas** para sumir e escapa de
gen 0. Por isso finalizers são caros e devem ser **raros**.

**Quando (e por que raramente) escrever um:** apenas como **rede de segurança** para um
recurso **não gerenciado direto** — se o usuário esquecer o `Dispose`, o finalizer ainda
libera o handle. **Nunca** coloque lógica de negócio num finalizer, e **nunca** dependa dele
para timing.

**SafeHandle — a alternativa moderna:** em vez de guardar um `IntPtr` cru e escrever um
`~destrutor`, encapsule o handle num tipo derivado de `SafeHandle` (ex.:
`SafeFileHandle`). O `SafeHandle` **já tem** um finalizer crítico próprio, é robusto contra
falhas parciais e resistente a *handle recycling attacks*. Com ele, sua classe **não precisa
de finalizer** — basta implementar `IDisposable` e dar `Dispose` no `SafeHandle`.

```csharp
public sealed class ArquivoSeguro : IDisposable
{
    private readonly SafeFileHandle _handle; // ele mesmo tem o finalizer crítico

    public ArquivoSeguro(string caminho)
        => _handle = File.OpenHandle(caminho);

    public void Dispose() => _handle.Dispose(); // sem ~destrutor necessário
}
```

**Pegadinha:** um finalizer que **toca em campo gerenciado** pode acessar um objeto **já
coletado** (ordem de finalização não é garantida) — por isso o `disposing == false` do padrão
evita mexer em gerenciados. E **lançar exceção** dentro de um finalizer **derruba o processo**.

**Como responder:** "Finalizer é o `~Classe()`, chamado pelo GC de forma não determinística.
É caro: o objeto entra na fila de finalização, sobrevive à primeira coleta e é promovido de
geração. Só escrevo um como rede de segurança pra recurso não gerenciado — e, hoje, quase
sempre uso `SafeHandle`, que já traz o finalizer crítico e me dispensa de escrever um."

---

## 6. IAsyncDisposable e await using

Às vezes a limpeza de um recurso é **assíncrona**: dar *flush* de um buffer para a rede,
fechar uma conexão com handshake, esvaziar um pipeline. Chamar isso de forma síncrona (com
`.Wait()`/`.Result`) bloquearia a thread e pode causar deadlock. Para isso existe o
`IAsyncDisposable`:

```csharp
public interface IAsyncDisposable
{
    ValueTask DisposeAsync();
}
```

Você o consome com **`await using`**: o compilador chama `DisposeAsync()` no fim do escopo e
faz `await` do resultado.

```csharp
public async Task GravarAsync(Stream destino, byte[] dados)
{
    await using var writer = new StreamWriter(destino); // IAsyncDisposable
    await writer.WriteAsync(Encoding.UTF8.GetString(dados));
    // no fim do escopo: await writer.DisposeAsync() — faz o flush async sem bloquear
}
```

**Casos reais:** `Stream`/`StreamWriter` async, pipelines de rede, e o **`DbContext`** do EF
Core, que implementa `IAsyncDisposable` (descartar a conexão do banco de forma assíncrona).

Boas práticas:

- Se a classe implementa **os dois** (`IDisposable` e `IAsyncDisposable`), prefira
  `DisposeAsync` no caminho assíncrono; o `Dispose` síncrono fica como fallback.
- **Não** faça `.Wait()`/`.Result` dentro do `DisposeAsync` — isso reintroduz bloqueio e
  arrisca deadlock.

**Pegadinha:** esquecer o `await` no `await using`. Como `DisposeAsync` retorna `ValueTask`,
sem o `await` você **não espera** a limpeza terminar — o flush pode não completar. `await
using` já cuida disso; o erro é fazer `DisposeAsync()` "na mão" sem `await`.

**Como responder:** "Quando a limpeza precisa ser assíncrona — flush de stream, fechar
conexão de rede, um `DbContext` do EF — implemento `IAsyncDisposable` com `DisposeAsync`
retornando `ValueTask`, e consumo com `await using`, que chama e aguarda o `DisposeAsync` no
fim do escopo, sem bloquear a thread."

---

## 7. Armadilhas práticas: HttpClient, double-dispose e Dispose que engole exceção

### HttpClient — NÃO dê new/dispose por requisição

`HttpClient` **implementa `IDisposable`**, o que induz o júnior a envolvê-lo num `using` a cada
chamada. **Isso é um erro clássico.** Quando você dá `Dispose` no `HttpClient`, o socket
subjacente **não** fecha na hora: ele fica em estado `TIME_WAIT` por um tempo. Criar e
descartar um `HttpClient` por requisição, em volume, esgota as **portas TCP** disponíveis —
*socket/port exhaustion* (`SocketException`).

`HttpClient` foi projetado para ser **reutilizado** (idealmente uma instância de longa vida).
Mas um singleton "na mão" tem outro problema: ele **cacheia o DNS** e não percebe mudanças de
endereço (DNS *stale*). A solução idiomática resolve os dois:

```csharp
// Registro (Program.cs)
builder.Services.AddHttpClient<MeuServico>();

// Uso — o factory injeta um HttpClient já gerenciado
public class MeuServico(HttpClient http)
{
    public Task<string> BuscarAsync(string url) => http.GetStringAsync(url);
}
```

`IHttpClientFactory` mantém um **pool de `HttpMessageHandler`** reutilizados (evita esgotar
sockets) e rotaciona os handlers periodicamente (resolve o DNS *stale*). Você **não** dá
`Dispose` nesse `HttpClient` — o factory cuida do ciclo de vida.

**Como responder:** "`HttpClient` não deve ser criado e descartado por requisição: o socket
fica em `TIME_WAIT` e você esgota as portas (*socket exhaustion*). Ele é feito pra ser
reutilizado. Uso `IHttpClientFactory` (`AddHttpClient`), que gerencia um pool de handlers e
lida com o DNS — sem eu precisar dar `Dispose`."

### Esquecer o Dispose

Se você não dá `Dispose` num recurso não gerenciado e a classe **não tem finalizer**, o
recurso vaza **para sempre** (ou até o processo morrer). Com finalizer, ele vaza até o GC
finalizar — mais tarde e mais caro. Por isso: `using` sempre que possível.

### Double-dispose

Chamar `Dispose()` duas vezes deve ser **no-op** (o campo `_disposed` protege). Um `Dispose`
que explode na segunda chamada é um bug — o contrato exige idempotência.

### Dispose que engole exceção

Um `Dispose` que faz `try { ... } catch { }` **silenciosamente** pode esconder falhas
importantes (ex.: um *flush*/commit que não completou). Por outro lado, **lançar** uma
exceção do `Dispose` quando ele roda dentro do `finally` de um `using` pode **mascarar a
exceção original** do bloco. Regra prática: `Dispose` deve ser barato e não deve lançar em
condições normais; se há uma operação que pode falhar de verdade (flush/commit), faça-a
**explicitamente** antes (ex.: `FlushAsync()` / `SaveChangesAsync()`), não escondida no
`Dispose`.

**Pegadinha (a mais cobrada):** "por que não `new HttpClient()` por chamada?" → socket/port
exhaustion (`TIME_WAIT`) + DNS *stale*, resolvido por `IHttpClientFactory`.

---

## Glossário

- **Recurso gerenciado:** objeto no heap do CLR, gerenciado pelo GC (memória).
- **Recurso não gerenciado:** handle/ponteiro fora do heap do GC (arquivo, socket, conexão de
  banco, handle de OS) — precisa de liberação explícita.
- **Liberação determinística:** liberar o recurso num momento controlado por você (fim do
  `using`), não quando o GC decidir.
- **IDisposable:** interface com `void Dispose()` — o contrato de limpeza explícita.
- **using statement / using declaration:** açúcar que garante `Dispose` via `try/finally`
  (`using (...)`) ou no fim do escopo (`using var`).
- **Dispose Pattern:** `Dispose()` público + `protected virtual Dispose(bool disposing)` +
  campo `_disposed` + `GC.SuppressFinalize(this)`.
- **Finalizer (~destrutor):** `~Classe()` → `Finalize()`, chamado pelo GC de forma não
  determinística; rede de segurança para recurso não gerenciado.
- **GC.SuppressFinalize(this):** remove o objeto da fila de finalização quando o descarte já
  foi explícito, evitando o custo do finalizer.
- **SafeHandle:** wrapper de handle não gerenciado com finalizer crítico embutido; dispensa
  escrever `~destrutor`.
- **IAsyncDisposable / await using:** limpeza assíncrona via `ValueTask DisposeAsync()`.
- **IHttpClientFactory:** fábrica que gerencia um pool de `HttpMessageHandler` para reusar
  `HttpClient` sem esgotar sockets.
- **Socket/port exhaustion:** esgotamento de portas TCP por sockets presos em `TIME_WAIT`.

---

## Checagem de entendimento

1. Por que o GC sozinho não basta para liberar um `FileStream` ou uma `SqlConnection`? Cite a
   diferença entre memória e recurso não gerenciado.
2. O que o compilador gera para um `using (var x = ...) { ... }`? Por que isso torna o
   `Dispose` seguro mesmo com exceção?
3. No Dispose Pattern, para que serve o parâmetro `bool disposing`? O que muda entre `true` e
   `false`?
4. O que `GC.SuppressFinalize(this)` faz e por que você o chama dentro do `Dispose()` público?
5. Cite dois custos concretos de ter um finalizer. Por que `SafeHandle` costuma dispensar
   escrever um `~destrutor`?
6. Por que você **não** deve dar `new HttpClient()` (e `Dispose`) a cada requisição, e qual é a
   solução idiomática?
