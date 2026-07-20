# Módulo 01 — Fundamentos de Design (Prática Guiada)

> Objetivo desta prática: **diagnosticar**, não curar. Você vai receber um trecho de C# recheado de
> problemas de design e sua missão é **nomear os code smells e os sintomas** — dizer *o que* está
> errado e *qual princípio* futuro atacaria cada coisa. Ainda **não** vamos refatorar a fundo (isso é
> dos próximos módulos). Aprender a enxergar o problema é 80% do caminho.
>
> **Abordagem:** conduzida no chat. Você lista os smells que enxergar; o Claude completa, corrige e
> conecta cada um ao sintoma (rigidez/fragilidade/…) e ao princípio SOLID que virá.

---

## Como funciona

1. Leia o código abaixo com calma.
2. **Antes de ver as dicas**, escreva sua lista: quais smells você vê? Qual sintoma de design podre
   cada um causa? Qual princípio SOLID (S/O/L/I/D) você chutaria pra cada?
3. Peça pro Claude: *"vamos fazer o diagnóstico da prática do módulo 1"*. Ele vai puxar sua lista,
   comparar com o gabarito e discutir cada ponto com você.

Não precisa acertar tudo — o objetivo é treinar o olhar. Errar aqui é aprendizado barato.

---

## O codigo para diagnosticar

Imagine o "coração" de um pequeno e-commerce, tudo numa classe só:

```csharp
public class GerenciadorDePedidos
{
    public decimal CalcularTotal(Pedido pedido)
    {
        decimal total = 0;
        foreach (var item in pedido.Itens)
            total += item.Preco * item.Quantidade;

        // frete decidido por um switch sobre string de tipo
        switch (pedido.TipoFrete)
        {
            case "normal":   total += pedido.Peso * 2m;  break;
            case "expresso": total += pedido.Peso * 5m;  break;
            case "retirada": total += 0m;                break;
            default: throw new ArgumentException("Frete desconhecido");
        }

        // desconto controlado por flag booleana de comportamento
        if (pedido.ClienteEhVip)
            total *= 0.90m;

        return total;
    }

    public void Finalizar(Pedido pedido, bool enviarEmail)
    {
        var total = CalcularTotal(pedido);

        // dependências concretas instanciadas com "new" aqui dentro
        var conexao = new SqlConnection("Server=prod;Database=loja;");
        conexao.Open();
        var cmd = new SqlCommand($"INSERT INTO Pedidos VALUES ({total})", conexao);
        cmd.ExecuteNonQuery();
        conexao.Close();

        // formatação de apresentação misturada com regra de negócio
        string recibo = "<html><body><h1>Pedido</h1><p>Total: R$ " + total + "</p></body></html>";
        File.WriteAllText($"recibos/{pedido.Id}.html", recibo);

        if (enviarEmail)
        {
            var smtp = new SmtpClient("smtp.loja.com", 587);
            smtp.Send("loja@loja.com", pedido.ClienteEmail, "Pedido", recibo);
        }

        Console.WriteLine("Pedido finalizado");
    }
}
```

Uma classe: cálculo de negócio, frete, desconto, **acesso a banco**, **geração de HTML**, **gravação
de arquivo**, **envio de e-mail** e log. Comece sua lista.

---

## Dicas progressivas

> Use uma de cada vez, só se travar. O objetivo é você chegar sozinho o máximo possível.

**Dica 1 — Conte as responsabilidades.** Quantas "razões diferentes de mudar" essa classe tem? Se o
formato do recibo mudar, você mexe aqui. Se trocar o banco, mexe aqui. Se mudar a regra de VIP, aqui.
Quantos *atores/motivos* independentes tocam essa classe? (Pense: qual princípio fala de "uma razão
para mudar"?)

**Dica 2 — Procure o `switch` sobre tipo.** O `switch (pedido.TipoFrete)` cresce a cada novo tipo de
frete — e cada crescimento **edita** um método que já funcionava. Que sintoma isso é? Qual princípio
transformaria isso em "adicionar uma classe" em vez de "editar o método"?

**Dica 3 — Ache as flags booleanas de comportamento.** `Finalizar(..., bool enviarEmail)` e o
`if (pedido.ClienteEhVip)` ligam/desligam *caminhos de comportamento*. Que princípio isso costuma
prenunciar?

**Dica 4 — Siga os `new`.** `new SqlConnection`, `new SmtpClient` — dependências **concretas**
instanciadas dentro da classe. Isso é acoplamento alto: dá pra testar `Finalizar` sem um banco e um
servidor SMTP reais? Qual princípio inverteria isso, fazendo a classe depender de *abstrações*?

**Dica 5 — Nomeie os sintomas.** Amarre cada smell a um dos quatro sintomas: essa classe é **rígida**
(mudar o banco cascateia)? **frágil** (mexer no HTML pode quebrar o cálculo)? **imóvel** (dá pra reusar
o cálculo de total noutro projeto sem arrastar SQL e SMTP junto)? **viscosa** (é mais fácil jogar mais
um `case`/`if` do que refatorar)?

---

## Solução de referência (diagnóstico comentado)

> Confira **depois** de montar sua própria lista.

**Smell principal — Classe God / baixa coesão.** `GerenciadorDePedidos` acumula pelo menos cinco
responsabilidades que mudam por razões diferentes: (1) regra de negócio (total, frete, desconto),
(2) persistência (SQL), (3) apresentação (HTML do recibo), (4) infraestrutura de e-mail (SMTP),
(5) log. → **Sintoma:** rigidez e fragilidade. → **Princípio:** **SRP** (Módulo 02) vai separar isso
por "razão de mudar".

**Smell — `switch` sobre tipo (`TipoFrete`).** Cada novo tipo de frete obriga a **editar** o método.
→ **Sintoma:** viscosidade (mais fácil jogar um `case`) e fragilidade. → **Princípio:** **OCP** (Módulo
03) — troca o `switch` por polimorfismo (uma estratégia de frete por tipo), aberto a extensão sem
editar o existente.

**Smell — flags booleanas de comportamento (`enviarEmail`, `ClienteEhVip`).** O booleano acende
caminhos de comportamento dentro do método. → **Princípio:** também **OCP** — comportamentos deveriam
ser objetos/estratégias separados, não `if`s internos.

**Smell — `new` de dependências concretas (`SqlConnection`, `SmtpClient`).** Acoplamento direto a
implementações concretas: impossível testar sem banco/SMTP reais, impossível trocar o provedor.
→ **Sintoma:** alto acoplamento → fragilidade + imobilidade. → **Princípio:** **DIP** (Módulo 06) —
depender de abstrações (`IRepositorioDePedidos`, `INotificador`) injetadas, não de `new` concreto.

**Smell — mistura de camadas (negócio + SQL string + HTML + arquivo).** Concatenar SQL e HTML na mão,
gravar arquivo e calcular preço no mesmo lugar. → **Sintoma:** baixa coesão + imobilidade (não dá pra
reusar o cálculo sem arrastar o resto). → **Princípio:** **SRP** separa as camadas.

**O que ainda NÃO fizemos:** não escrevemos a versão refatorada — isso é dos próximos módulos, um
princípio de cada vez. E lembre da **dosagem**: num script de uso único que roda uma vez e é jogado
fora, essa classe "feia" poderia até ser aceitável. O problema aqui é que é o *coração de um sistema
que vai mudar sempre* — é onde o custo de mudança realmente importa.

---

## ✅ Checklist de conclusão do módulo

- [ ] Entendi que design bom = **barato de mudar** (código é lido/mudado mais do que escrito).
- [ ] Sei nomear os **4 sintomas**: rigidez, fragilidade, imobilidade, viscosidade.
- [ ] Distingo **acoplamento** (dependência, queremos baixo) de **coesão** (foco, queremos alta).
- [ ] Reconheço os principais **code smells** e qual princípio ataca cada um.
- [ ] Sei o **mapa dos 5** (S/O/L/I/D) e entendo que princípios são **heurísticas** (dosagem/YAGNI).
- [ ] Diagnostiquei a `GerenciadorDePedidos`, nomeando smells → sintomas → princípios.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 SOLID/apps/modulo-01/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 1 de SOLID" e ele conduz as perguntas
> aqui no chat, tirando suas dúvidas a cada questão. Quando fechar o checklist e for bem no quiz, você
> está pronto pra **prova do módulo** (`SOLID/provas/modulo-01/`) e para o **Módulo 02 — SRP**.
