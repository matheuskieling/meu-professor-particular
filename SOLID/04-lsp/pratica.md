# Módulo 04 — LSP: Substituição de Liskov (Prática Guiada)

> Objetivo desta prática: pegar uma hierarquia que **viola LSP** e refatorá-la para que **todo
> subtipo substitua o supertipo sem surpresas**. Não há nuvem, custo nem execução obrigatória — é
> **refatoração de código conduzida no chat**. Você raciocina o design; o Claude guia com dicas
> progressivas e compara sua proposta com a solução de referência.
>
> **Como funciona:** leia o código de partida, tente identificar **qual contrato** o subtipo quebra
> e proponha a correção. Só então abra a solução. O objetivo é o **critério**, não decorar a resposta.

---

## O código de partida

Um sistema de e-commerce calcula o custo de **frete** por tipo de entrega. Alguém modelou assim,
achando que "entrega expressa **é uma** entrada de frete":

```csharp
public class Shipment
{
    public decimal Weight { get; set; }         // kg
    public decimal DistanceKm { get; set; }

    // Contrato: retorna SEMPRE um custo >= 0, calculado por peso e distância.
    public virtual decimal CalculateCost()
        => Weight * 0.5m + DistanceKm * 0.1m;
}

public class ExpressShipment : Shipment
{
    public override decimal CalculateCost()
        => base.CalculateCost() * 1.8m; // ok: mais caro, mas ainda é um custo válido
}

// Entrega "grátis" para brindes/amostras.
public class FreeSampleShipment : Shipment
{
    public override decimal CalculateCost()
        => throw new NotSupportedException("Amostra não tem cálculo de frete");
}

// Retirada na loja: sem custo, mas alguém decidiu sinalizar com -1.
public class StorePickupShipment : Shipment
{
    public override decimal CalculateCost() => -1m; // "código" de que não há frete
}
```

E o código cliente, escrito **contra `Shipment`**, que soma o frete de um carrinho:

```csharp
decimal TotalShipping(IEnumerable<Shipment> shipments)
{
    decimal total = 0m;
    foreach (var s in shipments)
        total += s.CalculateCost(); // confia no contrato: custo válido, >= 0
    return total;
}
```

Rode isso com uma lista que contenha um `FreeSampleShipment` ou um `StorePickupShipment` e sinta a dor.

---

## Sua vez — antes de olhar a solução

Pense (ou responda pro Claude):

1. **Qual o contrato de `Shipment.CalculateCost()`?** (Está no comentário: sempre retorna um custo
   válido `>= 0`.)
2. **`FreeSampleShipment` respeita esse contrato?** E `StorePickupShipment`?
3. Escreva **na cabeça** o teste-cliente que **passa** com `Shipment`/`ExpressShipment` e **falha**
   com os outros dois. Esse teste é a *prova* da violação.
4. Como consertar? Repensar a hierarquia? Compor? Uma interface diferente?

> ⚠️ Note que há **duas violações diferentes** aqui — elas quebram contratos distintos. Ache as duas
> antes de refatorar.

---

## Dicas progressivas

<details>
<summary>Dica 1 — nomeie as violações</summary>

- `FreeSampleShipment.CalculateCost()` **lança exceção** onde o pai promete devolver um número. Isso
  é o smell clássico `NotSupportedException` em método herdado: o subtipo **não honra a pós-condição**
  ("retorna um custo válido").
- `StorePickupShipment.CalculateCost()` **retorna `-1`**, violando a invariante/pós-condição "custo
  `>= 0`". O cliente vai **somar `-1`** ao total e nem perceber — um bug silencioso, pior que a
  exceção.

Ambos os subtipos **não são substituíveis** por `Shipment`. Quem chama `CalculateCost()` confiando
no contrato quebra.
</details>

<details>
<summary>Dica 2 — o que esses dois casos têm em comum?</summary>

`FreeSampleShipment` e `StorePickupShipment` **não têm custo calculável por peso/distância** —
o custo deles é, na verdade, **zero por regra**, não um cálculo. Forçá-los a herdar de um tipo cujo
contrato é "calcular custo por peso e distância" foi o erro de modelagem.

Duas saídas legítimas:
- **Custo zero honesto:** se "sem frete" significa **custo 0**, o subtipo pode simplesmente
  `return 0m;` — isso **respeita** o contrato (`0 >= 0`). É a correção mais simples e muitas vezes a
  certa. Sem exceção, sem `-1`.
- **Separar a capacidade:** se "ter frete" e "não ter frete" são **conceitos diferentes** no domínio,
  modele-os como tipos distintos sob uma abstração comum, em vez de forçar herança.
</details>

<details>
<summary>Dica 3 — escolha a dosagem certa</summary>

Não estoure em abstração. Pergunte: *o cliente só precisa de um número de custo (`>= 0`)?* Se sim, a
correção mínima — cada tipo retornando um custo válido (inclusive `0`) — já **restaura o LSP**. Não
há necessidade de interfaces novas.

Só parta para uma abstração/interface se o domínio realmente distingue "envio faturado" de "envio sem
custo" com **comportamentos diferentes** além do número. Caso contrário, seria over-engineering — o
oposto do que este curso prega.
</details>

---

## Solução de referência

Há dois caminhos; ambos respeitam LSP. Escolha pela dosagem.

### Caminho A — correção mínima: honrar o contrato (custo `0`)

Se "grátis" e "retirada" significam apenas **custo zero**, o contrato já cobre isso — `0` é um custo
válido. Basta os subtipos **honrarem** a pós-condição em vez de burlá-la:

```csharp
public class FreeSampleShipment : Shipment
{
    public override decimal CalculateCost() => 0m; // ✅ respeita "custo válido >= 0"
}

public class StorePickupShipment : Shipment
{
    public override decimal CalculateCost() => 0m; // ✅ sem -1, sem exceção
}
```

`TotalShipping` agora funciona com **qualquer** `Shipment`, sem `if (s is ...)`, sem `try/catch`.
LSP restaurado com a menor mudança possível. Na maioria dos casos reais, **é isto que você quer**.

### Caminho B — separar a capacidade (quando o domínio pede)

Se "envio com frete faturável" e "envio sem custo" forem conceitos **de fato distintos** (regras,
relatórios, impostos diferentes), não force um a herdar do outro. Modele a **capacidade**:

```csharp
public interface IShipment
{
    // Contrato explícito: custo válido, sempre >= 0.
    decimal CalculateCost();
}

public sealed class BilledShipment : IShipment
{
    public decimal Weight { get; init; }
    public decimal DistanceKm { get; init; }
    public decimal CalculateCost() => Weight * 0.5m + DistanceKm * 0.1m;
}

public sealed class ExpressShipment : IShipment
{
    private readonly BilledShipment _base; // composição, não herança
    public ExpressShipment(BilledShipment b) => _base = b;
    public decimal CalculateCost() => _base.CalculateCost() * 1.8m;
}

public sealed class FreeShipment : IShipment  // amostra, retirada, brinde...
{
    public decimal CalculateCost() => 0m;
}
```

`TotalShipping(IEnumerable<IShipment>)` continua igual e correto para **todos** os tipos. Repare:
- `ExpressShipment` usa **composição** (`tem-um BilledShipment`) em vez de herdar — ele só reaproveita
  o cálculo, não promete ser substituível por um `BilledShipment` em todo contexto.
- Nenhum tipo lança exceção nem devolve valor-sentinela. Todos honram o **mesmo contrato**.

> **Dosagem:** o Caminho A é o padrão — mais simples, e correto na maioria das vezes. Só vá para o
> Caminho B se o domínio realmente separar os conceitos. Criar a interface "por precaução" quando um
> `return 0m` resolveria é o over-engineering que estamos evitando.

---

## O que fixar desta prática

- **O smell não é o valor de retorno — é a promessa quebrada.** `throw` e `-1` são sintomas de que o
  subtipo não honra o contrato do supertipo.
- **O teste-cliente é a prova.** Se existe um uso legítimo do supertipo que **passa com o pai e falha
  com o filho**, LSP está violado. Escrever esse teste é o jeito mais rápido de detectar.
- **Composição corta a raiz.** `ExpressShipment` "tem-um" cálculo, não "é-um" tipo faturável — e por
  isso não carrega promessas que não pode cumprir.
- **Dose.** A menor correção que restaura o contrato (Caminho A) costuma ser a certa. Abstração nova
  só quando o domínio pede (Caminho B).

---

## 🧪 Aplicação de teste da aula

Depois desta prática, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 SOLID/apps/modulo-04/quiz.py
```

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 4" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Depois vem a **prova do módulo**
> (`SOLID/provas/modulo-04/`) e, ao passar, o **Módulo 05 — ISP (Segregação de Interfaces)**.
