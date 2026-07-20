# Módulo 06 — DIP: Inversão de Dependência (Prática Guiada)

> Objetivo desta prática: pegar um serviço que **dá `new` em dependências concretas de infraestrutura**
> lá dentro e **inverter a seta** — extrair as abstrações no lado do alto nível, injetá-las por
> construtor e registrar as implementações no container do .NET. No caminho, você vai **dosar**:
> decidir o que merece abstração e o que seria over-engineering.
>
> **Abordagem:** raciocínio de design conduzido no chat. Não precisamos compilar/rodar nada — o Claude
> apresenta o código, você propõe a inversão, e a gente refina passo a passo até a solução.
>
> ⏱️ Tempo estimado: 20–30 min. 💵 Custo: **zero** (é código, não infra).

---

## Como esta prática funciona

1. Leia o **código para refatorar** abaixo e identifique o cheiro do módulo (o `new` concreto no alto
   nível).
2. **Proponha** a inversão você mesmo — não corra pra solução. O Claude vai te dar **dicas
   progressivas** se você travar.
3. Ao final, compare com a **solução de referência comentada** e discuta a **dosagem** (o que valeu
   abstrair e o que não).

> 💡 Peça pro Claude "vamos fazer a prática do módulo 6" e ele conduz aqui no chat, criticando cada
> passo da sua refatoração.

---

## O código para refatorar

Um `InvoiceService` que emite uma fatura: calcula o total, persiste, gera um PDF, guarda o arquivo e
notifica o cliente. Ele instancia **tudo** por conta própria.

```csharp
public class InvoiceService
{
    public void Issue(Invoice invoice)
    {
        // 1) regra de negócio (alto nível)
        invoice.Total = invoice.Lines.Sum(l => l.Amount);
        invoice.IssuedAt = DateTime.Now;              // relógio concreto
        invoice.Number = Guid.NewGuid().ToString();   // aleatoriedade concreta

        // 2) detalhes concretos instanciados AQUI DENTRO (o smell)
        var repository = new SqlInvoiceRepository("Server=...;Database=Billing;");
        repository.Save(invoice);

        var pdf = new PdfInvoiceRenderer().Render(invoice);           // gera bytes do PDF
        new LocalFileStorage(@"C:\invoices").Write($"{invoice.Number}.pdf", pdf);

        var emailSender = new SmtpEmailSender("smtp.corp.com", 587);
        emailSender.Send(invoice.CustomerEmail, "Sua fatura", pdf);
    }
}
```

**Sintomas a reconhecer antes de mexer:**
- `new SqlInvoiceRepository(...)`, `new LocalFileStorage(...)`, `new SmtpEmailSender(...)`: acoplamento
  a **detalhes concretos de I/O** — o smell do `new` espalhado.
- `DateTime.Now` e `Guid.NewGuid()`: dependências **escondidas** do relógio e da aleatoriedade que
  tornam o método **impossível de testar de forma determinística** (o número e a data mudam a cada
  execução).
- Para testar `Issue`, você precisaria de um **banco, um disco e um SMTP reais**. Não dá pra verificar
  "o total ficou certo?" sem disparar tudo.

**Sua missão:**
1. Identificar as **fronteiras** que merecem abstração.
2. Definir as **interfaces no lado do alto nível** (o contrato que o serviço precisa).
3. Trocar cada `new` por uma dependência **injetada por construtor**.
4. **Registrar** as implementações no container do .NET.
5. **Dosar**: decidir o que NÃO abstrair e justificar.

---

## Dicas progressivas

<details>
<summary><b>Dica 1 — quais são as fronteiras?</b></summary>

Liste tudo que o método faz que é **I/O ou efeito colateral não determinístico**: persistir (banco),
renderizar PDF (CPU pura, mas plausível de variar?), gravar arquivo (disco), enviar e-mail (rede),
pegar a hora (`DateTime.Now`), gerar id (`Guid.NewGuid()`). Cada uma é candidata a virar uma abstração
injetada. Pergunte-se, em cada uma: *varia? é difícil de testar?*
</details>

<details>
<summary><b>Dica 2 — de quem é o contrato?</b></summary>

A interface expressa a **necessidade do `InvoiceService`**, não a API da classe concreta. Nomeie pelos
**verbos que a regra precisa**: `Save(invoice)`, `Write(name, bytes)`, `Send(to, subject, attachment)`,
`Now`, `NewId()`. Mantenha cada interface **enxuta** (ISP): só o que o serviço realmente usa.
</details>

<details>
<summary><b>Dica 3 — como injetar?</b></summary>

Nada de `new` no corpo. Adicione um **construtor** que recebe as interfaces e guarda em campos
`readonly`. O construtor passa a **documentar** as dependências reais da classe. Se ficarem muitos
parâmetros, isso é sinal — talvez o serviço faça coisas demais (um empurrão de **SRP**, Módulo 02).
</details>

<details>
<summary><b>Dica 4 — o relógio e o Guid</b></summary>

`DateTime.Now` e `Guid.NewGuid()` são dependências escondidas. Extraia `IClock { DateTimeOffset Now; }`
e `IIdGenerator { string NewId(); }`. Em produção, implementações que delegam ao sistema; em teste,
um `FakeClock` que devolve uma data fixa — aí o teste vira determinístico.
</details>

<details>
<summary><b>Dica 5 — registrar no container</b></summary>

No startup: `services.AddScoped<IInvoiceRepository, SqlInvoiceRepository>();` e afins. O
`InvoiceService` é resolvido pelo container, que **injeta** o grafo. Você nunca dá `new InvoiceService`.
Escolha lifetimes: repositório → **Scoped**; clock/idGen → **Singleton** (sem estado).
</details>

---

## Solução de referência (comentada)

```csharp
// === Abstrações: PERTENCEM AO ALTO NÍVEL (o InvoiceService dita os contratos que precisa) ===
public interface IInvoiceRepository { void Save(Invoice invoice); }
public interface IInvoiceRenderer   { byte[] Render(Invoice invoice); }
public interface IFileStorage       { void Write(string name, byte[] content); }
public interface IEmailSender       { void Send(string to, string subject, byte[] attachment); }
public interface IClock             { DateTimeOffset Now { get; } }
public interface IIdGenerator       { string NewId(); }

public class InvoiceService
{
    private readonly IInvoiceRepository _repository;
    private readonly IInvoiceRenderer _renderer;
    private readonly IFileStorage _storage;
    private readonly IEmailSender _emailSender;
    private readonly IClock _clock;
    private readonly IIdGenerator _idGenerator;

    // Todas as dependências ENTRAM por construtor: explícitas e substituíveis.
    public InvoiceService(
        IInvoiceRepository repository,
        IInvoiceRenderer renderer,
        IFileStorage storage,
        IEmailSender emailSender,
        IClock clock,
        IIdGenerator idGenerator)
    {
        _repository = repository;
        _renderer = renderer;
        _storage = storage;
        _emailSender = emailSender;
        _clock = clock;
        _idGenerator = idGenerator;
    }

    public void Issue(Invoice invoice)
    {
        // A regra de negócio agora só fala com CONTRATOS. Zero 'new' de concreto.
        invoice.Total = invoice.Lines.Sum(l => l.Amount);
        invoice.IssuedAt = _clock.Now;          // testável: FakeClock devolve data fixa
        invoice.Number = _idGenerator.NewId();  // testável: FakeIdGenerator devolve id fixo

        _repository.Save(invoice);
        var pdf = _renderer.Render(invoice);
        _storage.Write($"{invoice.Number}.pdf", pdf);
        _emailSender.Send(invoice.CustomerEmail, "Sua fatura", pdf);
    }
}

// === Detalhes: apenas IMPLEMENTAM os contratos (a seta agora aponta para a abstração) ===
public class SqlInvoiceRepository : IInvoiceRepository { public void Save(Invoice i) { /* SQL */ } }
public class SmtpEmailSender : IEmailSender { public void Send(string to, string s, byte[] a) { /* SMTP */ } }
public class SystemClock : IClock { public DateTimeOffset Now => DateTimeOffset.Now; }
// ...LocalFileStorage : IFileStorage, PdfInvoiceRenderer : IInvoiceRenderer, GuidIdGenerator : IIdGenerator
```

**Registro no container (startup):**

```csharp
services.AddScoped<IInvoiceRepository, SqlInvoiceRepository>();
services.AddScoped<IFileStorage, LocalFileStorage>();
services.AddScoped<IEmailSender, SmtpEmailSender>();
services.AddSingleton<IInvoiceRenderer, PdfInvoiceRenderer>();  // sem estado
services.AddSingleton<IClock, SystemClock>();
services.AddSingleton<IIdGenerator, GuidIdGenerator>();
services.AddScoped<InvoiceService>();
```

**Teste que agora é possível (e determinístico):**

```csharp
var service = new InvoiceService(
    new FakeInvoiceRepository(),        // guarda em memória, dá pra inspecionar
    new FakeRenderer(),                 // devolve bytes fixos
    new FakeFileStorage(),
    new FakeEmailSender(),              // registra o que "enviou", sem tocar em rede
    new FakeClock(new DateTimeOffset(2026, 1, 1, 0, 0, 0, TimeSpan.Zero)),
    new FakeIdGenerator("INV-1"));

service.Issue(invoice);

Assert.Equal(42m, invoice.Total);           // regra verificada sem banco/SMTP/disco reais
Assert.Equal("INV-1", invoice.Number);      // determinístico graças ao IIdGenerator
```

---

## A conversa sobre dosagem (parte essencial da prática)

Inverter **tudo** aqui foi certo? Discuta:

- ✅ **Repository, FileStorage, EmailSender, Clock, IdGenerator**: são **fronteiras de I/O ou
  não-determinismo**. Abstrair paga — dá teste determinístico e permite trocar SQL→Postgres,
  local→S3, SMTP→SendGrid sem tocar na regra. **Vale.**
- 🤔 **IInvoiceRenderer**: é **CPU pura** (gera bytes a partir do objeto), sem I/O. Se a geração de PDF
  **nunca vai variar** (só existe um formato) e você consegue testá-la direto, `new PdfInvoiceRenderer()`
  poderia ficar. Se há **chance real** de variar (PDF hoje, mas talvez HTML/CSV amanhã) ou de ser lenta
  a ponto de querer um fake no teste, aí a abstração se justifica. **É a fronteira do julgamento.**
- ❌ **`Invoice`, `InvoiceLine`, `Money`**: são **tipos de domínio/valor estáveis**. Criar `IInvoice`
  seria **over-engineering** — o smell do Módulo 01. Não abstraia o coração do domínio "por via das
  dúvidas".
- ⚠️ **Muitas dependências no construtor** (6 aqui) é um cheiro de **SRP**: talvez `Issue` esteja
  fazendo coisas demais (persistir + renderizar + arquivar + notificar). Uma direção é quebrar em
  colaboradores (ex.: um `InvoiceNotifier` que junta renderer+storage+email). DIP resolveu o
  acoplamento; SRP resolveria a **coesão**.

---

## ✅ Checklist de conclusão do módulo

- [ ] Reconheceu o smell: `new` de concreto de I/O dentro da regra de negócio.
- [ ] Extraiu as abstrações **no lado do alto nível** (contratos que o serviço precisa).
- [ ] Substituiu os `new` por **injeção por construtor** (campos `readonly`).
- [ ] Isolou o **relógio** e a **aleatoriedade** para tornar o teste **determinístico**.
- [ ] **Registrou** as implementações no container do .NET, com lifetimes coerentes.
- [ ] Sabe distinguir **DIP** (design) de **DI** (técnica) de **IoC/container** (padrão/ferramenta).
- [ ] Consegue **dosar**: justificar o que abstrair e o que seria over-engineering.

---

## 🧪 Aplicação de teste da aula

Depois desta prática, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 SOLID/apps/modulo-06/quiz.py
```

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 6" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Ao fechar o checklist e ir bem no quiz, você está pronto
> pra **prova do módulo** (`SOLID/provas/modulo-06/`) e para o **Módulo 07 — Capstone**.
