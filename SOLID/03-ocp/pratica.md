# Módulo 03 — OCP (Prática Guiada: refatoração no chat)

> Objetivo desta prática: pegar um trecho de C# com o **smell do `switch` que cresce por tipo** e
> refatorá-lo, passo a passo, para **polimorfismo / Strategy**, respeitando OCP. Não há código pra
> rodar nem nuvem — a prática é **raciocínio de design conduzido no chat**. O Claude apresenta o
> código, você propõe a refatoração, e ele conduz/critica até a solução.
>
> **Fecho importante:** ao final, discutimos a **dosagem** — essa abstração se justifica *aqui*?

---

## O código para refatorar

Um sistema de e-commerce calcula o **valor do frete** conforme a transportadora escolhida. Toda
transportadora nova que entra no catálogo obriga a mexer no mesmo lugar:

```csharp
public enum Carrier { Correios, Jadlog, LoggiExpress }

public class Order
{
    public Carrier Carrier { get; set; }
    public decimal Weight { get; set; }   // kg
    public string State { get; set; }     // UF de destino
}

public class ShippingCalculator
{
    public decimal Calculate(Order order)
    {
        switch (order.Carrier)
        {
            case Carrier.Correios:
                return 10m + order.Weight * 2m;

            case Carrier.Jadlog:
                var jadlog = 15m + order.Weight * 1.5m;
                if (order.State == "SP") jadlog *= 0.9m;   // desconto regional
                return jadlog;

            case Carrier.LoggiExpress:
                return 25m + order.Weight * 1m;            // express, taxa fixa alta

            default:
                throw new ArgumentException("Transportadora desconhecida");
        }
    }
}
```

Amanhã entra a **"Total Express"**. Depois a **"Azul Cargo"**. Cada uma = mais um `case` editado
neste `switch`, e o mesmo padrão pode reaparecer (ex.: um `switch(order.Carrier)` que decide o prazo
de entrega em outra classe).

**Sua missão:** refatorar isto para respeitar OCP — adicionar uma transportadora nova deve ser
**criar uma classe**, não **editar o `ShippingCalculator`**.

---

## Dicas progressivas

Tente antes de olhar. Se travar, revele uma dica de cada vez.

<details>
<summary>Dica 1 — Ache o eixo de variação</summary>

Qual é a coisa que **muda a cada requisito novo**? A **transportadora** (e a regra de cálculo dela).
Esse é o seu **ponto de variação**. É *ele* que você vai fechar contra modificação — não o resto.
</details>

<details>
<summary>Dica 2 — Extraia a abstração</summary>

Cada `case` do `switch` é, na verdade, uma **estratégia de cálculo de frete**. Crie uma interface
que capture "calcular frete de um pedido":

```csharp
public interface IShippingStrategy
{
    decimal Calculate(Order order);
}
```
</details>

<details>
<summary>Dica 3 — Um case → uma classe</summary>

Mova o corpo de cada `case` para a sua própria implementação (`CorreiosShipping`,
`JadlogShipping`, `LoggiExpressShipping`). O `switch` inteiro deixa de existir dentro do
calculador — o polimorfismo faz a escolha.
</details>

<details>
<summary>Dica 4 — Quem escolhe a estratégia?</summary>

Alguém ainda precisa mapear `Carrier` → estratégia. Mas isso vira **configuração** (um dicionário,
ou o **container de DI** do .NET), não um `switch` de comportamento espalhado. Fechar a *seleção*
num único ponto de composição é ok; o que não pode é a *lógica de cada frete* obrigar edição.
</details>

---

## Solução de referência (comentada)

```csharp
// 1) A abstração: o "encaixe" fechado. Todo cálculo de frete se pluga aqui.
public interface IShippingStrategy
{
    decimal Calculate(Order order);
}

// 2) Cada transportadora vira uma classe: o comportamento mora JUNTO do tipo.
public class CorreiosShipping : IShippingStrategy
{
    public decimal Calculate(Order order) => 10m + order.Weight * 2m;
}

public class JadlogShipping : IShippingStrategy
{
    public decimal Calculate(Order order)
    {
        var price = 15m + order.Weight * 1.5m;
        if (order.State == "SP") price *= 0.9m;
        return price;
    }
}

public class LoggiExpressShipping : IShippingStrategy
{
    public decimal Calculate(Order order) => 25m + order.Weight * 1m;
}

// 3) O calculador some ou vira um simples delegador. Nenhum switch de comportamento aqui.
public class ShippingCalculator
{
    private readonly IShippingStrategy _strategy;
    public ShippingCalculator(IShippingStrategy strategy) => _strategy = strategy;

    public decimal Calculate(Order order) => _strategy.Calculate(order);
}
```

E a **seleção** vira composição — num único ponto, resolvida por DI:

```csharp
// Program.cs / composição — mapear Carrier -> estratégia num só lugar (fábrica ou keyed services do .NET 8).
services.AddKeyedScoped<IShippingStrategy, CorreiosShipping>(Carrier.Correios);
services.AddKeyedScoped<IShippingStrategy, JadlogShipping>(Carrier.Jadlog);
services.AddKeyedScoped<IShippingStrategy, LoggiExpressShipping>(Carrier.LoggiExpress);
```

### O teste de OCP: chega a "Total Express"

```csharp
public class TotalExpressShipping : IShippingStrategy
{
    public decimal Calculate(Order order) => 12m + order.Weight * 1.8m;
}
// + uma linha de registro no ponto de composição.
```

**Uma classe nova, um registro.** `ShippingCalculator`, `CorreiosShipping`, `JadlogShipping` — nada
disso foi tocado. **Aberto para extensão, fechado para modificação.** ✅

> 💡 Note a diferença entre os dois `switch`. O `switch` de **comportamento** (como calcular cada
> frete) foi eliminado — era ele que violava OCP. Um mapeamento de **seleção** (Carrier → estratégia)
> num único ponto de composição é aceitável e centralizado; só ele muda quando entra uma
> transportadora, e ele existe pra isso.

---

## O outro lado: quando NÃO refatorar (dosagem)

Antes de aplaudir, faça a pergunta honesta: **essa abstração se justifica?**

- Se o sistema tem **três transportadoras estáveis há dois anos** e nenhuma nova no horizonte, o
  `switch` original talvez estivesse **bom o suficiente**. Refatorar por reflexo é **YAGNI**.
- **Sinal verde para refatorar** (o caso deste exercício): as transportadoras **estão entrando com
  frequência**, o `switch(order.Carrier)` **se repete** em outros lugares (frete, prazo,
  rastreamento), e mexer nele **já causou regressão** antes. Aí o padrão **emergiu** — pela **Rule
  of Three**, é hora de abstrair.

> 🎯 O que você deve saber justificar ao Claude: (1) qual era o **ponto de variação**, (2) por que a
> refatoração deixou o código **fechado para modificação** nesse eixo, e (3) em que cenário essa
> mesma abstração seria **over-engineering**.

---

## ✅ Checklist de conclusão da prática

- [ ] Identifiquei o **eixo de variação** (a transportadora/regra de frete).
- [ ] Extraí a abstração `IShippingStrategy` e movi cada `case` para sua própria classe.
- [ ] O `switch` de **comportamento** deixou de existir dentro do calculador.
- [ ] Consigo adicionar uma transportadora nova **sem editar** as classes existentes.
- [ ] Sei **justificar a dosagem**: quando essa refatoração vale a pena e quando seria YAGNI.

---

## 🧪 Aplicação de teste da aula

Depois desta prática, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 SOLID/apps/modulo-03/quiz.py
```

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 3" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Fechado o checklist e indo bem no quiz, você está pronto
> pra **prova do módulo** (`SOLID/provas/modulo-03/`) e para o **Módulo 04 — LSP (Substituição de
> Liskov)**.
