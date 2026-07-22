# Módulo 06 — .NET: DI, Service Lifetimes & Repository

Este é um dos módulos que **mais cai** em entrevista .NET de nível pleno/sênior. O container de
Injeção de Dependência é o coração do ASP.NET Core moderno, os **service lifetimes** são a pergunta
que separa quem "usa o framework" de quem "entende o framework", e o **Repository Pattern** é onde o
candidato pleno decora a receita e o sênior mostra maturidade — sabe usar **e** sabe criticar.

O objetivo aqui é você conseguir, em voz alta e com exemplo:

1. Explicar o que é DI, e diferenciar **DI** (técnica), **IoC** (conceito) e **DIP** (princípio SOLID).
2. Explicar os três lifetimes — **Transient**, **Scoped**, **Singleton** — e **quando** usar cada um.
3. Explicar a armadilha da **captured dependency** (Scoped dentro de Singleton) e como resolvê-la.
4. Explicar o **Repository Pattern** e o **Unit of Work**, e — o pulo do gato — **quando NÃO usar** com EF Core.

Alvo: **.NET 8 / C# 12**, `Microsoft.Extensions.DependencyInjection`, ASP.NET Core, EF Core.

---

## 1. DI: o que é, IoC, container embutido e constructor injection

**Injeção de Dependência (DI)** é uma técnica em que uma classe **recebe** suas dependências de fora,
em vez de **criá-las** ela mesma com `new`. Em vez de a classe decidir qual implementação usar, alguém
de fora (o container) entrega tudo pronto.

**IoC (Inversão de Controle)** é o **conceito** por trás disso: em código tradicional, seu código
controla o fluxo e cria os objetos que precisa. Com IoC, você **inverte** esse controle — quem
constrói os objetos e chama seu código é o framework. DI é a forma mais comum de aplicar IoC.

**Por que fazer isso?**
- **Desacoplamento:** a classe depende de uma **interface** (`IEmailSender`), não de uma classe
  concreta (`SmtpEmailSender`). Trocar a implementação não mexe na classe consumidora.
- **Testabilidade:** no teste, você injeta um **fake/mock** da interface. Se a classe fizesse
  `new SmtpEmailSender()` internamente, seria impossível testar sem enviar e-mail de verdade.

**O container embutido** do .NET tem duas peças:
- **`IServiceCollection`** — onde você **registra** os serviços, na inicialização da app.
- **`IServiceProvider`** — quem **resolve** (constrói) os serviços em runtime, montando o grafo inteiro.

```csharp
// Program.cs — REGISTRO (na inicialização)
builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddSingleton<IClock, SystemClock>();
builder.Services.AddTransient<IEmailSender, SmtpEmailSender>();

// CONSTRUCTOR INJECTION — a forma padrão de RESOLVER
public class UserService
{
    private readonly IUserRepository _repo;
    private readonly IEmailSender _email;

    // O container preenche o construtor automaticamente,
    // resolvendo recursivamente TODO o grafo de dependências.
    public UserService(IUserRepository repo, IEmailSender email)
    {
        _repo = repo;
        _email = email;
    }
}
```

Você também pode resolver manualmente com `provider.GetRequiredService<IUserService>()`, mas em
ASP.NET Core o normal é o framework injetar via construtor (controllers, minimal APIs, outros serviços).

**Pegadinha:** dar `new SqlUserRepository()` dentro do `UserService` **anula** o DI: a classe volta a
estar acoplada à implementação concreta e não dá mais pra testar isoladamente nem trocar a fonte de
dados. Se você faz `new` de uma dependência com lógica, é cheiro de que ela deveria ser injetada.

**Como responder:** "DI é entregar as dependências prontas de fora, tipicamente pelo construtor, em
vez de a classe criá-las com `new`. É a técnica que aplica IoC. Ganho: desacoplamento — dependo da
interface — e testabilidade — no teste injeto um mock. No .NET, registro no `IServiceCollection` e o
`IServiceProvider` resolve o grafo em runtime."

---

## 2. DI vs IoC vs DIP (o princípio SOLID)

Três termos parecidos que o entrevistador adora ver você **separar**:

- **IoC (Inversão de Controle)** — o **conceito** guarda-chuva. Inverter quem controla o fluxo e a
  criação de objetos: o framework chama seu código, não o contrário. DI é um caso de IoC (há outros,
  como o padrão Template Method ou eventos).
- **DI (Injeção de Dependência)** — a **técnica** específica de IoC: entregar as dependências prontas
  de fora (via construtor, geralmente). É como você faz IoC acontecer para dependências.
- **DIP (Princípio da Inversão de Dependência)** — o **"D" do SOLID**, um **princípio de design**:
  módulos de alto nível não devem depender de módulos de baixo nível; **ambos devem depender de
  abstrações**. E abstrações não devem depender de detalhes.

A relação: o **DIP** diz *"dependa de abstrações (interfaces)"*. A **DI** é *como* você satisfaz essa
regra na prática — o container injeta a implementação concreta por trás da interface. O **IoC** é o
conceito amplo que dá nome à ideia de inverter o controle.

```csharp
// DIP aplicado: UserService (alto nível) depende de uma ABSTRAÇÃO...
public class UserService(IUserRepository repo) { /* ... */ }

// ...e a implementação concreta (baixo nível) também depende da mesma abstração.
public class SqlUserRepository : IUserRepository { /* ... */ }

// DI é o que "cola" tudo: o container injeta SqlUserRepository onde se pede IUserRepository.
services.AddScoped<IUserRepository, SqlUserRepository>();
```

**Pegadinha:** dizer "DI e IoC são a mesma coisa" ou "DI é o mesmo que DIP". São coisas diferentes:
DIP é a regra, DI é a técnica que a cumpre, IoC é o guarda-chuva conceitual.

**Como responder:** "IoC é o conceito de inverter o controle da criação/fluxo pro framework. DI é uma
técnica de IoC: injetar dependências de fora. DIP é o princípio SOLID que manda depender de abstrações,
não de concretos. Na prática: DIP é a regra, DI é como eu a aplico, e o container de IoC é a ferramenta."

---

## 3. Lifetime Transient

**Transient** significa que o container cria uma **instância nova a cada resolução**. Toda vez que o
serviço é pedido — seja injetado num construtor, seja resolvido manualmente — você recebe um objeto
novo.

```csharp
services.AddTransient<IEmailSender, SmtpEmailSender>();
```

Se num mesmo request três serviços diferentes pedem `IEmailSender`, são criadas **três instâncias**
distintas de `SmtpEmailSender`.

**Quando usar:**
- Serviços **leves, sem estado** e **baratos de criar**: validadores, mappers, formatadores, geradores.
- Quando cada consumidor deve ter sua própria cópia limpa, sem risco de estado compartilhado.

**Pegadinha:** um Transient injetado **dentro de um Singleton** é criado **uma única vez** — ele fica
"preso" à vida do Singleton e, na prática, vive tanto quanto ele. Transient não garante "sempre novo"
se quem o segura é longevo. (Isso é uma variação da captured dependency — ver seção 6.)

**Como responder:** "Transient é uma instância nova a cada resolução. Uso pra serviços sem estado,
leves e baratos — um validador, um mapper. É o default mais seguro quando não preciso compartilhar
nada. Só tomo cuidado: se um Singleton injeta um Transient, o Transient vira efetivamente Singleton."

---

## 4. Lifetime Scoped

**Scoped** significa **uma instância por escopo**. No ASP.NET Core, **cada request HTTP** abre um
**escopo** (um `IServiceScope`), e todos os serviços Scoped resolvidos **dentro daquele request**
compartilham a **mesma instância**. Em outro request, é outra instância. No fim do request, o
framework faz `Dispose` do escopo (e dos serviços descartáveis nele).

```csharp
services.AddScoped<IUserRepository, UserRepository>();

// EF Core: AddDbContext registra o DbContext como Scoped por padrão.
services.AddDbContext<AppDbContext>(o => o.UseSqlServer(cs));
```

**O que é um "escopo"?** É o `IServiceScope`: uma fronteira de tempo de vida. O middleware do ASP.NET
Core abre um por request no início e o descarta no fim. Fora de um request (ex.: num background service
Singleton) **não há escopo automático** — você precisa criar um manualmente (ver seção 6).

**Por que o DbContext é Scoped?** Dois motivos centrais:
1. **Não é thread-safe.** Um `DbContext` não pode ser usado por duas threads ao mesmo tempo. Como cada
   request costuma rodar numa thread por vez, "um DbContext por request" evita uso concorrente.
2. **Change tracker por unidade de trabalho.** O DbContext rastreia as entidades carregadas/alteradas.
   Um request = uma unidade de trabalho; ter o **mesmo** DbContext em todos os serviços daquele request
   faz o rastreamento e o `SaveChanges` funcionarem de forma coerente. Compartilhar entre requests
   misturaria unidades de trabalho e vazaria entidades rastreadas de um request no outro.

**Pegadinha:** Scoped **não** é "por chamada de método" nem "por classe" — é **por escopo**. Em web, é
por request. Se você reusa a app fora de um request (background job, console), precisa abrir o escopo
você mesmo, senão não há escopo pra resolver um Scoped.

**Como responder:** "Scoped é uma instância por escopo; em ASP.NET Core cada request HTTP é um escopo,
então é uma instância por request, compartilhada entre os serviços daquele request. O DbContext é
Scoped por isso: não é thread-safe e o change tracker representa a unidade de trabalho do request."

---

## 5. Lifetime Singleton

**Singleton** significa **uma única instância para toda a aplicação**. O container cria uma vez (na
primeira resolução, ou na inicialização se você registrar uma instância) e reutiliza para **todos os
requests e todas as threads** pelo tempo de vida da app.

```csharp
services.AddSingleton<IClock, SystemClock>();
services.AddSingleton<IMemoryCache, MemoryCache>();
```

**Quando usar:**
- Estado **imutável** ou configuração carregada uma vez.
- Caches, clientes reutilizáveis e caros de criar, componentes sem estado mutável por request.

**O grande perigo — thread-safety e estado compartilhado:** como a **mesma** instância é usada por
**vários requests simultâneos em threads diferentes**, qualquer **estado mutável** dentro de um
Singleton precisa ser **thread-safe**.

```csharp
// PERIGOSO: Dictionary mutável num Singleton, sem sincronização.
public class ContadorService // registrado como Singleton
{
    private readonly Dictionary<string, int> _hits = new();
    public void Registrar(string chave) => _hits[chave]++; // RACE CONDITION sob concorrência!
}

// SEGURO: use uma estrutura concorrente (ou lock).
public class ContadorService
{
    private readonly ConcurrentDictionary<string, int> _hits = new();
    public void Registrar(string chave) => _hits.AddOrUpdate(chave, 1, (_, v) => v + 1);
}
```

**Pegadinha:** guardar dados "de um usuário" ou "do request atual" num Singleton **vaza entre
usuários/requests**, porque a instância é a mesma pra todo mundo. Estado por request é papel do Scoped,
não do Singleton.

**Como responder:** "Singleton é uma instância pra app inteira, compartilhada entre todos os requests
e threads. Uso pra estado imutável, cache, config. O cuidado é thread-safety: qualquer estado mutável
precisa de `lock` ou de uma coleção concorrente, senão dá race condition. E nunca guardo estado de
request nele — isso vaza entre usuários."

---

## 6. A armadilha da "captured dependency" (Scoped dentro de Singleton)

Este é **o** bug clássico de DI e uma pergunta favorita em entrevista.

**O problema:** você injeta um serviço **Scoped** (ou Transient) no **construtor de um Singleton**. Como
o Singleton é criado **uma vez** e segura suas dependências pra sempre, aquele Scoped é resolvido **uma
única vez** e fica **capturado** — vira, na prática, um **Singleton**. Ele para de respeitar o próprio
lifetime.

```csharp
// BUG: DbContext (Scoped) capturado por um Singleton.
public class CacheAquecedor // registrado como Singleton
{
    private readonly AppDbContext _db; // Scoped, mas capturado -> vira Singleton!
    public CacheAquecedor(AppDbContext db) => _db = db;
}
```

**Por que é grave:**
- O `AppDbContext` fica **compartilhado entre TODOS os requests** — mas ele **não é thread-safe**.
  Requests concorrentes usam o mesmo DbContext ao mesmo tempo → exceções, dados corrompidos, change
  tracker acumulando entidades pra sempre (vazamento de memória).
- O `Dispose` por request nunca acontece: o Scoped foi arrancado do seu ciclo de vida.

**Como o ASP.NET Core te protege:** o **validador de escopo** (`ValidateScopes`), **ligado por padrão
em ambiente de Development**, detecta esse erro e lança `InvalidOperationException` ("Cannot consume
scoped service ... from singleton ...") ao resolver o grafo. É por isso que o bug costuma estourar
cedo — o framework recusa a montagem.

**A correção — `IServiceScopeFactory`:** o Singleton **não** injeta o Scoped diretamente. Ele injeta o
`IServiceScopeFactory` e, **a cada operação**, cria um **escopo próprio**, resolve o Scoped **dentro**
dele e descarta o escopo ao terminar.

```csharp
public class CacheAquecedor // Singleton, agora correto
{
    private readonly IServiceScopeFactory _scopeFactory;
    public CacheAquecedor(IServiceScopeFactory scopeFactory) => _scopeFactory = scopeFactory;

    public async Task AquecerAsync()
    {
        // Cria um escopo por operação; o DbContext vive só o tempo desse using.
        using var scope = _scopeFactory.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var itens = await db.Produtos.AsNoTracking().ToListAsync();
        // ... usa itens ...
    } // Dispose do escopo -> Dispose do DbContext
}
```

**Regra de ouro:** *a vida de uma dependência nunca pode ser MENOR que a de quem a injeta.* Singleton
pode injetar Singleton. Scoped pode injetar Scoped ou Singleton. Um Singleton **não** injeta Scoped
nem Transient com estado — cria um escopo sob demanda.

**Pegadinha:** "então nunca posso usar Scoped num Singleton?" Pode — só não por **injeção direta no
construtor**. Você usa `IServiceScopeFactory` pra criar um escopo curto por operação.

**Como responder:** "Injetar um Scoped no construtor de um Singleton é a captured dependency: o Scoped
é resolvido uma vez e vira efetivamente Singleton. Com DbContext isso é grave — vira um DbContext
compartilhado entre requests, não é thread-safe e vaza o change tracker. O validador de escopo do
ASP.NET Core pega isso em Development. A correção é injetar `IServiceScopeFactory` e criar um escopo por
operação. A regra: a vida da dependência não pode ser menor que a de quem injeta."

---

## 7. Repository Pattern e Unit of Work

**Repository Pattern** é **abstrair o acesso a dados atrás de uma interface**. O restante do código
fala com `IUserRepository` e **não conhece** se por trás há SQL Server, Mongo, um arquivo ou uma lista
em memória.

**Motivação:**
- **Testabilidade:** mockar `IUserRepository` no teste, sem tocar em banco.
- **Trocar a fonte de dados:** mudar a implementação sem mexer na regra de negócio.
- **Centralizar queries:** ter um lugar só para as consultas de uma entidade, evitando SQL/LINQ espalhado.

```csharp
public interface IUserRepository
{
    Task<User?> GetByIdAsync(int id);
    Task<IReadOnlyList<User>> GetActiveAsync();
    void Add(User user);
    void Remove(User user);
}
```

**Repositório genérico** — para reduzir repetição entre entidades, um `IRepository<T>`:

```csharp
public interface IRepository<T> where T : class
{
    Task<T?> GetByIdAsync(int id);
    Task<IReadOnlyList<T>> ListAsync();
    void Add(T entity);
    void Remove(T entity);
}
```

**Unit of Work (UoW)** coordena **vários repositórios** dentro de **uma mesma transação**: você faz
várias alterações em repositórios diferentes e um único `SaveChanges`/`CommitAsync` grava tudo **de uma
vez** — "tudo ou nada".

```csharp
public interface IUnitOfWork
{
    IUserRepository Users { get; }
    IOrderRepository Orders { get; }
    Task<int> SaveChangesAsync();  // commita a transação
}

// Uso: debita saldo e cria pedido na MESMA transação.
_uow.Users.Add(novoUsuario);
_uow.Orders.Add(novoPedido);
await _uow.SaveChangesAsync(); // ambos gravam juntos, ou nada grava
```

**Por que UoW existe:** sem ele, cada repositório poderia salvar isoladamente, e uma falha no meio
deixaria dados **inconsistentes** (usuário criado, pedido não). O UoW garante atomicidade.

**Pegadinha:** confundir Repository (abstrai **a coleção de entidades**) com UoW (coordena a
**transação** entre repositórios). São responsabilidades diferentes que costumam andar juntas.

**Como responder:** "Repository abstrai o acesso a dados atrás de uma interface — o domínio não conhece
o banco. Ganho testabilidade, troco a fonte e centralizo queries. O Unit of Work coordena vários
repositórios numa transação: um `SaveChanges` commita tudo junto, garantindo atomicidade."

---

## 8. Crítica: quando NÃO usar Repository (o EF Core já é um)

Aqui é onde o **sênior se destaca**: saber que Repository nem sempre vale a pena — especialmente sobre
**EF Core**.

**O ponto central:** o **`DbContext` do EF Core JÁ implementa** os dois padrões:
- Cada **`DbSet<T>`** já é, na prática, um **repositório** (`Add`, `Remove`, `Find`, consultas LINQ).
- O **`SaveChanges`/`SaveChangesAsync`** já é o **Unit of Work** (rastreia mudanças e commita tudo junto).

Então colocar `IRepository<T>` + `IUnitOfWork` **por cima** do EF Core frequentemente é **redundância**
— você embrulha um padrão que já existe.

**Problema do repositório genérico sobre `IQueryable`** — a "abstração vazada":
- Se o repositório **retorna `IQueryable<T>`** para dar flexibilidade de query, o consumidor **ainda
  depende do provider do EF** (a tradução pra SQL, `Include`, `AsNoTracking`...). A abstração **não
  abstrai nada** — trocar de fonte quebraria tudo.
- Se o repositório **esconde** tudo atrás de métodos concretos, você precisa criar **um método pra cada
  variação de query** (`GetActiveUsersOrderedByNamePaged(...)`), e a interface **explode**. Você perde o
  poder de compor queries que o LINQ dá de graça.

Ou seja: você escolhe entre **vazar o EF** (abstração inútil) ou **engessar as queries** (interface
gigante). Nenhum dos dois é bom por padrão.

**Quando Repository AINDA faz sentido:**
- **Domínios ricos / DDD:** o repositório expõe operações do **domínio** (agregados), não CRUD genérico
  — ele fala a linguagem do negócio, não do banco.
- **Múltiplas fontes de dados:** de fato precisa alternar entre banco, cache, API externa.
- **Queries complexas centralizadas** e testáveis sem banco, quando o valor da abstração é real.

```csharp
// Bom: repositório de DOMÍNIO (fala do negócio, não é CRUD genérico sobre IQueryable).
public interface IPedidoRepository
{
    Task<Pedido?> ObterPorNumeroAsync(string numero);
    Task<IReadOnlyList<Pedido>> ObterPendentesDoClienteAsync(int clienteId);
    void Adicionar(Pedido pedido);
}
```

**Pegadinha:** dizer no automático "sempre use Repository, é boa prática". O entrevistador sênior quer
ver que você **pensa no trade-off**, não que decora dogma. Repositório genérico sobre `IQueryable` +
EF Core costuma ser **over-engineering**.

**Como responder:** "Depende. O DbContext do EF Core já é um repositório — cada `DbSet` — e um Unit of
Work — o `SaveChanges`. Um `IRepository<T>` genérico por cima costuma ser redundante e vira abstração
vazada: ou expõe `IQueryable` e não abstrai nada, ou esconde tudo e a interface explode. Eu uso
Repository quando ele fala a linguagem do **domínio** (DDD, agregados), quando há múltiplas fontes, ou
pra centralizar queries complexas testáveis. Fora disso, uso o DbContext direto e não pago o custo da
abstração."

---

## Glossário

- **DI (Injeção de Dependência):** técnica de entregar dependências prontas de fora (via construtor).
- **IoC (Inversão de Controle):** conceito de inverter o controle de criação/fluxo pro framework.
- **DIP (Princípio da Inversão de Dependência):** o "D" do SOLID — depender de abstrações, não de concretos.
- **`IServiceCollection`:** onde os serviços são **registrados** na inicialização.
- **`IServiceProvider`:** quem **resolve** (constrói) os serviços em runtime.
- **Constructor injection:** injetar dependências pelo construtor (forma padrão).
- **Transient:** nova instância a cada resolução.
- **Scoped:** uma instância por escopo (em web, por request HTTP).
- **Singleton:** uma instância para toda a aplicação.
- **Escopo (`IServiceScope`):** fronteira de tempo de vida; o ASP.NET Core abre um por request.
- **Captured dependency:** dependência de vida curta (Scoped/Transient) presa numa de vida longa (Singleton).
- **`IServiceScopeFactory`:** cria escopos manualmente para resolver Scoped dentro de um Singleton.
- **Validador de escopo (`ValidateScopes`):** verificação (ligada em Development) que detecta captured dependency.
- **Repository Pattern:** abstrair acesso a dados atrás de uma interface.
- **Unit of Work:** coordenar vários repositórios numa mesma transação (um `SaveChanges`).
- **Abstração vazada:** abstração que expõe detalhes da implementação que deveria esconder.

## Checagem de entendimento

1. Qual a diferença entre **DI**, **IoC** e **DIP** — em uma frase cada?
2. Um serviço leve, sem estado e barato de criar deveria ser Transient, Scoped ou Singleton — e por quê?
3. **Por que o DbContext do EF Core é registrado como Scoped** e não como Singleton?
4. O que é a **captured dependency**, por que é um bug com DbContext, e como o `IServiceScopeFactory` resolve?
5. Explique o papel do **Unit of Work** e por que ele existe **além** dos repositórios.
6. **Faz sentido usar Repository Pattern com EF Core?** Defenda os dois lados (quando sim, quando é over-engineering).
