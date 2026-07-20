# Módulo 02 — SRP (Prática Guiada: refatoração no chat)

> Objetivo desta prática: pegar uma **God class** real em C# e refatorá-la aplicando o SRP —
> **separando responsabilidades por ator** e deixando um **coordenador fino**. Sem estilhaçar em
> micro-classes. Não há nada pra rodar: é **raciocínio de design conduzido no chat**. O Claude
> apresenta o código, você propõe a separação, e ele critica/guia com dicas progressivas.
>
> ⏱️ Tempo estimado: 20–30 min. Formato: você pensa, propõe, e a gente refina junto.

---

## O código de partida

Uma classe que gera o relatório mensal de um cliente. Ela **busca os dados no banco**, **calcula o
resumo**, **formata como texto** e **envia por e-mail** — tudo num método só:

```csharp
public class ReportService
{
    public void GenerateAndSendMonthlyReport(int customerId)
    {
        // 1) Busca no banco
        using var conn = new SqlConnection(_connString);
        conn.Open();
        var cmd = new SqlCommand(
            "SELECT Amount, Date FROM Transactions WHERE CustomerId = @id", conn);
        cmd.Parameters.AddWithValue("@id", customerId);
        var transactions = new List<Transaction>();
        using (var reader = cmd.ExecuteReader())
            while (reader.Read())
                transactions.Add(new Transaction(
                    reader.GetDecimal(0), reader.GetDateTime(1)));

        // 2) Calcula o resumo
        decimal total = 0;
        foreach (var t in transactions) total += t.Amount;
        var average = transactions.Count > 0 ? total / transactions.Count : 0;

        // 3) Formata como texto
        var sb = new StringBuilder();
        sb.AppendLine($"Relatório do cliente {customerId}");
        sb.AppendLine($"Transações: {transactions.Count}");
        sb.AppendLine($"Total: {total:C}");
        sb.AppendLine($"Média: {average:C}");
        var body = sb.ToString();

        // 4) Envia por e-mail
        var smtp = new SmtpClient("smtp.empresa.com");
        var mail = new MailMessage("relatorios@empresa.com",
            GetCustomerEmail(customerId)) { Subject = "Seu relatório mensal", Body = body };
        smtp.Send(mail);
    }
}
```

Sua missão: refatorar isso aplicando SRP, com a dosagem certa.

---

## Passo 1 — Identifique os atores (razões para mudar)

Antes de mover uma linha, responda: **quantos atores diferentes pediriam mudanças aqui?** Passe o
olho pelos quatro blocos e diga, para cada um, *quem* pediria a mudança e *por quê*.

<details>
<summary>💡 Dica progressiva 1</summary>

Pense em quem "reclama" quando cada parte precisa mudar:
- O bloco de **busca** muda se o **DBA** troca o esquema ou a tecnologia de banco.
- O **cálculo do resumo** muda se o **negócio** redefine o que é "total"/"média".
- A **formatação** muda se alguém pede outro **layout**/idioma do relatório.
- O **envio** muda se a **infra** troca SMTP por outro canal (SendGrid, fila, etc.).

Quatro razões distintas para mudar → quatro responsabilidades.
</details>

---

## Passo 2 — Uma classe por responsabilidade

Proponha os nomes das classes que vão surgir. Bons nomes **revelam o ator** e descrevem *uma* coisa
(fuja de `ReportManager`, `ReportUtil` ou nomes com "And").

<details>
<summary>💡 Dica progressiva 2</summary>

Algo como:
- `TransactionRepository` — busca os dados (ator: DBA/infra de dados).
- `ReportSummaryCalculator` — calcula total/média (ator: negócio).
- `ReportFormatter` — monta o texto (ator: quem define o layout).
- `EmailSender` — envia (ator: infra de comunicação).

Cada uma tem **uma** razão para mudar.
</details>

---

## Passo 3 — O coordenador fino

Quem chama as quatro peças na ordem certa? Defina um coordenador que **orquestra** sem **reimplementar**
as regras. Ele deve receber as peças por injeção (construtor) e apenas encadear as chamadas.

<details>
<summary>💡 Dica progressiva 3</summary>

O coordenador `ReportService` fica com um método curto:
1. `repository.GetTransactions(customerId)`
2. `calculator.Summarize(transactions)`
3. `formatter.Format(summary)`
4. `emailSender.Send(...)`

Se você se pegar escrevendo `SELECT` ou `total += ...` dentro do coordenador, ele voltou a ser uma
God class. O coordenador só **decide a ordem**.
</details>

---

## Passo 4 — Cheque a dosagem

Antes de declarar vitória, faça o teste anti-over-engineering:

- **Total e média** sempre mudam juntos, pela mesma razão (definição de "resumo")? Então ficam
  **juntos** em `ReportSummaryCalculator` — não crie um `TotalCalculator` e um `AverageCalculator`
  separados. Isso seria estilhaçar.
- Alguma peça ficou **anêmica** (só passa dados adiante, sem lógica)? Se sim, talvez ela não precise
  existir — reavalie.
- Pergunta-bússola final: cada classe que sobrou é editada por **um único ator**? Se sim, dosagem sã.

---

## Solução de referência (comentada)

Tente antes de abrir. Compare com a sua — pode haver variações igualmente válidas.

<details>
<summary>✅ Ver solução de referência</summary>

```csharp
// Ator: DBA/infra de dados — só persistência/leitura
public class TransactionRepository
{
    private readonly string _connString;
    public TransactionRepository(string connString) => _connString = connString;

    public IReadOnlyList<Transaction> GetByCustomer(int customerId)
    {
        // SQL isolado aqui; se o banco mudar, só esta classe muda
        // ...
        return transactions;
    }
}

// Ator: negócio — o que é "resumo" do relatório
public record ReportSummary(int Count, decimal Total, decimal Average);

public class ReportSummaryCalculator
{
    // Total e média mudam pela MESMA razão → ficam juntos (dosagem correta)
    public ReportSummary Summarize(IReadOnlyList<Transaction> transactions)
    {
        var total = transactions.Sum(t => t.Amount);
        var avg = transactions.Count > 0 ? total / transactions.Count : 0m;
        return new ReportSummary(transactions.Count, total, avg);
    }
}

// Ator: quem define o layout do relatório
public class ReportFormatter
{
    public string Format(int customerId, ReportSummary s)
    {
        var sb = new StringBuilder();
        sb.AppendLine($"Relatório do cliente {customerId}");
        sb.AppendLine($"Transações: {s.Count}");
        sb.AppendLine($"Total: {s.Total:C}");
        sb.AppendLine($"Média: {s.Average:C}");
        return sb.ToString();
    }
}

// Ator: infra de comunicação — só envio
public class EmailSender
{
    public void Send(string to, string subject, string body) { /* SMTP isolado */ }
}

// Coordenador FINO: orquestra, não contém as regras
public class ReportService
{
    private readonly TransactionRepository _repository;
    private readonly ReportSummaryCalculator _calculator;
    private readonly ReportFormatter _formatter;
    private readonly EmailSender _email;
    private readonly ICustomerDirectory _customers;

    public ReportService(TransactionRepository repository,
                         ReportSummaryCalculator calculator,
                         ReportFormatter formatter,
                         EmailSender email,
                         ICustomerDirectory customers)
    {
        _repository = repository; _calculator = calculator;
        _formatter = formatter; _email = email; _customers = customers;
    }

    public void GenerateAndSendMonthlyReport(int customerId)
    {
        var transactions = _repository.GetByCustomer(customerId);
        var summary = _calculator.Summarize(transactions);
        var body = _formatter.Format(customerId, summary);
        _email.Send(_customers.GetEmail(customerId), "Seu relatório mensal", body);
    }
}
```

**Por que este design respeita o SRP (e a dosagem):**
- Cada classe tem **uma razão para mudar** (um ator dono): banco, negócio, layout, comunicação.
- `ReportSummaryCalculator` mantém `Total` **e** `Average` juntos — eles mudam pela mesma razão;
  separá-los seria over-engineering.
- `ReportService` é **fino**: encadeia as peças e nada mais. Nenhum SQL, cálculo ou template mora nele.
- Testável: `ReportSummaryCalculator` e `ReportFormatter` se testam com dados em memória, sem banco
  nem SMTP. Isso, por si só, prova que o acoplamento acidental sumiu.
</details>

---

## ✅ Checklist de conclusão do módulo

- [ ] Identifiquei os **atores** (razões para mudar) da God class de partida.
- [ ] Extraí **uma classe por responsabilidade**, com nomes que revelam o ator.
- [ ] Defini um **coordenador fino** que orquestra sem reimplementar as regras.
- [ ] Não estilhacei o que **muda junto** (ex.: total + média ficaram na mesma classe).
- [ ] Sei explicar por que cada classe agora tem **uma única razão para mudar**.
- [ ] Consigo distinguir SRP **correto** do slogan ingênuo "faz só uma coisa".

---

## 🧪 Aplicação de teste da aula

Depois desta prática, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 SOLID/apps/modulo-02/quiz.py
```

Ou peça pro Claude "vamos fazer o quiz do módulo 2" e ele conduz as perguntas aqui no chat, tirando
suas dúvidas a cada questão. Quando fechar o checklist e for bem no quiz, você está pronto pra
**prova do módulo** (`SOLID/provas/modulo-02/`) e para o **Módulo 03 — OCP (Aberto/Fechado)**.
