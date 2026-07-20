# Módulo 07 — Capstone: refatoração integradora (Prática Guiada)

> Objetivo desta prática: pegar **um** mini-sistema em C# com **vários cheiros de uma vez** e
> refatorá-lo aplicando os **cinco princípios na ordem** (SRP → OCP → LSP → ISP → DIP), chegando a um
> design **injetável, extensível e testável** — **sem exagerar**. Esta é a maior prática do curso: é
> onde tudo se costura.
>
> **Abordagem:** eu apresento o código podre, você propõe a refatoração e eu conduzo/critico passo a
> passo — um princípio por vez. Ao fim de cada passo, checamos o smell que sumiu. E no final,
> checamos a **dosagem**: onde a gente **parou** de propósito.
>
> Não precisa rodar nada. É raciocínio de design conduzido no chat.

---

## O código de partida

Um sistema de processamento de pedidos. Uma classe só faz **tudo**: calcula total, aplica desconto
por tipo de cliente, escolhe o meio de pagamento por `switch`, dá `new` em concretos de fronteira
(gateway, SMTP, banco), e ainda implementa uma **interface gorda**. Leia e vá caçando os cheiros.

```csharp
public interface IPedidoService
{
    void Processar(Pedido pedido);
    void Reembolsar(Pedido pedido);
    void GerarRelatorioMensal();   // <- a maioria dos clientes não usa isto
    void EnviarNewsletter();       // <- nem isto
}

public class OrderProcessor : IPedidoService   // God class + fat interface
{
    public void Processar(Pedido pedido)
    {
        // 1) cálculo do total
        decimal total = 0;
        foreach (var item in pedido.Itens)
            total += item.Preco * item.Quantidade;

        // 2) desconto por tipo de cliente (switch que vive crescendo)
        switch (pedido.TipoCliente)
        {
            case "Comum":  break;
            case "Vip":    total *= 0.90m; break;
            case "Black":  total *= 0.70m; break;
            // toda promoção nova = editar AQUI (viola OCP)
            default: throw new ArgumentException("tipo de cliente desconhecido");
        }

        // 3) pagamento por switch, com new de concretos no meio
        switch (pedido.MeioPagamento)
        {
            case "Cartao":
                var gateway = new StripeGateway("sk_live_xxx");   // new de fronteira (viola DIP)
                gateway.Cobrar(total);
                break;
            case "Boleto":
                var banco = new BancoDoBrasilApi();               // outro concreto acoplado
                banco.GerarBoleto(total);
                break;
            default: throw new ArgumentException("meio de pagamento desconhecido");
        }

        // 4) persistência: new direto do contexto de banco
        var db = new SqlConnection("Server=prod;...");            // acoplado ao SQL concreto
        db.Executar($"INSERT INTO pedidos VALUES ({pedido.Id}, {total})");

        // 5) notificação: SMTP concreto no meio da regra de negócio
        var smtp = new SmtpClient("smtp.empresa.com");            // acoplado ao SMTP concreto
        smtp.Enviar(pedido.EmailCliente, "Pedido confirmado", $"Total: {total}");
    }

    public void Reembolsar(Pedido pedido) { /* ... mais new de gateway aqui ... */ }

    // Implementações "de fachada": esta classe é forçada a ter métodos que não são dela
    public void GerarRelatorioMensal() => throw new NotImplementedException();
    public void EnviarNewsletter()    => throw new NotImplementedException();
}
```

**Os cheiros (todos de uma vez):**
- **God class (SRP):** `OrderProcessor` calcula, desconta, cobra, salva **e** notifica — cinco razões
  pra mudar.
- **`switch` por tipo (OCP):** desconto e pagamento crescem por edição de código existente.
- **`new` de concreto de fronteira (DIP):** `StripeGateway`, `BancoDoBrasilApi`, `SqlConnection`,
  `SmtpClient` — tudo acoplado e **impossível de testar**.
- **Fat interface (ISP):** `IPedidoService` mistura processar/reembolsar com relatório/newsletter;
  `OrderProcessor` é forçada a implementar o que não é dela → `NotImplementedException` (que também
  fere **LSP**).

---

## A refatoração, um princípio por vez

Não tente arrumar tudo de uma vez. Vamos na **ordem mental** do Módulo 07.

### Passo 1 — SRP: separe por responsabilidade

**Pergunta-guia:** quantas razões diferentes essa classe tem pra mudar? Quais são os **atores**?

Responsabilidades distintas escondidas ali: **calcular total/desconto**, **cobrar**, **persistir**,
**notificar**. Cada uma vira sua própria classe. O `OrderProcessor` deixa de *fazer* e passa a
*coordenar*.

<details>
<summary>💡 Dica progressiva 1</summary>

Liste os "atores": o financeiro muda regra de desconto; o time de pagamentos muda o gateway; o DBA
muda a persistência; o marketing muda o texto do e-mail. Cada ator = uma classe candidata.
</details>

### Passo 2 — OCP: troque os `switch` por polimorfismo

O `switch (TipoCliente)` e o `switch (MeioPagamento)` são pontos de **variação**. Cada um vira uma
**abstração** com uma implementação por variante (isto é o padrão **Strategy**). Adicionar uma
promoção ou um meio de pagamento passa a ser **criar uma classe**, sem tocar no processador.

<details>
<summary>💡 Dica progressiva 2</summary>

`IDescontoStrategy { decimal Aplicar(decimal total); }` com `SemDesconto`, `DescontoVip`,
`DescontoBlack`. E `IMeioPagamento { void Cobrar(decimal valor); }` com `CartaoPagamento`,
`BoletoPagamento`. O `default: throw` some — quem escolhe a strategy é quem monta o pedido.
</details>

### Passo 3 — LSP: garanta que os subtipos honram o contrato

Cada `IMeioPagamento` **realmente cobra**? Nenhuma implementação pode estourar `NotSupportedException`
nem devolver algo que quebre quem chama. Os `NotImplementedException` do relatório/newsletter também
somem — porque no próximo passo eles saem da interface. LSP aqui é: **toda implementação é um
substituto de verdade**.

<details>
<summary>💡 Dica progressiva 3</summary>

Se uma "estratégia de pagamento" não puder cobrar (ex.: "pagamento presencial" que não tem API), ela
**não deveria** implementar `IMeioPagamento` só pra jogar exceção. Isso seria um LSP quebrado — sinal
de que a hierarquia está errada. Prefira modelar só o que honra o contrato.
</details>

### Passo 4 — ISP: quebre a interface gorda por papel

`IPedidoService` mistura papéis. Separe: `IProcessadorPedido { Processar(); Reembolsar(); }` de um
lado; relatório e newsletter viram **outras** interfaces/serviços (`IRelatorioService`,
`INewsletterService`), implementados por **outras** classes. O `OrderProcessor` para de ser forçado a
ter métodos que não são dele — os `NotImplementedException` desaparecem.

<details>
<summary>💡 Dica progressiva 4</summary>

Pergunte: "quem CHAMA `Processar` também chama `EnviarNewsletter`?" Não. São clientes diferentes,
papéis diferentes → interfaces diferentes. Cada consumidor depende só da fatia que usa.
</details>

### Passo 5 — DIP: inverta as dependências de fronteira e injete

Os `new StripeGateway`, `new SmtpClient`, `new SqlConnection` são **fronteiras**. Crie abstrações
(`IGatewayPagamento`, `INotificador`, `IPedidoRepository`) e **injete pelo construtor**. Agora o
processador depende de **abstrações**, roda com a DI do .NET e — de brinde — é **testável** (você
injeta fakes).

<details>
<summary>💡 Dica progressiva 5</summary>

Construtor: `OrderProcessor(ICalculadoraPedido calc, IPedidoRepository repo, INotificador notif)`.
Quem constrói o quê? O **container de DI** (`services.AddScoped<INotificador, EmailNotificador>()`).
O processador só recebe as abstrações prontas — ele não sabe se é SMTP ou SendGrid.
</details>

### Passo 6 — DOSAGEM: onde PARAR

O passo mais maduro. Nem tudo merece abstração:

- **`Pedido` e `Item`** são dados simples — não precisam de interface nem de fábrica. `new Pedido()`
  está ótimo.
- **`SemDesconto`** poderia ser só `total` sem strategy nenhuma se **nunca** houvesse variação — mas
  como já temos VIP e Black (três casos, Regra dos Três), a strategy se paga.
- **Não crie** `IOrderProcessorFactory` nem uma camada de "serviço" que só repassa. Se `OrderProcessor`
  tem uma implementação só e ninguém vai trocá-la, **a interface dele é opcional** (mantenha se for
  testar por mock; senão, YAGNI).

> 🎯 O objetivo é um design **injetável e extensível** — mas **enxuto**. Reconhecer onde parar é tão
> importante quanto saber aplicar.

---

## Solução de referência (comentada)

Chegue nela **por conta própria** primeiro. Use só pra conferir.

```csharp
// ---------- SRP: cada responsabilidade na sua classe ----------

// Cálculo (com OCP via Strategy de desconto)
public interface IDescontoStrategy { decimal Aplicar(decimal total); }
public sealed class SemDesconto   : IDescontoStrategy { public decimal Aplicar(decimal t) => t; }
public sealed class DescontoVip   : IDescontoStrategy { public decimal Aplicar(decimal t) => t * 0.90m; }
public sealed class DescontoBlack : IDescontoStrategy { public decimal Aplicar(decimal t) => t * 0.70m; }

public sealed class CalculadoraPedido
{
    public decimal Calcular(Pedido pedido, IDescontoStrategy desconto)
    {
        decimal total = pedido.Itens.Sum(i => i.Preco * i.Quantidade);
        return desconto.Aplicar(total);   // OCP: nova promoção = nova strategy, sem tocar aqui
    }
}

// ---------- OCP+LSP: meios de pagamento polimórficos, todos honram o contrato ----------
public interface IMeioPagamento { void Cobrar(decimal valor); }

public sealed class CartaoPagamento : IMeioPagamento
{
    private readonly IGatewayPagamento _gateway;               // DIP: depende da abstração
    public CartaoPagamento(IGatewayPagamento gateway) => _gateway = gateway;
    public void Cobrar(decimal valor) => _gateway.Cobrar(valor);
}

public sealed class BoletoPagamento : IMeioPagamento
{
    private readonly IBancoApi _banco;
    public BoletoPagamento(IBancoApi banco) => _banco = banco;
    public void Cobrar(decimal valor) => _banco.GerarBoleto(valor);
}

// ---------- DIP: abstrações de fronteira (injetadas) ----------
public interface IGatewayPagamento { void Cobrar(decimal valor); }
public interface IBancoApi         { void GerarBoleto(decimal valor); }
public interface IPedidoRepository { void Salvar(Pedido pedido, decimal total); }
public interface INotificador      { void Notificar(string destino, string assunto, string corpo); }

// ---------- ISP: interface enxuta por papel (relatório/newsletter foram para OUTRAS classes) ----------
public interface IProcessadorPedido
{
    void Processar(Pedido pedido, IDescontoStrategy desconto, IMeioPagamento pagamento);
    void Reembolsar(Pedido pedido);
}

// ---------- O coordenador: só orquestra, depende só de abstrações ----------
public sealed class OrderProcessor : IProcessadorPedido
{
    private readonly CalculadoraPedido _calc;
    private readonly IPedidoRepository _repo;
    private readonly INotificador _notificador;

    public OrderProcessor(CalculadoraPedido calc, IPedidoRepository repo, INotificador notificador)
    {
        _calc = calc; _repo = repo; _notificador = notificador;   // DIP: tudo injetado
    }

    public void Processar(Pedido pedido, IDescontoStrategy desconto, IMeioPagamento pagamento)
    {
        var total = _calc.Calcular(pedido, desconto);   // SRP: delega o cálculo
        pagamento.Cobrar(total);                        // OCP/LSP: qualquer meio serve
        _repo.Salvar(pedido, total);                    // DIP: não sabe se é SQL/Mongo/fake
        _notificador.Notificar(pedido.EmailCliente, "Pedido confirmado", $"Total: {total}");
    }

    public void Reembolsar(Pedido pedido) { /* usa as mesmas abstrações injetadas */ }
}

// ---------- Composição na fronteira (Program.cs / DI do .NET) ----------
// services.AddScoped<CalculadoraPedido>();
// services.AddScoped<IPedidoRepository, SqlPedidoRepository>();
// services.AddScoped<INotificador, EmailNotificador>();
// services.AddScoped<IGatewayPagamento, StripeGateway>();
// services.AddScoped<IProcessadorPedido, OrderProcessor>();
```

**O que mudou (o placar dos 5):**
- **SRP** ✅ — cada classe tem uma razão de mudar; `OrderProcessor` só coordena.
- **OCP** ✅ — nova promoção ou meio de pagamento = **nova classe**, sem editar o processador.
- **LSP** ✅ — toda `IMeioPagamento`/`IDescontoStrategy` honra o contrato; nenhum `throw` falso.
- **ISP** ✅ — relatório/newsletter saíram da interface; cada cliente depende só do seu papel.
- **DIP** ✅ — fronteiras (gateway, banco, repo, e-mail) são abstrações injetadas → **testável**.

**E a dosagem (onde paramos):** `Pedido`/`Item` continuam classes de dados simples; não criamos
fábricas triviais nem camadas que só repassam; `SemDesconto` só existe porque já há três variantes
reais. Injetável e extensível, **sem** indireção sobrando.

---

## ✅ Checklist de conclusão

- [ ] Identifiquei os cheiros do código de partida (God class, switch, new de fronteira, fat interface).
- [ ] **SRP:** separei as responsabilidades por ator/razão de mudar.
- [ ] **OCP:** troquei os `switch` por tipo por polimorfismo (Strategy).
- [ ] **LSP:** garanti que toda implementação honra o contrato (sem `throw` falso).
- [ ] **ISP:** quebrei a interface gorda por papel; relatório/newsletter saíram.
- [ ] **DIP:** inverti as dependências de fronteira e injetei pelo construtor.
- [ ] **Dosagem:** reconheci ao menos um ponto onde **NÃO** abstrair (over-engineering) foi a escolha certa.
- [ ] Consigo ligar cada refatoração a um Design Pattern (Strategy, Factory, Adapter...).

---

## 🧪 Aplicação de teste da aula

Depois desta prática, rode o quiz integrador pra fixar:

```bash
python3 SOLID/apps/modulo-07/quiz.py
```

Ele te faz perguntas cruzando os cinco princípios e corrige na hora. Quando fechar o checklist e for
bem no quiz, você está pronto pra **prova final** (`SOLID/provas/modulo-07/`) — o exame de formatura
do curso.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 7" e ele conduz as perguntas aqui no
> chat, tirando dúvidas a cada questão. Você não precisa rodar nada sozinho.
