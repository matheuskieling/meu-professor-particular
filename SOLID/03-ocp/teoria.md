# Módulo 03 — OCP: Aberto para Extensão, Fechado para Modificação (Teoria)

> Objetivo do módulo: aprender a **adicionar comportamento novo criando código novo**, em vez de
> editar código que já está testado e em produção. O vilão é um smell que você já viu mil vezes: o
> **`switch`/`if-else` que cresce em cima de um "tipo"** a cada requisito novo. A cura é
> **polimorfismo e abstração** (muitas vezes na forma do padrão **Strategy**). E, tão importante
> quanto: **saber a dose** — OCP aplicado cedo demais vira over-engineering.

---

## 1. A definição: aberto para extensão, fechado para modificação

O princípio foi enunciado por **Bertrand Meyer** em 1988 e popularizado por **Robert C. Martin
(Uncle Bob)**:

> **Entidades de software (classes, módulos, funções) devem ser abertas para EXTENSÃO, mas fechadas
> para MODIFICAÇÃO.**

À primeira vista soa como um paradoxo — como algo pode ser "fechado" e "aberto" ao mesmo tempo? A
chave é entender o que significa cada metade:

- **Aberto para extensão:** o *comportamento* do sistema pode crescer. Você consegue fazê-lo fazer
  coisas novas.
- **Fechado para modificação:** você consegue isso **sem editar** o código-fonte que já existe e já
  funciona.

Ou seja: **comportamento novo entra na forma de código NOVO, não como uma edição no código velho.**

### Por que "fechado para modificação" importa tanto

Código que já está **testado e rodando em produção** é um **ativo**. Cada vez que você reabre esse
arquivo pra encaixar um caso novo, você:

- corre **risco de regressão** (quebrar o que já funcionava);
- invalida testes e revisões que já tinham sido feitos;
- transforma uma classe num **ímã de modificação** — todo mundo mexe nela o tempo todo.

Repare a conexão com o **Módulo 01**: uma classe que precisa ser editada a cada requisito novo é o
retrato da **rigidez** (mudar dói) e da **fragilidade** (mudar aqui quebra ali).

### Analogia da tomada

Pense na **tomada** da parede. Você pluga um carregador, um ventilador, uma TV — aparelhos que nem
existiam quando a casa foi construída — **sem reabrir a parede**. A *interface* (o formato da
tomada) é **fechada**: ninguém a modifica. O que se **pluga** nela é **aberto**: infinitos aparelhos
novos. OCP é isso: você projeta um "encaixe" estável e faz o novo se plugar nele.

---

## 2. O smell central: o `switch` que cresce por tipo

O jeito mais rápido de reconhecer uma violação de OCP é procurar por um **`switch` ou `if-else` que
decide comportamento com base num "tipo"** (um `enum`, uma `string`, uma flag), e que **cresce a
cada requisito novo**.

Exemplo canônico — um calculador de área:

```csharp
public enum ShapeType { Circle, Rectangle }

public class Shape
{
    public ShapeType Type { get; set; }
    public double Radius { get; set; }
    public double Width { get; set; }
    public double Height { get; set; }
}

public class AreaCalculator
{
    public double Area(Shape shape)
    {
        switch (shape.Type)
        {
            case ShapeType.Circle:
                return Math.PI * shape.Radius * shape.Radius;
            case ShapeType.Rectangle:
                return shape.Width * shape.Height;
            default:
                throw new ArgumentException("Forma desconhecida");
        }
    }
}
```

Agora chega o requisito: **"precisamos de triângulos"**. O que você é obrigado a fazer?

1. Adicionar `Triangle` ao `enum`.
2. Adicionar os campos `Base`/`Altura` na classe `Shape` (que agora carrega campos de todas as formas).
3. **Editar** o `switch` do `AreaCalculator` — o mesmo arquivo testado — pra incluir mais um `case`.

Isso **viola OCP**: você **modificou** código existente pra **estender** comportamento. E o pior: o
mesmo `switch(shape.Type)` costuma **se repetir** em vários lugares (um pra calcular área, outro pra
desenhar, outro pra serializar) — cada forma nova é uma caçada por todos os `switch` espalhados.

### O smell aparece disfarçado

Não é só forma geométrica. O mesmo cheiro em outros contextos:

- **Desconto por tipo de cliente:** `if (cliente.Tipo == Tipo.VIP) ... else if (Tipo.Normal) ...`.
- **Exportar relatório por formato:** `if (format == "PDF") ... else if (format == "CSV") ...`.
- **Cálculo de frete por transportadora**, **cálculo de imposto por região**, etc.

Em todos, o padrão é o mesmo: **um dado de "tipo" comandando um `switch`, e a lista de casos só
cresce, nunca fecha.** Isso é rigidez + fragilidade do Módulo 01 na veia.

---

## 3. A solução: polimorfismo e abstração

A cura para o `switch` por tipo é quase sempre a mesma: **mover o comportamento pra dentro de cada
tipo, atrás de uma abstração** — e deixar o **polimorfismo** fazer o "switch" por você, em runtime.

Voltando à área. Em vez de um `enum` burro + `switch`, cada forma **sabe calcular a própria área**:

```csharp
public abstract class Shape
{
    public abstract double Area();
}

public class Circle : Shape
{
    public double Radius { get; init; }
    public override double Area() => Math.PI * Radius * Radius;
}

public class Rectangle : Shape
{
    public double Width { get; init; }
    public double Height { get; init; }
    public override double Area() => Width * Height;
}
```

E o calculador... praticamente some. Vira uma chamada polimórfica:

```csharp
// Antes: um switch de N casos. Depois: uma linha.
double area = shape.Area();
```

Agora chega o requisito do **triângulo**. O que você faz?

```csharp
public class Triangle : Shape
{
    public double Base { get; init; }
    public double Height { get; init; }
    public override double Area() => Base * Height / 2;
}
```

**Só isso.** Uma classe **nova**. Você **não tocou** em `Circle`, `Rectangle`, nem no código que
chama `shape.Area()`. Isso é OCP na prática: **aberto para extensão** (adicionei `Triangle`),
**fechado para modificação** (não editei nada que já funcionava).

| | Antes (switch por tipo) | Depois (polimorfismo) |
|---|---|---|
| Onde mora o cálculo? | Fora, no `AreaCalculator` | Dentro de cada forma |
| Adicionar `Triangle` | **Editar** enum, `Shape` e o `switch` | **Criar** uma classe nova |
| Risco de regressão | Alto (reabre código testado) | Baixo (código velho intocado) |
| `switch` repetido em N lugares | Editar todos | Não existe |

---

## 4. Strategy, injeção e "pontos de variação"

O padrão **Strategy** é a **materialização mais comum de OCP**: você **encapsula "o que varia" atrás
de uma interface** e **injeta** a implementação desejada. Comportamento novo = **nova implementação
registrada**, sem tocar em quem usa.

Pegue o desconto por tipo de cliente. Em vez do `if` que cresce:

```csharp
public interface IDiscountPolicy
{
    decimal Apply(decimal amount);
}

public class RegularDiscount : IDiscountPolicy
{
    public decimal Apply(decimal amount) => amount;               // 0%
}

public class VipDiscount : IDiscountPolicy
{
    public decimal Apply(decimal amount) => amount * 0.90m;       // 10%
}

public class OrderService
{
    private readonly IDiscountPolicy _discount;

    // A política chega por injeção — o serviço não sabe (nem quer saber) qual é.
    public OrderService(IDiscountPolicy discount) => _discount = discount;

    public decimal Total(decimal amount) => _discount.Apply(amount);
}
```

Precisa de um desconto de **Black Friday**? Crie `BlackFridayDiscount : IDiscountPolicy` e registre.
`OrderService` **não muda**. Repare que isso é exatamente a ponte para o **DIP (Módulo 06)**:
`OrderService` depende da **abstração** `IDiscountPolicy`, não das implementações concretas — e o
**container de DI do .NET** faz a ligação:

```csharp
// Program.cs — registra a estratégia; trocar/adicionar comportamento é config, não edição de código.
services.AddScoped<IDiscountPolicy, VipDiscount>();
services.AddScoped<OrderService>();
```

### "Pontos de variação": você escolhe os eixos

Aqui está a sutileza que separa quem entende OCP de quem decora: **você não consegue estar fechado
contra TODA mudança.** Se você tentar abstrair tudo, cria um sistema impossível de entender.

O que OCP pede é: **identifique o eixo ao longo do qual você antecipa variação** — o "ponto de
variação" — e feche a modificação **só nesse eixo**.

- Num sistema de **frete**, o ponto de variação é a **transportadora/regra de frete** → abstraia
  `IShippingStrategy`.
- Num **exportador**, o ponto é o **formato** → abstraia `IExporter`.
- Mas o *fluxo* que orquestra o pedido talvez varie pouco — não precisa de abstração especulativa ali.

OCP é uma aposta consciente: "**esta** dimensão vai mudar, então eu a deixo plugável". Você paga o
preço da indireção **onde a variação é real**, e só ali.

---

## 5. Dosagem: OCP prematuro, YAGNI e a Rule of Three

Este é o ponto mais importante do módulo — e o mais ignorado. **OCP aplicado cedo demais é um
problema, não uma virtude.**

Criar uma interface + hierarquia de classes para algo que **nunca variou** é **abstração
especulativa** — puro **over-engineering**, movido pelo medo de uma mudança que talvez nunca venha.
O nome disso é **YAGNI**: *You Aren't Gonna Need It*.

> ⚠️ Uma `IExporter` com uma única implementação `PdfExporter`, para um relatório que só exporta PDF
> e nunca precisou de outro formato, é **pior** que um método `ExportPdf()` direto: mais arquivos,
> mais indireção, mais "onde é que isso é ligado?", e **zero** benefício. Você pagou o custo da
> flexibilidade sem nunca colher o retorno.

### A regra prática: simples primeiro

- **Da primeira vez**, escreva o mais **simples** que resolve. Um `if` direto está **ok**. Um método
  concreto está **ok**. Não abstraia por reflexo.
- **Refatore para OCP quando o padrão EMERGE** — quando você *vê* a variação acontecendo, não quando
  você *imagina* que ela pode acontecer.

### Rule of Three

Uma heurística concreta pra decidir a hora:

> **Rule of Three:** na **primeira** vez, faça direto. Na **segunda** variação, você *nota* a
> duplicação, mas talvez ainda tolere. Na **terceira**, o eixo de variação já está **evidente** — aí
> sim, refatore para uma abstração (Strategy/polimorfismo).

Na terceira ocorrência, você não está mais adivinhando: o padrão se **provou**. Abstrair agora é
baseado em evidência, não em especulação.

### O equilíbrio

OCP se **apoia** em polimorfismo (**LSP**, Módulo 04 — os subtipos precisam ser substituíveis de
verdade) e em abstrações (**DIP**, Módulo 06). Mas o objetivo final é sempre o do Módulo 01:
**baixar o custo de mudar**. Rigidez (não conseguir estender) e over-engineering (abstrair o que
não varia) são **os dois lados do mesmo erro** — errar a dose. A maestria em OCP é menos sobre
"criar interfaces" e mais sobre **saber quando NÃO criar**.

---

## 6. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| OCP | Aberto para extensão (código novo), fechado para modificação (não edita o velho). |
| Extensão | Adicionar comportamento criando classes/implementações novas. |
| Modificação | Editar código-fonte já existente e testado (o que queremos evitar). |
| Switch por tipo | O smell: `switch`/`if` sobre um enum/tipo que cresce a cada caso novo. |
| Polimorfismo | Deixar o objeto certo executar seu próprio método em runtime — o "switch" implícito. |
| Strategy | Padrão que encapsula "o que varia" atrás de uma interface injetável. |
| Ponto de variação | O eixo em que você antecipa mudança e decide fechar contra modificação. |
| Abstração especulativa | Criar abstração para uma variação que ainda não existe (over-engineering). |
| YAGNI | "You Aren't Gonna Need It": não construa flexibilidade que ninguém pediu. |
| Rule of Three | Faça direto na 1ª vez; abstraia quando o padrão se prova (por volta da 3ª). |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Explique OCP com suas palavras. O que significa "fechado para modificação" e por que isso protege
   código em produção?
2. Você viu um `switch(pedido.TipoPagamento)` que ganha um `case` novo a cada meio de pagamento.
   Qual princípio está sendo violado e por quê?
3. Como o **polimorfismo** transforma um `switch` por tipo em "adicionar uma classe nova"? O que
   acontece com o código que fazia o `switch`?
4. O que é um "ponto de variação"? Por que você **não** deve tentar estar fechado contra toda
   mudança possível?
5. Quando aplicar OCP é **cedo demais**? Explique a Rule of Three e dê um exemplo de abstração que
   seria over-engineering.

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
