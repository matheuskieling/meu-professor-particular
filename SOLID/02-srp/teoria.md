# Módulo 02 — SRP: Single Responsibility Principle (Teoria)

> Objetivo do módulo: dominar o **S** do SOLID — o **Princípio da Responsabilidade Única**. Você vai
> aprender a definição *correta* (que não é a popular), a enxergar uma "responsabilidade" como um
> **ator** (uma razão para mudar), a refatorar uma **God class** separando responsabilidades, e —
> tão importante quanto — a **dosar**: SRP levado ao extremo apodrece o código tanto quanto ignorá-lo.

---

## 1. A definição correta: uma única razão para mudar

A frase que você mais vai ouvir por aí é *"uma classe deve fazer apenas uma coisa"*. Ela é
**imprecisa e engana**. O que é "uma coisa"? Uma classe `EmailSender` monta o corpo do e-mail, abre
conexão SMTP, faz retry e loga o envio — são quatro "coisas" e ninguém acharia que ela viola SRP.

A formulação do **Robert C. Martin (Uncle Bob)**, que criou o princípio, é outra:

> **Uma classe deve ter apenas UMA razão para mudar.**

E, na sua reformulação mais precisa:

> **Reúna as coisas que mudam pela mesma razão; separe as que mudam por razões diferentes.**

Repare o deslocamento: o critério não é *quantas coisas a classe faz*, e sim **quantos motivos
diferentes fariam você abrir esse arquivo para editá-lo**. Se há mais de um motivo — mais de uma
"fonte" de pedidos de mudança — a classe tem mais de uma responsabilidade.

Isso conecta direto com o Módulo 01: SRP é a ferramenta prática para **reduzir acoplamento** (coisas
que não têm relação param de estar amarradas) e **elevar coesão** (o que sobra numa classe fala de
um assunto só).

---

## 2. Responsabilidade é um ator (um eixo de mudança)

Se "uma razão para mudar" é o critério, a pergunta natural é: **quem** decide que algo precisa mudar?
A resposta do Uncle Bob é o conceito de **ator**:

> Uma **responsabilidade** é uma família de mudanças pedidas por **um mesmo grupo de stakeholders** —
> um **ator**. Uma classe deve ser responsável perante **um único ator**.

Ator = um eixo de mudança, uma "fonte" de pedidos. O exemplo canônico dele é uma classe `Employee`:

```csharp
public class Employee
{
    public decimal CalculatePay() { /* ... */ }   // pedido pelo FINANCEIRO
    public string  ReportHours()  { /* ... */ }   // pedido pelo RH
    public void    Save()         { /* ... */ }   // pedido pelo DBA / infra
}
```

Três métodos, **três atores distintos**:

| Método | Ator (quem pede a mudança) | Razão para mudar |
|--------|----------------------------|------------------|
| `CalculatePay()` | Departamento financeiro | Regra de folha de pagamento muda |
| `ReportHours()` | Recursos Humanos | Formato/regra do relatório de horas muda |
| `Save()` | DBA / time de infra | Esquema de banco ou tecnologia de persistência muda |

Três atores → **três razões para mudar** → **viola o SRP**.

### Por que isso é perigoso (não é só estética)

O risco real aparece quando esses métodos **compartilham código interno**. Suponha que
`CalculatePay()` e `ReportHours()` usem um helper privado `RegularHours()` que arredonda horas de
um jeito. O financeiro pede uma mudança na regra de arredondamento para a folha; você edita
`RegularHours()` — e **silenciosamente quebra o relatório do RH**, que dependia do comportamento
antigo. Dois atores que não se falam foram acoplados **acidentalmente** por um método compartilhado
dentro da mesma classe.

> 💡 **A dor do SRP violado é essa:** uma mudança pedida por *um* ator produz um bug para *outro*
> ator. Separar as responsabilidades remove esse acoplamento acidental.

---

## 3. O "antes": uma God class em C#

Vamos a um caso mais realista. Uma **God class** que processa um pedido — ela **valida**, **calcula
imposto**, **persiste no banco** e **envia e-mail**, tudo num arquivo só:

```csharp
public class OrderProcessor
{
    public void Process(Order order)
    {
        // 1) Regras de negócio (ator: produto/negócio)
        if (order.Items.Count == 0) throw new InvalidOperationException("Pedido vazio");
        if (order.Total <= 0)       throw new InvalidOperationException("Total inválido");

        // 2) Cálculo de imposto (ator: fiscal/contábil)
        var tax = order.Total * 0.18m;
        order.Total += tax;

        // 3) Persistência (ator: DBA/infra de dados)
        using var conn = new SqlConnection(_connString);
        conn.Open();
        var cmd = new SqlCommand("INSERT INTO Orders (Id, Total) VALUES (@id, @total)", conn);
        cmd.Parameters.AddWithValue("@id", order.Id);
        cmd.Parameters.AddWithValue("@total", order.Total);
        cmd.ExecuteNonQuery();

        // 4) Notificação (ator: infra de comunicação/marketing)
        var smtp = new SmtpClient("smtp.empresa.com");
        var mail = new MailMessage("no-reply@empresa.com", order.CustomerEmail)
        {
            Subject = "Pedido confirmado",
            Body = $"Seu pedido {order.Id} no valor de {order.Total:C} foi confirmado."
        };
        smtp.Send(mail);
    }
}
```

Sintomas que gritam violação de SRP:

- **Quatro atores num arquivo:** negócio, fisco, DBA, comunicação. Cada um pode pedir mudança por
  conta própria — quatro razões para mudar.
- **Mistura de níveis de abstração:** regra de domínio (`Items.Count == 0`), SQL cru
  (`INSERT INTO...`) e template de string de e-mail convivem no mesmo método. Ler isso é pular entre
  camadas mentais o tempo todo.
- **Difícil de testar:** para testar a *validação* — pura regra de negócio — você acaba precisando de
  um banco SQL de pé e um servidor SMTP. As dependências não relacionadas contaminam tudo.
- **Fragilidade:** mudar a alíquota de imposto de `0.18m` te obriga a mexer no mesmo arquivo onde
  mora o envio de e-mail. Um deslize e você quebra algo sem relação.
- **Cheiro no nome:** `Processor`, `Manager`, `Util`, `Helper`, ou qualquer nome com **"And"**
  (`OrderValidatorAndMailer`) costuma denunciar acúmulo de responsabilidades. O nome não consegue
  descrever *uma* coisa porque a classe faz várias.

---

## 4. O "depois": separar por ator (mais um coordenador fino)

Extraímos **uma classe por responsabilidade** — cada uma com um único ator dono — e deixamos um
**coordenador fino** só para orquestrar a ordem das operações:

```csharp
// Ator: negócio/produto — só regras de validação
public class OrderValidator
{
    public void Validate(Order order)
    {
        if (order.Items.Count == 0) throw new InvalidOperationException("Pedido vazio");
        if (order.Total <= 0)       throw new InvalidOperationException("Total inválido");
    }
}

// Ator: fiscal/contábil — só cálculo de imposto
public class TaxCalculator
{
    public decimal CalculateTax(Order order) => order.Total * 0.18m;
}

// Ator: DBA/infra de dados — só persistência
public class OrderRepository
{
    public void Save(Order order) { /* SQL isolado aqui */ }
}

// Ator: infra de comunicação — só envio de e-mail
public class EmailSender
{
    public void SendConfirmation(Order order) { /* SMTP isolado aqui */ }
}

// Coordenador FINO: orquestra, não reimplementa as regras
public class OrderService
{
    private readonly OrderValidator _validator;
    private readonly TaxCalculator _tax;
    private readonly OrderRepository _repository;
    private readonly EmailSender _email;

    public OrderService(OrderValidator validator, TaxCalculator tax,
                        OrderRepository repository, EmailSender email)
    {
        _validator = validator; _tax = tax;
        _repository = repository; _email = email;
    }

    public void Process(Order order)
    {
        _validator.Validate(order);
        order.Total += _tax.CalculateTax(order);
        _repository.Save(order);
        _email.SendConfirmation(order);
    }
}
```

O que mudou de fato:

- **Cada classe tem UMA razão para mudar.** A alíquota mudou? Só `TaxCalculator`. Trocou SQL Server
  por PostgreSQL? Só `OrderRepository`. O RH... perdão, o marketing quer outro texto de e-mail? Só
  `EmailSender`. Nenhuma dessas mudanças arrisca as outras.
- **O coordenador é fino.** `OrderService.Process` **decide a ordem** das operações, mas **não contém
  as regras**. Ele coordena; não valida imposto nem monta SQL. Essa é a chave: o coordenador não é
  uma nova God class disfarçada.
- **Dependências injetadas.** As peças chegam pelo construtor (mais sobre isso no Módulo 06 — DIP).
  Isso permite testar cada uma isolada e trocar implementações.
- **Testável de verdade.** `TaxCalculator` se testa com um `Order` em memória, sem banco nem SMTP.
- **Coesão restaurada.** Cada arquivo fala de um assunto só — exatamente o "alta coesão" do Módulo 01.

---

## 5. Dosagem: o outro lado do SRP

Aqui mora a parte que separa quem entende SRP de quem só decorou o slogan. **SRP levado ao extremo é
tão nocivo quanto ignorá-lo.** Se você tratar "uma razão para mudar" como "**um método por classe**",
você produz uma **explosão de micro-classes**:

```csharp
// OVER-ENGINEERING: cada operação virou uma classe anêmica
public class OrderTotalCalculator { public decimal Calc(Order o) => /* ... */; }
public class OrderTotalRounder    { public decimal Round(decimal v) => /* ... */; }
public class OrderTotalFormatter  { public string  Format(decimal v) => /* ... */; }
// ...e mais dez classes que SEMPRE mudam juntas
```

O que dá errado:

- **Classes anêmicas.** Classes que só têm getters/setters ou um método bobo, com a lógica espalhada
  em vários lugares. Isso é coesão **baixa**, não alta — o oposto do que o SRP quer.
- **Acoplamento sobe, não desce.** Se `Calc`, `Round` e `Format` **sempre mudam juntos** (mesmo ator,
  mesma razão), separá-los só cria três arquivos que você precisa editar em conjunto toda vez.
  Trocou uma regra? Abra três classes. Isso é acoplamento entre arquivos, disfarçado de "limpeza".
- **Navegar vira um inferno.** Rastrear uma lógica que atravessa 12 micro-classes é pior do que lê-la
  num único método coeso.

### A bússola: separe por ATOR, não por verbo

A pergunta certa **nunca** é "esse método faz mais de uma coisinha?". É:

> **Quantos atores diferentes pediriam mudanças nesta classe?**

- Se a resposta é **um** ator → deixe junto, mesmo que sejam vários métodos. Coisas que **mudam pela
  mesma razão** pertencem à mesma classe.
- Se a resposta é **mais de um** ator → separe, para que a mudança de um não atinja o outro.

> 🎯 **Regra prática:** *"Não separe o que sempre muda junto; não junte o que muda por razões
> diferentes."* O ator é a fronteira. Verbos (`Calcular`, `Formatar`, `Salvar`) não são, por si sós,
> responsabilidades distintas — só são se pertencerem a atores distintos.

### Quando NÃO aplicar (ainda)

- Código **pequeno, estável e que muda por um único motivo**: não estilhaçe por dogma. Você pode
  separar depois, *quando* uma segunda razão para mudar aparecer de fato (YAGNI).
- **Regra de ouro:** aplique SRP quando o acúmulo já **dói** (mudanças que se contaminam, testes
  difíceis) ou quando você **sabe** que dois atores vão evoluir separado. Não aplique "por garantia".

SRP bem-dosado é a **base** dos outros princípios: separar por responsabilidade prepara o terreno
para **OCP** (Módulo 03 — estender sem editar) e **ISP** (Módulo 05 — interfaces enxutas por cliente).

---

## 6. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Responsabilidade | Uma família de mudanças pedidas por um mesmo ator; uma razão para mudar. |
| Ator | Um grupo de stakeholders (fonte) que pede um tipo de mudança. Ex.: financeiro, RH, DBA. |
| Razão para mudar | O motivo que faria você editar a classe; o critério real do SRP. |
| God class | Classe que acumula muitas responsabilidades/atores (nome-cheiro: Manager, Util, Processor). |
| Coordenador fino | Classe que orquestra a ordem das peças **sem** conter as regras delas. |
| Classe anêmica | Classe quase sem comportamento (só dados), com a lógica dispersa — baixa coesão. |
| Coesão | O quanto os elementos de uma classe pertencem juntos; SRP respeitado ≈ alta coesão. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Por que *"uma classe deve fazer apenas uma coisa"* é uma formulação **imprecisa** do SRP? Qual é
   a formulação correta?
2. O que é um **ator** no contexto do SRP, e quantos atores tem a classe `Employee` do exemplo?
3. Qual é o **perigo concreto** de duas responsabilidades diferentes conviverem na mesma classe
   (pense em métodos que compartilham código interno)?
4. No "depois" do `OrderProcessor`, por que o `OrderService` coordenador **não** volta a ser uma God
   class, mesmo chamando quatro peças?
5. Dê um exemplo de SRP **mal-dosado** (over-engineering). Qual pergunta você faz para decidir se
   deve separar ou manter junto?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
