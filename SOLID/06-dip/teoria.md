# Módulo 06 — DIP: Inversão de Dependência (Teoria)

> Objetivo do módulo: aprender a **inverter a seta da dependência**. Sua regra de negócio (o
> **alto nível** — o motivo de o sistema existir) hoje costuma depender diretamente dos **detalhes**
> concretos (SQL Server, SMTP, sistema de arquivos, relógio). O DIP diz para **ambos dependerem de uma
> abstração** — e, crucial, essa abstração **pertence ao alto nível**. Isso baixa acoplamento ao
> concreto (a raiz da fragilidade e da imobilidade do Módulo 01), torna o código testável e permite
> trocar o detalhe sem tocar na regra. De quebra, vamos desembaraçar três siglas que quase todo mundo
> confunde: **DIP** (o princípio), **DI** (a técnica) e **IoC** (o padrão amplo) — e ver como o
> **container do .NET** entra nessa história.

---

## 1. A definição: inverter a seta da dependência

O DIP, do Uncle Bob, tem **duas partes**:

> **(a)** Módulos de **alto nível** não devem depender de módulos de **baixo nível**. **Ambos** devem
> depender de **abstrações**.
>
> **(b)** Abstrações não devem depender de **detalhes**. **Detalhes** devem depender de **abstrações**.

Antes de tudo, dois termos:

- **Alto nível** = a **política**, a **regra de negócio** — o que dá sentido ao sistema. Ex.:
  "ao finalizar um pedido, calcular o total, salvar o pedido e avisar o cliente". É o *quê importa*.
- **Baixo nível** = os **detalhes de mecanismo** — *como* cada coisa acontece na infraestrutura.
  Ex.: "salvar" via SQL Server, "avisar" via SMTP, "ler o arquivo" via disco, "que horas são" via
  `DateTime.Now`.

### A "inversão", literalmente

Num código ingênuo, a seta de dependência aponta do **alto nível para o detalhe concreto**:

```
OrderService  ───▶  SqlOrderRepository
(regra)             (detalhe SQL)
```

O problema: a coisa **importante** (a regra) está pendurada na coisa **volátil** (o detalhe). Se o
detalhe muda, a regra sofre. Está tudo de cabeça para baixo — o essencial refém do acidental.

O DIP **inverte a seta**. Você define uma abstração (`IOrderRepository`) e faz **os dois** dependerem
dela:

```
OrderService  ───▶  IOrderRepository  ◀───  SqlOrderRepository
(regra)             (abstração)              (detalhe SQL)
```

Repare no que aconteceu: a seta que ia do serviço **para** o SQL sumiu. Agora o `SqlOrderRepository`
é quem **aponta para** a abstração (ele a implementa). A dependência do **detalhe** foi *invertida*
para apontar para a abstração — por isso o nome "inversão de dependência".

> 🔌 **Analogia da tomada.** Uma lâmpada não vem **soldada** na fiação da casa. Ela pluga num
> **soquete** (a abstração). O soquete é o contrato: "forneça energia neste formato". A fiação depende
> do soquete; a lâmpada depende do soquete; nenhuma depende diretamente da outra. Troque a lâmpada
> (o detalhe) sem mexer na fiação (a regra). O DIP é isso: programar contra o **soquete**, não contra
> a **lâmpada**.

**A régua do Módulo 01:** DIP é a técnica mais direta para **baixar o acoplamento ao concreto** — e
acoplamento a concreto é a causa direta da **fragilidade** ("mudar o banco quebrou a regra") e da
**imobilidade** ("não dá pra reusar/testar a regra sem arrastar o SQL junto").

---

## 2. O problema: o `new` do concreto dentro do alto nível

O cheiro do módulo é o **`new` de uma classe concreta de infraestrutura dentro da regra de negócio**.
Veja o **antes**:

```csharp
public class OrderService
{
    // Sem parâmetros: o serviço instancia as próprias dependências CONCRETAS.
    public void PlaceOrder(Order order)
    {
        var repository = new SqlOrderRepository("Server=...;Database=Shop;");
        var emailSender = new SmtpEmailSender("smtp.gmail.com", 587);

        order.Total = order.Items.Sum(i => i.Price * i.Quantity);

        repository.Save(order);                                  // detalhe: SQL
        emailSender.Send(order.CustomerEmail, "Pedido confirmado!"); // detalhe: SMTP
    }
}
```

Parece inofensivo — e roda. Mas a regra de negócio (`OrderService`) está **grudada** ao SQL Server e
ao SMTP *concretos*. Três dores nascem daí:

1. **Impossível de testar isoladamente.** Para rodar um teste de `PlaceOrder`, você precisa de um
   **banco SQL real** e de um **servidor SMTP real** no ar. Não dá pra injetar um dublê (mock/fake),
   porque o `new` está **cravado** dentro do método. Você não consegue verificar "o total foi
   calculado certo?" sem também disparar um e-mail de verdade.
2. **Trocar o detalhe obriga a editar a regra.** Migrar para PostgreSQL, ou trocar SMTP por um
   provedor HTTP (SendGrid), significa **abrir o `OrderService`** e mexer nele — código de negócio
   que já funcionava. Fragilidade pura.
3. **Acoplamento de compilação/deploy.** O alto nível **conhece** e **referencia** as classes de
   baixo nível. Ele não compila sem elas; recompila junto com elas. O essencial fica preso ao
   volátil.

> Este é o smell **"`new` espalhado"** da tabela do Módulo 01, e o **acoplamento a concreto** na veia.
> Toda vez que você vir `new AlgumaCoisaDeInfra()` dentro de uma classe de regra, acendeu a luz do DIP.

Repare também: o **construtor sem parâmetros** que "resolve tudo sozinho" é enganoso. Ele esconde as
dependências reais da classe. Olhando a assinatura, você não faz ideia de que `OrderService` precisa
de um banco e de um servidor de e-mail — só descobre lendo o corpo dos métodos.

---

## 3. A inversão: interface + injeção por construtor

A cura tem **duas partes que andam juntas**:

1. **Definir uma abstração** para cada fronteira volátil (`IOrderRepository`, `IEmailSender`).
2. **Receber a dependência de fora**, pelo **construtor** (constructor injection) — nunca dar `new`
   no concreto dentro da classe.

Veja o **depois**:

```csharp
// A ABSTRAÇÃO pertence ao ALTO NÍVEL: é a regra que dita o contrato do que precisa.
public interface IOrderRepository { void Save(Order order); }
public interface IEmailSender     { void Send(string to, string body); }

public class OrderService
{
    private readonly IOrderRepository _repository;
    private readonly IEmailSender _emailSender;

    // Dependências entram por construtor. O serviço não sabe (nem quer saber) se é SQL ou SMTP.
    public OrderService(IOrderRepository repository, IEmailSender emailSender)
    {
        _repository = repository;
        _emailSender = emailSender;
    }

    public void PlaceOrder(Order order)
    {
        order.Total = order.Items.Sum(i => i.Price * i.Quantity);
        _repository.Save(order);                                   // fala com o CONTRATO
        _emailSender.Send(order.CustomerEmail, "Pedido confirmado!");
    }
}

// O DETALHE apenas IMPLEMENTA o contrato definido pelo alto nível.
public class SqlOrderRepository : IOrderRepository
{
    public void Save(Order order) { /* ...SQL... */ }
}
```

### O ponto que quase todo mundo perde: a abstração **pertence ao alto nível**

Não basta "criar uma interface". O que faz a inversão acontecer é **onde** a interface mora e **quem**
dita o contrato. É a **regra de negócio** que declara *"eu preciso de algo que saiba `Save(order)`"*.
A interface expressa a **necessidade do alto nível**, não a **API do detalhe**. O
`SqlOrderRepository` é obrigado a se **encaixar** nesse contrato — e não o contrário.

Por isso a seta inverte de fato:

```
ANTES:  OrderService ──▶ SqlOrderRepository
DEPOIS: SqlOrderRepository ──▶ IOrderRepository ◀── OrderService
```

O detalhe (`SqlOrderRepository`) passou a **depender** da abstração. Se, ao "extrair a interface",
você só copiar a assinatura da classe concreta para uma interface e deixá-la no pacote de
infraestrutura, você criou uma abstração que **serve ao detalhe** — não inverteu nada de verdade.

### O que você ganha

| Situação | Antes (`new` concreto) | Depois (injeção de abstração) |
|---|---|---|
| Teste unitário | precisa de banco + SMTP reais | injeta `FakeOrderRepository` + `FakeEmailSender` |
| Trocar de banco | editar o `OrderService` | escrever `PostgresOrderRepository`, zero mudança na regra |
| Ver as dependências | ler o corpo dos métodos | estão explícitas no **construtor** |

Repare que "adicionar uma implementação nova sem tocar na regra" é exatamente o **OCP** (Módulo 03) —
e é o **DIP** que o torna possível. Voltaremos a isso na seção 5.

---

## 4. Desembaraçar DIP x DI x IoC (e o container do .NET)

Estas três siglas vivem sendo usadas como sinônimos, e **não são**. Separe-as com cuidado — cai em
entrevista e, pior, confunde na hora de projetar.

| Sigla | O que é | Analogia |
|---|---|---|
| **DIP** | O **princípio de design**: dependa de abstrações, não de concretos. | *A regra*. |
| **DI** (Injeção de Dependência) | A **técnica**: entregar as dependências **de fora** (por construtor/propriedade/método), em vez de instanciá-las dentro. | *Uma forma de cumprir a regra*. |
| **IoC** (Inversão de Controle) | O **padrão amplo**: "não me chame, eu te chamo" — você entrega o controle (do fluxo, da criação) ao framework. | *A família a que a DI pertence*. |
| **Container IoC/DI** | A **ferramenta** que resolve o grafo de objetos por você (ex.: `Microsoft.Extensions.DependencyInjection`). | *O robô que monta os LEGOs*. |

Amarrando:

- O **DIP** diz *"dependa de abstrações"*. É o objetivo.
- A **DI** é o **como** mais comum de alcançar o DIP: em vez de a classe dar `new` na dependência,
  alguém **injeta** a dependência pronta. Injeção por **construtor** é a forma preferida (torna a
  dependência obrigatória e explícita).
- **IoC** é o guarda-chuva. O nome vem do **Hollywood Principle**: *"não nos chame, nós chamamos
  você"*. Você entrega o controle ao framework — ele decide **quando** criar e **quando** chamar seu
  código. DI é **uma** forma de IoC (a inversão de *quem cria as dependências*). Callbacks, eventos e
  o próprio ciclo de vida de um framework web também são IoC.
- O **container** é só a ferramenta que automatiza a DI: você declara "quando alguém pedir
  `IOrderRepository`, entregue um `SqlOrderRepository`", e ele **monta o grafo** de objetos pra você.

> ⚠️ **DI não implica DIP.** Você pode injetar uma **classe concreta** por construtor
> (`OrderService(SqlOrderRepository repo)`) — usou a *técnica* DI, mas continua dependendo do
> **concreto**, então **não** cumpriu o DIP. E o inverso: dá pra respeitar o DIP sem container nenhum,
> montando os objetos à mão no `Main`. **DIP é design; DI é entrega; container é conveniência.**

### O container do .NET na prática

No `Microsoft.Extensions.DependencyInjection`, você **registra** os mapeamentos abstração → concreto:

```csharp
services.AddScoped<IOrderRepository, SqlOrderRepository>();
services.AddScoped<IEmailSender, SmtpEmailSender>();
services.AddScoped<OrderService>();
```

E pronto: quando alguém pede um `OrderService`, o container vê que o construtor precisa de
`IOrderRepository` e `IEmailSender`, cria um `SqlOrderRepository` e um `SmtpEmailSender`, e os
**injeta** — você **nunca** dá `new` no `OrderService`. O container **resolve o grafo** inteiro.

**Tempos de vida** (uma pincelada — decide *quantas instâncias* o container reaproveita):

| Lifetime | Quantas instâncias | Uso típico |
|---|---|---|
| **Transient** | uma **nova** a cada resolução | serviços leves e sem estado |
| **Scoped** | **uma por escopo** (por request web, tipicamente) | repositórios, `DbContext` |
| **Singleton** | **uma** para toda a aplicação | cache, config, clientes HTTP reutilizáveis |

> 🎯 **A pegadinha conceitual:** usar o container é **DI** (a técnica). O **valor real** vem de você
> ter respeitado o **DIP** no *design* — de as suas classes dependerem de `IOrderRepository`, não de
> `SqlOrderRepository`. Sem DIP, o container só instancia o seu **acoplamento** mais rápido. Container
> é consequência, não a essência.

---

## 5. Dosagem: interface só nas fronteiras que variam ou precisam de teste

Como todo princípio, DIP **cobra um preço** e pode ser exagerado. Abstração custa: mais um arquivo,
mais **indireção** (o famoso "F12 me joga na interface, não na implementação que eu queria ver"),
navegação mais chata, e um construtor que engorda. Se o benefício não paga esse custo, você fez
**over-engineering** — o smell do Módulo 01.

### Onde o DIP **vale a pena**

Nas **fronteiras de I/O e efeitos colaterais** — as coisas que **variam** ou que você precisa
**isolar para testar**:

- **Banco de dados** (`IOrderRepository`), **rede/HTTP** (`IPaymentGateway`, `ICurrencyApi`),
  **arquivo** (`IFileStorage`), **e-mail/SMS** (`IEmailSender`), **fila/mensageria** (`IMessageBus`).
- **O relógio** (`IClock` em vez de `DateTime.Now`) e **aleatoriedade** (`IGuidProvider`) — para
  tornar testável qualquer lógica que dependa de "que horas são" ou de valores aleatórios.

Todas têm em comum: são **detalhes voláteis**, **difíceis de reproduzir em teste**, e **plausíveis de
trocar**. Abstraí-las paga.

### Onde o DIP **não** vale a pena

- **Objetos de valor e tipos de domínio estáveis**: um `Money`, um `Endereco`, um `Pedido` puro. São
  o *coração* do domínio, não uma fronteira volátil. Criar `IMoney` é ruído.
- **Lógica pura, sem I/O e sem variação**: um cálculo de imposto determinístico que nunca mudou de
  estratégia. Ele já é testável (entra número, sai número) — não precisa de abstração para isso.
- **Uma interface com um único implementador que nunca vai variar e não é I/O**: o caso clássico de
  abstração especulativa. É o **YAGNI** (Módulo 01) gritando.

> **A régua prática:** abstraia a fronteira quando ela **(a)** faz I/O ou tem efeito colateral difícil
> de reproduzir em teste, **ou (b)** tem uma variação real/provável. Se não é nenhum dos dois,
> `new` direto (ou uma dependência concreta) provavelmente é o **melhor** design — mesmo que "viole" o
> DIP no papel.

### O fio com os outros princípios

- **OCP (Mód. 03):** DIP é o que **sustenta** o OCP. Estender comportamento com uma nova
  implementação (sem editar a regra) só é possível porque a regra depende da **abstração**.
- **LSP (Mód. 04):** as implementações que você injeta precisam ser **substituíveis** pela abstração —
  um `FakeEmailSender` que joga exceção onde o real funciona quebra o LSP e estraga o benefício.
- **ISP (Mód. 05):** as abstrações do DIP devem ser **enxutas**. `IOrderRepository` com 15 métodos
  força implementadores e mocks a lidar com o que não usam. DIP + ISP = **abstrações pequenas e
  focadas**, na direção certa.

---

## 6. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Alto nível | A regra de negócio, a política — o motivo de o sistema existir. |
| Baixo nível | Os detalhes de mecanismo (SQL, SMTP, arquivo, relógio). |
| Abstração | O contrato (interface) que ambos os lados passam a depender. |
| Inversão da seta | A dependência do detalhe passa a apontar para a abstração, não o contrário. |
| DIP | O princípio: dependa de abstrações, não de concretos. |
| DI (Injeção de Dependência) | A técnica: entregar as dependências de fora (construtor/prop./método). |
| Constructor injection | Injetar pela assinatura do construtor — dependência obrigatória e explícita. |
| IoC (Inversão de Controle) | O padrão amplo ("não me chame, eu te chamo"); DI é uma forma dele. |
| Container IoC/DI | A ferramenta que resolve o grafo de objetos (ex.: MS.Extensions.DI). |
| Lifetime | Quantas instâncias o container reaproveita: Transient / Scoped / Singleton. |
| Fronteira de I/O | Banco, rede, arquivo, e-mail, relógio — onde o DIP costuma valer. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Enuncie as **duas partes** do DIP. O que exatamente é "invertido" — e quem passa a depender de quem
   depois da inversão?
2. Por que um `OrderService` que dá `new SqlOrderRepository()` lá dentro é **difícil de testar**? O
   que a injeção por construtor muda nisso?
3. Por que se diz que a **abstração pertence ao alto nível**? O que dá errado se você só "extrai uma
   interface" a partir da classe concreta e a deixa junto do detalhe?
4. Diferencie **DIP**, **DI** e **IoC**. Onde entra o **container** do .NET — e por que "usar o
   container" não garante que você respeitou o DIP?
5. Dê um exemplo de fronteira onde **vale** aplicar DIP e um exemplo de tipo onde criar interface seria
   **over-engineering**. Qual é a régua para decidir?

Quando estiver confortável com essas respostas, siga para **`pratica.md`** — lá você vai *inverter as
dependências* de um serviço de verdade.
