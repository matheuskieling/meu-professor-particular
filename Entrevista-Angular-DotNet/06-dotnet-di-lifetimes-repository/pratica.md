# Prática — Simulação de entrevista (Módulo 06)

Nesta fase a mesa vira: **você é o candidato, eu sou o entrevistador**. Vou fazer as perguntas abaixo
**uma a uma**, ouvir sua resposta em voz alta (texto) e então **criticar**: o que faltou, o que soou
impreciso, o que um sênior diria a mais. Não é pra decorar a resposta-modelo — é pra treinar a **fala**.

Cada pergunta traz uma **resposta-modelo** (o que um bom candidato diria) e os **erros comuns** que
derrubam gente na entrevista.

---

### Pergunta 1 — O que é Injeção de Dependência e por que ela importa?

**Resposta-modelo:** "DI é entregar as dependências de uma classe prontas de fora, tipicamente pelo
construtor, em vez de a classe criá-las com `new`. Isso dá **desacoplamento** — a classe depende de uma
interface, não de uma implementação concreta — e **testabilidade** — no teste eu injeto um mock. No
.NET, registro os serviços no `IServiceCollection` e o `IServiceProvider` resolve o grafo em runtime."

**Erros comuns:**
- Descrever só o mecanismo ("é passar pelo construtor") sem citar o **porquê** (desacoplamento/teste).
- Não mencionar que a classe depende de **abstração**, não de concreto.
- Confundir DI com um framework específico (é um conceito; o container é a ferramenta).

---

### Pergunta 2 — Qual a diferença entre DI, IoC e DIP?

**Resposta-modelo:** "IoC é o conceito guarda-chuva: inverter o controle da criação/fluxo pro
framework. DI é uma técnica de IoC: injetar dependências de fora. DIP é o princípio SOLID — o 'D' — que
manda depender de abstrações, não de concretos. Resumindo: DIP é a regra, DI é a técnica que a aplica,
IoC é o conceito, e o container de DI é a ferramenta."

**Erros comuns:**
- Dizer "DI e IoC são a mesma coisa" — não são: DI é um caso de IoC.
- Confundir DI (técnica) com DIP (princípio).
- Não saber que DIP é o "D" do SOLID.

---

### Pergunta 3 — Explique os três service lifetimes: Transient, Scoped e Singleton.

**Resposta-modelo:** "**Transient** cria uma instância nova a cada resolução — bom pra serviços leves e
sem estado. **Scoped** é uma instância por escopo; em ASP.NET Core cada request HTTP é um escopo, então
é uma por request, compartilhada entre os serviços daquele request — é o caso do DbContext. **Singleton**
é uma instância pra app inteira, compartilhada entre todos os requests e threads — bom pra estado
imutável e cache, mas exige thread-safety em qualquer estado mutável."

**Erros comuns:**
- Dizer que Scoped é "por chamada de método" ou "por classe" — é **por escopo/request**.
- Esquecer o alerta de **thread-safety** no Singleton.
- Não dar um exemplo de uso de cada um.

---

### Pergunta 4 — Por que o DbContext do EF Core é registrado como Scoped?

**Resposta-modelo:** "Por dois motivos: o DbContext **não é thread-safe**, então não pode ser usado por
requests concorrentes ao mesmo tempo; e o **change tracker** representa uma **unidade de trabalho** — um
request é uma unidade de trabalho, então faz sentido um DbContext por request, compartilhado entre os
serviços daquele request. Se fosse Singleton, ele seria usado por várias threads simultaneamente e
acumularia entidades rastreadas pra sempre — bug e vazamento de memória."

**Erros comuns:**
- Responder só "é o padrão do `AddDbContext`" sem explicar **por quê**.
- Não citar o **thread-safety** nem o **change tracker/unidade de trabalho**.
- Dizer que poderia ser Transient sem notar que isso criaria vários DbContexts por request, quebrando a
  unidade de trabalho.

---

### Pergunta 5 — O que acontece se você injetar um serviço Scoped dentro de um Singleton?

**Resposta-modelo:** "É a **captured dependency**. O Singleton é criado uma vez e segura a dependência
pra sempre, então o Scoped é resolvido uma única vez e vira **efetivamente Singleton** — para de
respeitar o próprio lifetime. Com DbContext isso é grave: vira um DbContext compartilhado entre todos os
requests, não é thread-safe e vaza o change tracker. O **validador de escopo** do ASP.NET Core, ligado
em Development, detecta isso e lança `InvalidOperationException`. A correção é injetar
`IServiceScopeFactory` e criar um escopo por operação."

**Erros comuns:**
- Dizer "não acontece nada" ou "funciona normal".
- Não saber o nome (captured dependency) nem que o Scoped "vira Singleton".
- Não conhecer a correção com `IServiceScopeFactory`.

---

### Pergunta 6 — Como você corrigiria essa captured dependency na prática?

**Resposta-modelo:** "Em vez de injetar o Scoped no construtor do Singleton, injeto o
`IServiceScopeFactory`. A cada operação, faço `using var scope = _scopeFactory.CreateScope();` e resolvo
o Scoped com `scope.ServiceProvider.GetRequiredService<AppDbContext>()` dentro do `using`. Assim o
DbContext vive só o tempo daquela operação e é descartado no fim do escopo — cada operação tem seu
próprio, sem compartilhamento entre threads."

**Erros comuns:**
- Esquecer o `using` (o escopo precisa ser descartado, senão vaza).
- Injetar `IServiceProvider` no lugar de `IServiceScopeFactory` e resolver Scoped na raiz (isso ainda
  captura — a resolução precisa ser **dentro de um escopo criado**).
- Achar que basta trocar o registro do serviço.

---

### Pergunta 7 — Qual a regra geral para combinar lifetimes com segurança?

**Resposta-modelo:** "A regra de ouro: **a vida de uma dependência nunca pode ser menor que a de quem a
injeta**. Singleton pode injetar Singleton. Scoped pode injetar Scoped ou Singleton. Um Singleton não
injeta Scoped nem Transient com estado diretamente — se precisar, cria um escopo sob demanda com
`IServiceScopeFactory`."

**Erros comuns:**
- Inverter a regra (achar que o problema é injetar Singleton num Scoped — isso é seguro).
- Não conseguir generalizar a partir do caso do DbContext.

---

### Pergunta 8 — Quando você usaria um Singleton, e qual o principal cuidado?

**Resposta-modelo:** "Uso Singleton pra estado **imutável**, configuração carregada uma vez, cache e
clientes reutilizáveis caros de criar. O principal cuidado é **thread-safety**: como a mesma instância é
usada por vários requests em threads diferentes, qualquer estado mutável precisa de `lock` ou de uma
coleção concorrente como `ConcurrentDictionary`. E nunca guardo estado 'do request atual' num Singleton
— isso vaza entre usuários."

**Erros comuns:**
- Não citar thread-safety.
- Sugerir guardar dados de request/usuário num Singleton.
- Achar que Singleton é sempre a opção "mais eficiente" e usar pra tudo.

---

### Pergunta 9 — O que é o Repository Pattern e por que usar?

**Resposta-modelo:** "É abstrair o acesso a dados atrás de uma interface — o domínio fala com
`IUserRepository` e não conhece o banco por trás. Ganho **testabilidade** (mocko o repo), a
possibilidade de **trocar a fonte de dados** e **centralizar as queries** num lugar só. Junto costuma vir
o **Unit of Work**, que coordena vários repositórios numa transação — um `SaveChanges` commita tudo,
garantindo atomicidade."

**Erros comuns:**
- Descrever Repository como "uma classe que faz CRUD" sem citar **abstração/interface**.
- Não saber explicar o **Unit of Work** nem por que ele existe (atomicidade).
- Confundir os dois: Repository abstrai a coleção; UoW coordena a transação.

---

### Pergunta 10 — Faz sentido usar Repository com EF Core?

**Resposta-modelo:** "Depende — e essa é a resposta madura. O DbContext do EF Core **já é** um
repositório (cada `DbSet`) e um Unit of Work (o `SaveChanges`). Um `IRepository<T>` genérico por cima
costuma ser redundante e vira **abstração vazada**: ou expõe `IQueryable` e não abstrai nada — o
consumidor ainda depende do EF — ou esconde tudo e a interface explode com um método por query. Eu uso
Repository quando ele fala a linguagem do **domínio** (DDD, agregados), quando há **múltiplas fontes de
dados**, ou pra **centralizar queries complexas** testáveis. Fora disso, uso o DbContext direto."

**Erros comuns:**
- Responder no automático "sim, sempre — é boa prática" (o entrevistador quer ver o trade-off).
- Não saber que o DbContext já é repo + UoW.
- Não conhecer o conceito de **abstração vazada** com `IQueryable`.

---

### Pergunta 11 — Um colega criou um `IRepository<T>` genérico que retorna `IQueryable<T>`. Qual o problema?

**Resposta-modelo:** "Se ele retorna `IQueryable<T>`, a abstração **não abstrai nada**: o consumidor
ainda compõe a query com LINQ que o **provider do EF** vai traduzir — usa `Include`, `AsNoTracking`,
etc. Trocar a fonte de dados quebraria tudo, e a lógica de query vaza pra fora do repositório. É uma
abstração vazada e a promessa do Repository (esconder o EF) não se cumpre. Se ao contrário ele escondesse
tudo atrás de métodos, a interface explodiria com um método por variação de query."

**Erros comuns:**
- Achar que retornar `IQueryable` é o "melhor dos dois mundos" (é o pior — perde a abstração e o
  encapsulamento).
- Não nomear "abstração vazada".

---

### Pergunta 12 — Como o container do .NET resolve o grafo de dependências? E como você registra e resolve um serviço?

**Resposta-modelo:** "Na inicialização, registro no `IServiceCollection` com `AddTransient`,
`AddScoped` ou `AddSingleton`, mapeando a interface pra implementação. Em runtime, quando algo pede um
serviço — via constructor injection ou `GetRequiredService` — o `IServiceProvider` constrói a instância
e resolve **recursivamente** todas as dependências do construtor dela, montando o grafo inteiro,
respeitando o lifetime de cada uma. Constructor injection é a forma padrão; resolução manual eu evito,
uso só em pontos de fronteira como um background service."

**Erros comuns:**
- Não separar **registro** (`IServiceCollection`, na inicialização) de **resolução**
  (`IServiceProvider`, em runtime).
- Não saber que o container resolve o grafo **recursivamente**.
- Abusar de `GetService`/service locator em vez de constructor injection (anti-padrão).
