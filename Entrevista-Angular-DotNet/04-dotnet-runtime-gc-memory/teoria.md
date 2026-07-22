# Módulo 04 — .NET: Runtime, GC & Memory Management

Este módulo é preparação para entrevista .NET (alvo: **.NET 8 / C# 12**). O foco não é decorar
definições, e sim conseguir **explicar o motor por baixo** — porque é exatamente aí que o
entrevistador cava nuance: gerações do GC, LOH, por que `struct` "vive na stack" (com ressalvas),
como um *memory leak* acontece mesmo existindo um Garbage Collector.

A estratégia de resposta em toda a entrevista é a mesma: **resposta direta primeiro** (uma ou duas
frases que já valem), **depois** o detalhe técnico que mostra senioridade. Onde marcamos
**Pegadinha**, é onde a maioria erra; onde marcamos **Como responder**, é o script para soar sênior.

---

## 1. .NET Framework vs .NET Core vs .NET 5/6/7/8 (e Standard, Mono)

Esta é a pergunta de aquecimento mais comum. Você precisa contar a história curta e as diferenças
concretas.

- **.NET Framework (1.0 → 4.8.x):** o .NET original, **só Windows**, acoplado ao SO, instalado
  globalmente (GAC). Está em **manutenção** — recebe correções de segurança, mas **não ganha
  features novas**. É o "legado".
- **.NET Core (1.0 → 3.1):** reescrita do zero, **cross-platform** (Windows, Linux, macOS),
  **open source**, **modular** (você referencia só os pacotes NuGet que usa), **alta performance**
  e deploy self-contained. É a base do .NET moderno.
- **.NET 5 e em diante (5, 6, 7, 8...):** a partir do 5, a Microsoft **dropou o "Core" do nome** —
  virou "**só .NET**". Foi a **unificação**: uma base única de runtime/BCL que atende desktop, web,
  cloud, mobile (via MAUI) e IoT. Numeração anual: **pares são LTS** (6, 8 têm 3 anos de suporte);
  ímpares são STS (18 meses). **.NET 8 é LTS.**
- **.NET Standard:** **não é um runtime** — é uma **especificação de API**, um contrato. Uma
  biblioteca que mira `netstandard2.0` roda tanto em .NET Framework quanto em .NET Core/5+. Hoje
  importa quase só para **suportar Framework legado**; código novo que só roda em .NET 6+ mira o TFM
  do runtime (`net8.0`) direto.
- **Mono / Xamarin:** implementação **alternativa** do runtime, historicamente para mobile e Unity.
  No .NET 6+ o Xamarin foi absorvido no **MAUI** e o runtime Mono passou a fazer parte do .NET
  unificado (é o runtime usado no Blazor WebAssembly e mobile).

**Pegadinha:** dizer só "Core é mais novo". O entrevistador quer os **eixos concretos**:
cross-platform, open source, modular/NuGet, performance, e que **Framework é fim de linha**. E não
confundir **.NET Standard** (contrato de API) com um runtime.

**Como responder:**
> ".NET Framework é o legado, só Windows, em manutenção. .NET Core foi a reescrita cross-platform,
> open source, modular e mais performática. A partir do .NET 5 caiu o 'Core' do nome e virou 'só
> .NET', unificando tudo numa base só — .NET 8 é o LTS atual. .NET Standard não é um runtime, é um
> contrato de API pra uma lib rodar nos dois mundos, e hoje só importa pra suportar Framework
> legado. Migro pra .NET moderno por cross-platform, performance e por Framework não receber mais
> features."

---

## 2. CLR/CoreCLR, IL, JIT e código gerenciado

Aqui você mostra que entende o que acontece **entre** escrever C# e a CPU executar.

- **CLR (Common Language Runtime)** — no .NET moderno é o **CoreCLR** — é a máquina virtual do .NET:
  gerencia **memória e Garbage Collection**, **exceções**, **segurança de tipos** e hospeda o
  **JIT**.
- **IL (Intermediate Language, ou CIL/MSIL):** o compilador C# (**Roslyn**) **não gera código de
  máquina** no build. Gera **IL**, um bytecode independente de CPU, empacotado no **assembly**
  (`.dll`/`.exe`) junto com metadados.
- **JIT (Just-In-Time):** em tempo de execução, o JIT compila o IL para **código de máquina nativo**
  — **método a método, na primeira vez que cada método é chamado**. O resultado fica em cache para
  as chamadas seguintes.
- **Código gerenciado vs unmanaged:** *gerenciado* é o que roda **sob o CLR** — ganha GC, type
  safety, verificação. *Unmanaged* é código nativo fora do CLR (C/C++, chamadas via **P/Invoke**,
  ponteiros em bloco `unsafe`); o CLR não gerencia sua memória.
- **AOT / ReadyToRun (visão rápida):** compilam IL para nativo **antes** de rodar. **ReadyToRun**
  pré-compila parte do código para reduzir o custo do JIT no startup. **Native AOT** gera um binário
  totalmente nativo **sem JIT** — startup instantâneo e pegada menor, ideal para **serverless e
  containers** (custo: menos reflection/dinamismo).

**Pegadinha:** dizer que C# é "interpretado" ou que "compila direto pra nativo no build". Nenhum dos
dois: é **IL no build, JIT em runtime** (ou AOT, se você optar).

**Como responder:**
> "O compilador C# gera IL, um bytecode independente de plataforma, dentro do assembly. Em runtime,
> o JIT do CLR compila esse IL pra código de máquina nativo, método a método, na primeira chamada.
> Código gerenciado roda sob o CLR com GC e type safety; unmanaged é nativo, sem GC. Se quero
> startup rápido em container, uso Native AOT, que pré-compila tudo pra nativo sem JIT."

---

## 3. Stack vs Heap, value types vs reference types, string

O par de conceitos mais cobrado — e onde imprecisão custa caro.

- **Value type** (`struct`, `int`, `bool`, `enum`, `DateTime`, `Guid`): a variável **guarda o valor
  direto**. **Cópia copia o conteúdo** (semântica de valor) — mexer na cópia não afeta o original.
- **Reference type** (`class`, `string`, arrays, delegates): a variável guarda uma **referência**
  (ponteiro) para um objeto **no heap**. **Cópia copia a referência** — duas variáveis, **um único
  objeto**; mexer por uma enxerga pela outra.

```csharp
struct Ponto { public int X; }           // value type
class  Caixa { public int X; }            // reference type

var p1 = new Ponto { X = 1 };
var p2 = p1;  p2.X = 99;                   // p1.X continua 1  (cópia de valor)

var c1 = new Caixa { X = 1 };
var c2 = c1;  c2.X = 99;                   // c1.X agora é 99  (mesma referência)
```

- **Stack vs Heap (regra prática de entrevista):** uma **variável local de value type** vive na
  **stack**; um objeto de **class** vive no **heap gerenciado**. A stack é rápida, LIFO, liberada
  automaticamente ao sair do método; o heap é gerenciado pelo **GC**.
- **A ressalva que importa:** um value type **não vive sempre na stack**. Se ele é **campo de uma
  class**, ele mora **no heap junto com o objeto**; se é capturado por uma **closure** ou sofre
  **boxing**, também vai pro heap. Ou seja: **onde a variável mora** decide, não só o tipo.
- **string:** é **reference type**, mas **imutável**. Toda "alteração" (`+`, `Replace`, etc.) cria
  **uma nova string** — a original fica intocada. Por isso concatenar em loop gera lixo:

```csharp
// ruim: N strings intermediárias no heap → pressão no GC
var s = "";
for (int i = 0; i < 1000; i++) s += i;

// bom: um buffer mutável
var sb = new StringBuilder();
for (int i = 0; i < 1000; i++) sb.Append(i);
```

**Pegadinha:** afirmar "**struct sempre vive na stack**". É **impreciso** — depende de onde a
variável está (campo de classe, boxed, capturada por closure → heap). A frase certa é "**value type
como variável local vive na stack**".

**Como responder:**
> "Value type guarda o valor e tem semântica de cópia por valor; reference type guarda uma
> referência pro objeto no heap, e copiar copia só a referência. Como regra, value type local fica
> na stack e objeto de class no heap — mas value type dentro de uma class vai pro heap junto, então
> 'struct sempre na stack' é impreciso. E string é reference type imutável: por isso uso
> StringBuilder pra concatenar em loop."

---

## 4. Boxing e unboxing

Custo escondido de performance — pergunta clássica de "otimização".

- **Boxing:** **empacotar um value type dentro de um objeto no heap** para tratá-lo como `object`
  (ou uma interface). **Aloca** no heap e **copia** o valor pra dentro da "box".
- **Unboxing:** extrair o value type de volta da box — exige **cast explícito** e checa o tipo em
  runtime (`InvalidCastException` se o tipo não bater).

```csharp
int n = 42;
object o = n;        // BOXING: aloca no heap, copia 42
int back = (int)o;   // UNBOXING: cast + cópia de volta
```

- **Custo:** cada boxing é **uma alocação no heap** + cópia → **pressão no GC**. Em **loops quentes**
  ou coleções grandes, vira gargalo real.
- **Onde acontece escondido:** coleções **não-genéricas** (`ArrayList`, `Hashtable`) que guardam
  `object`; `object.Equals`/`GetHashCode` num value type; interpolação/`string.Format` com value
  types; chamar método de **interface** através de uma variável do tipo da interface num struct.
- **Como evitar:** **generics** — `List<int>` guarda `int` sem boxing porque `T` é resolvido para o
  tipo concreto. Além disso: `Span<T>`, evitar `object`/interface no caminho quente, usar structs com
  cuidado.

```csharp
var lista = new List<int>();  lista.Add(42);   // SEM boxing
var arr   = new ArrayList();  arr.Add(42);     // COM boxing (guarda object)
```

**Pegadinha:** achar que `List<int>` faz boxing. **Não faz** — o ponto todo dos generics é evitá-lo.
Quem faz é `ArrayList`/`Hashtable`. Saber essa diferença é o que o entrevistador procura.

**Como responder:**
> "Boxing é empacotar um value type num objeto no heap pra tratá-lo como object; unboxing é tirar de
> volta com cast. O custo é uma alocação no heap por operação, que pressiona o GC — vira gargalo em
> loop quente. Evito com generics: List<int> não faz boxing, ArrayList faz. Também cuido de Equals,
> interpolação e chamadas de interface em structs."

---

## 5. Garbage Collector: reachability, mark-sweep-compact

O coração do módulo. Aqui você explica **por que** existe e **como** decide.

- **Por que existe:** o .NET tem **memória gerenciada** — você **não chama `free()`**. O GC libera
  automaticamente o que **não é mais alcançável**, eliminando classes inteiras de bug (leaks de
  esquecimento, *dangling pointers*, double-free).
- **Como decide o que coletar — alcançabilidade (reachability):** o GC parte das **raízes (GC
  roots)** e marca tudo que consegue alcançar por referências. Raízes são: **variáveis locais na
  stack** (e registradores) dos métodos em execução, **campos `static`**, e **handles do GC**
  (ex.: `GCHandle`). Tudo que **não** é alcançável a partir de nenhuma raiz é **lixo**.
- **Ciclo mark-sweep-compact:**
  1. **Mark:** percorre o grafo a partir das raízes e **marca** os objetos vivos.
  2. **Sweep:** o que **não** foi marcado é lixo — sua memória é recuperada.
  3. **Compact:** os objetos vivos são **movidos** para ficarem contíguos, desfragmentando o heap.
     Como os objetos se movem, o GC **atualiza as referências** para os novos endereços.
- **Não-determinismo:** você **não controla quando** o GC roda (depende de pressão de memória,
  alocações, etc.). Existe `GC.Collect()`, mas **quase nunca** deve ser chamado em produção — atrapalha
  a heurística do runtime.
- **Alcançável ≠ "em uso":** um objeto ainda **referenciado** (por um `static`, um event handler, um
  cache) **não é coletado**, mesmo que seu código nunca mais vá usá-lo. Essa distinção é a **raiz de
  quase todo leak em .NET** (ver seção 7).

**Pegadinha:** dizer que o GC usa **contagem de referência**. **Não usa** — isso é COM/Python. O GC
do .NET é por **rastreamento de alcançabilidade (tracing)**, então **ciclos de referência** (A → B →
A) **são coletados** normalmente se ninguém de fora os alcança.

**Como responder:**
> "O GC existe porque a memória é gerenciada: eu não dou free, ele libera o que não é mais
> alcançável. Ele parte das raízes — locais na stack, statics, handles — e marca tudo que alcança;
> o que não marcou é lixo (sweep), e ele compacta os vivos pra desfragmentar, atualizando as
> referências. É não-determinístico e uso tracing, não contagem de referência, então ciclos são
> coletados. O perigo é que 'alcançável' não é 'em uso' — um static ou event handler segurando o
> objeto impede a coleta e vira leak."

---

## 6. Gerações 0/1/2, LOH, workstation vs server, background GC

O detalhe fino que separa júnior de sênior.

- **Por que gerações — a hipótese geracional:** empiricamente, **a maioria dos objetos morre
  jovem** (variáveis temporárias, DTOs de request). Então, em vez de varrer o heap inteiro toda vez,
  o GC particiona por idade e coleta principalmente a **Gen0** — **barato e frequente**, recuperando
  a maior parte do lixo com pouco trabalho.
- **As gerações:**
  - **Gen0:** objetos **recém-alocados**. Coleta **rápida e frequente**.
  - **Gen1:** **buffer** — objetos que sobreviveram a uma coleta de Gen0.
  - **Gen2:** objetos **longevos** (sobreviveram várias coletas). Coleta **cara e rara**.
  - Regra: **sobreviveu a uma coleta → é promovido** para a geração seguinte.
- **LOH (Large Object Heap):** objetos **>= ~85.000 bytes** (~85 KB) vão para um heap separado. Ele
  é **logicamente Gen2** (só é coletado em GC de Gen2) e **não é compactado por padrão** — mover
  objetos grandes é caro, então o runtime evita, ao custo de **fragmentação**. Dá pra forçar
  compactação pontual com `GCSettings.LargeObjectHeapCompactionMode = GCLargeObjectHeapCompactionMode.CompactOnce`.
- **Workstation vs Server GC:**
  - **Workstation** (padrão em apps client/desktop): otimiza **latência/responsividade**, um heap.
  - **Server** (padrão comum em ASP.NET Core no servidor): **múltiplos heaps e threads de GC, um por
    CPU lógica**, otimiza **throughput** em máquinas multi-core.
- **Background / concurrent GC:** coleta a **Gen2** em **thread(s) separada(s)**, em paralelo com o
  app, minimizando as pausas **"stop-the-world"**. É o padrão moderno.

**Pegadinha:** achar que existem "Gen3, Gen4...". **Gen2 é o teto.** E: **coletar Gen2 é um full GC**
— implica coletar **Gen0 e Gen1 juntas**. Também: **~85 KB é o limiar do LOH**, não "objeto grande é
qualquer array de mil itens".

**Como responder:**
> "Existem gerações por causa da hipótese geracional: a maioria dos objetos morre jovem, então
> coletar só a Gen0, que é barato e frequente, já recupera quase todo o lixo. Gen0 é o novo, Gen1 é
> um buffer, Gen2 são os longevos — sobreviveu, é promovido. Objetos com 85 KB ou mais vão pro LOH,
> que é Gen2 e por padrão não compacta, então cuida com fragmentação. Server GC usa um heap por CPU
> pra throughput; workstation otimiza latência. E o background GC coleta a Gen2 em paralelo pra
> reduzir pausa."

---

## 7. Memory leaks em código gerenciado

Sim, **existem leaks com GC** — e explicar *por quê* impressiona.

O GC **nunca coleta o que ainda é alcançável**. Um *leak* gerenciado é justamente isso: um objeto
que você **deixou de usar mas continua referenciado** por alguma raiz viva. O GC não tem como saber
que você "não vai mais usar" — só que ainda dá pra alcançá-lo.

**Causas clássicas (o entrevistador quer pelo menos duas):**

- **Event handlers / delegates não removidos.** Ao fazer `publisher.Evento += handler`, o
  **publisher passa a referenciar o subscriber**. Se o publisher vive muito (ex.: é um serviço
  singleton) e você **não faz `-=`**, o subscriber **nunca é coletado**. É o caso mais citado.

```csharp
longLived.OnTick += obj.Handler;   // longLived agora segura obj
// ...esqueceu do -= → obj nunca é coletado enquanto longLived viver
longLived.OnTick -= obj.Handler;   // a correção
```

- **Referências `static`** que só crescem (uma `static List`/`Dictionary` usada como cache
  improvisado). Raiz permanente → nada ali é coletado.
- **Caches sem limite/eviction:** um dicionário que só adiciona e nunca remove/expira cresce para
  sempre. Use `MemoryCache` com política de expiração ou limite de tamanho.
- **Closures capturando objetos:** uma lambda mantém **vivas as variáveis que captura**; se essa
  lambda é assinada a um evento/timer de vida longa, prende o que capturou.
- **Timers e subscriptions não cancelados** (`System.Threading.Timer`, `IObservable`, conexões) —
  a fonte contínua segura o callback.
- **`IDisposable` não liberado** (**ponte pro módulo 05**): aqui o problema é diferente — não é o
  heap gerenciado, é o **recurso unmanaged** (arquivo, socket, conexão de banco) que **o GC não
  libera no tempo certo**. Não chamar `Dispose()`/não usar `using` **segura recursos escassos**.

**Como diagnosticar (visão rápida):**
- **`dotnet-counters`:** monitora em tempo real — tamanho das gerações, taxa de alocação, tempo em
  GC. Se o **heap sobe e nunca desce**, há suspeita de leak.
- **`dotnet-gcdump` / `dotnet-dump`:** tiram um **dump** do heap; você analisa **quem retém** o
  objeto (o **caminho de raiz / GC root path**) para achar a referência culpada.

**Pegadinha:** responder "não existe leak em .NET porque tem GC". **Errado** — existe, e o mecanismo
é sempre o mesmo: **algo ainda alcançável**. O exemplo de ouro é o **event handler sem `-=`**.

**Como responder:**
> "Existe leak em .NET, sim. O GC só coleta o que não é mais alcançável, então basta você deixar de
> usar um objeto mas mantê-lo referenciado. O caso clássico é event handler: += sem -= faz o
> publisher segurar o subscriber pra sempre. Outros: static que só cresce, cache sem eviction,
> closure capturando objeto, e IDisposable não liberado, que segura recurso unmanaged. Diagnostico
> com dotnet-counters pra ver o heap subir e um gcdump pra achar quem retém a referência."

---

## 8. Span<T>, Memory<T> e stackalloc

Onde a entrevista de **performance** vai — reduzir alocação no heap.

- **`Span<T>`:** uma **view (janela) sobre memória contígua** — um array, uma `string`, um buffer de
  `stackalloc` ou memória unmanaged — **sem copiar**. Fatiar, parsear e percorrer **sem alocar novos
  arrays**:

```csharp
ReadOnlySpan<char> texto = "2026-07-21";
ReadOnlySpan<char> ano   = texto.Slice(0, 4);   // "2026" SEM alocar nova string
int a = int.Parse(ano);
```

- **É um `ref struct`:** **só pode viver na stack** — **não pode** ser campo de classe, nem ir pro
  heap, nem ser usado através de `object`/interface, nem **em métodos `async`** ou blocos com
  `await`/`yield`. Essa restrição é justamente o que o torna **barato e seguro** (o compilador
  garante que ele não sobrevive além do escopo).
- **`Memory<T>`:** o "primo" que **pode viver no heap**, ser **campo** e ser usado em **`async`**.
  Quando você precisa da view contígua, chama **`.Span`**. **Use `Memory<T>` quando `Span<T>` não
  cabe** — tipicamente em código assíncrono.
- **`stackalloc`:** aloca um buffer **na stack**, **não no heap gerenciado** → **zero pressão no
  GC**. Ótimo para buffers pequenos e de vida curta. Cuidados: **tamanho** (buffer grande → *stack
  overflow*) e **escopo** (não deixa a memória escapar do método). Combina naturalmente com `Span<T>`:

```csharp
Span<byte> buffer = stackalloc byte[128];   // na stack, sem tocar o GC
// ...usa buffer para montar/parsear algo curto...
```

- **Por que cai em entrevista de performance:** menos alocações no heap → **menos trabalho pro GC**
  → **menos pausas e mais throughput** em caminho quente (parsing, serialização, hot loops). É o
  vocabulário que aparece em código de alto desempenho no .NET moderno.

**Pegadinha:** tentar usar `Span<T>` **em método `async`** ou **como campo de classe** — **não
compila**, porque é `ref struct`. **Se precisar disso, é `Memory<T>`.**

**Como responder:**
> "Span<T> é uma view sobre memória contígua — array, string, stackalloc — que deixa fatiar e
> parsear sem alocar novos objetos, reduzindo pressão no GC. É um ref struct, então só vive na
> stack: não pode ser campo nem ir pra método async. Quando preciso disso, uso Memory<T>, que vive
> no heap e me dá .Span quando preciso da view. E stackalloc aloca um buffer na stack, sem tocar o
> GC — uso pra buffers pequenos em caminho quente."

---

## Glossário

- **CLR / CoreCLR** — a máquina virtual do .NET: GC, JIT, exceções, type safety. CoreCLR é a
  implementação no .NET moderno.
- **IL (CIL/MSIL)** — bytecode independente de CPU gerado pelo compilador C#, dentro do assembly.
- **JIT** — compilador Just-In-Time: transforma IL em código nativo em runtime, método a método.
- **AOT / ReadyToRun / Native AOT** — compilação antecipada de IL para nativo (menos/zero JIT).
- **Código gerenciado / unmanaged** — sob o CLR (com GC) vs nativo fora do CLR.
- **Value type / reference type** — guarda o valor (cópia por valor) vs guarda referência (cópia da
  referência).
- **Stack / Heap** — memória LIFO liberada ao sair do método vs memória gerenciada pelo GC.
- **Boxing / unboxing** — empacotar value type num objeto no heap vs extrair de volta com cast.
- **GC roots / alcançabilidade** — variáveis locais, statics, handles; o que é alcançável a partir
  delas está vivo.
- **Mark-sweep-compact** — marcar vivos, recuperar o não-marcado, compactar os vivos.
- **Gerações 0/1/2** — partição por idade do objeto (hipótese geracional). Gen2 é o teto.
- **LOH** — Large Object Heap: objetos >= ~85 KB, Gen2, não compactado por padrão.
- **Workstation / Server GC** — otimiza latência (um heap) vs throughput (um heap por CPU).
- **Background / concurrent GC** — coleta Gen2 em thread separada para reduzir pausas.
- **Memory leak gerenciado** — objeto ainda alcançável que você não usa mais (ex.: event handler sem
  `-=`).
- **Span<T> / Memory<T> / stackalloc** — view sem cópia (ref struct, só stack) / view heap-friendly
  (async) / buffer na stack.

---

## Checagem de entendimento

1. Em uma frase para o entrevistador: qual é a diferença entre **.NET Framework** e **.NET
   Core/.NET 8**, e o que é **.NET Standard**?
2. Descreva a cadeia **C# → IL → JIT → nativo**. O que significa "**código gerenciado**"?
3. Por que dizer "**struct sempre vive na stack**" é impreciso? Dê um caso em que um value type vai
   pro heap.
4. O que é **boxing**, qual o custo, e por que `List<int>` **não** faz boxing mas `ArrayList` **faz**?
5. Explique o ciclo **mark-sweep-compact** e por que **ciclos de referência não vazam** no .NET.
6. Por que existem **gerações**? O que é o **LOH**, o limiar de **~85 KB** e por que ele **não
   compacta** por padrão?
7. **Existe memory leak em .NET?** Dê o exemplo do **event handler** e diga como você o
   **diagnosticaria**.
8. Quando você usaria **`Span<T>`** e quando teria que trocar por **`Memory<T>`**?
