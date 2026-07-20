# Módulo 04 — LSP: Liskov Substitution Principle (Teoria)

> Objetivo do módulo: entender a **Substituição de Liskov** — a regra que diz que um subtipo tem
> que poder **substituir** o supertipo sem quebrar o programa. Você vai ver por que o clássico
> `Square : Rectangle` é uma armadilha, aprender os **contratos** que uma subclasse precisa honrar
> (pré-condições, pós-condições, invariantes), reconhecer os **sinais de violação** e saber quando
> trocar herança por composição — sem cair no extremo de banir herança.

---

## 1. A definição: substituibilidade comportamental

O princípio vem de **Barbara Liskov** (1988). A formulação original é acadêmica, mas a ideia
prática é simples:

> **Se `S` é um subtipo de `T`, então objetos de `T` podem ser substituídos por objetos de `S`
> sem quebrar a corretude do programa.**

Traduzindo para o dia a dia: **quem usa a abstração não pode ter surpresas.** Se um método recebe
um `Repository`, ele deve funcionar corretamente com **qualquer** classe que herde/implemente
`Repository` — sem `if` especiais, sem exceções inesperadas, sem resultados errados.

Repare na palavra **corretude**. Não basta o código **compilar** com o subtipo no lugar do
supertipo (o compilador já garante isso via herança/interface). O programa tem que continuar
**correto em tempo de execução** — mesmas garantias, mesmo comportamento esperado.

O subtipo, portanto, precisa **honrar o contrato** do supertipo. Contrato aqui não é só a
assinatura dos métodos; é o **comportamento prometido**: o que ele aceita, o que ele devolve, o
que ele garante.

> 🔗 **Ligação com o OCP (Módulo 03):** o Aberto/Fechado se apoia em **polimorfismo** — você
> estende trocando implementações por trás de uma abstração. O LSP é **o que faz esse polimorfismo
> funcionar de verdade**. Sem LSP, cada novo subtipo pode introduzir um bug silencioso no código
> que já dependia da abstração. LSP é a garantia de que "estender por subtipo" é seguro.

---

## 2. O clássico Retângulo/Quadrado

Este é o exemplo canônico de LSP — e o mais instrutivo, porque a herança parece **obviamente
certa** e mesmo assim está errada.

Na geometria, **um quadrado é um retângulo** (com lados iguais). O instinto de OO diz: "é-um" →
herança. Então:

```csharp
public class Rectangle
{
    public virtual int Width { get; set; }
    public virtual int Height { get; set; }
    public int Area => Width * Height;
}

public class Square : Rectangle
{
    // Para manter a invariante do quadrado (lados iguais),
    // setar um lado precisa mudar o outro:
    public override int Width
    {
        get => base.Width;
        set { base.Width = value; base.Height = value; }
    }

    public override int Height
    {
        get => base.Height;
        set { base.Width = value; base.Height = value; }
    }
}
```

Agora imagine um código cliente **inocente**, escrito contra `Rectangle`:

```csharp
void ResizeAndCheck(Rectangle r)
{
    r.Width = 5;
    r.Height = 4;
    // Quem escreveu isso assume: largura e altura são independentes.
    Debug.Assert(r.Area == 20); // 5 * 4
}
```

Passe um `Rectangle` e `Area == 20`. ✅
Passe um `Square` e o que acontece? `r.Height = 4` também seta a largura para 4 → `Area == 16`. ❌

O programa **quebrou** só porque trocamos o supertipo por um subtipo. Isso é uma violação de LSP,
apesar de o quadrado ser, "de verdade", um retângulo.

### A lição

O erro não está na geometria — está em confundir **taxonomia** ("é-um" no mundo real) com
**substituibilidade comportamental** ("é-um" no código). O `Rectangle` tem uma **invariante
implícita**: *largura e altura são independentes; mexer numa não mexe na outra*. O `Square`
**viola essa invariante**. Portanto ele não é um subtipo válido de `Rectangle`, por mais que a
frase "quadrado é um retângulo" seja verdadeira.

> 🎯 **LSP é sobre COMPORTAMENTO esperado, não sobre a taxonomia do mundo real.** "É-um" na fala
> não implica "é substituível" no código.

---

## 3. Os contratos de Liskov

Como saber, **objetivamente**, se um subtipo respeita LSP? Existem três regras de contrato. Se o
subtipo viola qualquer uma, quebrou a substituibilidade.

### Pré-condições — não podem ser **fortalecidas**

Uma pré-condição é o que o método **exige** para funcionar. O subtipo **não pode exigir mais** do
que o supertipo. Se o pai aceita qualquer inteiro, o filho não pode passar a exigir "só positivos".

```csharp
class Processor          { public virtual void Handle(int x) { /* aceita qualquer int */ } }
class StrictProcessor : Processor
{
    public override void Handle(int x)
    {
        if (x < 0) throw new ArgumentException(); // ❌ fortaleceu a pré-condição
        base.Handle(x);
    }
}
```

Quem chamava `Handle(-1)` com o pai funcionava; com o filho, quebra. **Violação.**

### Pós-condições — não podem ser **enfraquecidas**

Uma pós-condição é o que o método **garante** ao terminar. O subtipo **não pode entregar menos ou
pior** do que o supertipo. Se o pai **nunca** retorna `null`, o filho também não pode.

```csharp
class UserRepo         { public virtual User Find(int id) => /* nunca retorna null */ ...; }
class CachedUserRepo : UserRepo
{
    public override User Find(int id) => _cache.TryGet(id); // ❌ pode retornar null
}
```

O cliente confiava que `Find` nunca é `null` e não checava. Com o filho, `NullReferenceException`.
**Violação.**

### Invariantes — devem ser **preservadas**

Invariante é o que o supertipo garante como **sempre verdadeiro** sobre seu estado. O subtipo tem
que manter isso. No exemplo da seção 2, a invariante "`Width` e `Height` são independentes" é o que
o `Square` viola.

### Regra da história (history rule)

O subtipo **não pode permitir mudanças de estado que o supertipo proíbe**. Se o supertipo é, digamos,
imutável depois de criado, um subtipo não pode introduzir um setter que muda o estado por baixo — isso
"reescreve a história" de um jeito que o cliente do supertipo não esperava.

| Contrato | Regra | Sintoma de violação |
|----------|-------|---------------------|
| **Pré-condição** | Não fortalecer (não exigir mais) | Filho lança em entrada que o pai aceitava |
| **Pós-condição** | Não enfraquecer (não entregar menos) | Filho retorna `null`/menos garantias que o pai |
| **Invariante** | Preservar o que o pai garante | Filho quebra uma verdade que o pai mantinha |
| **História** | Não permitir mudança de estado que o pai proíbe | Filho torna mutável o que era imutável |

> 💡 Regra mnemônica: **exija a mesma coisa ou menos; entregue a mesma coisa ou mais.** Um subtipo
> honesto é *mais permissivo na entrada* e *mais forte na saída* — nunca o contrário.

---

## 4. Sinais de violação (smells)

Você raramente vai calcular contratos formalmente. Na prática, LSP é detectado por **cheiros**:

- **`throw new NotImplementedException()` / `NotSupportedException()` em método herdado.** O subtipo
  herdou uma operação que **não sabe/não pode** cumprir e "resolve" lançando. Exemplos clássicos:
  ```csharp
  class Penguin : Bird
  {
      public override void Fly() => throw new NotSupportedException("Pinguim não voa");
  }

  class ReadOnlyList<T> : List<T>
  {
      public new void Add(T item) => throw new NotSupportedException("Lista somente-leitura");
  }
  ```
  Quem tem um `Bird` e chama `Fly()` explode ao receber um `Penguin`. **Violação.**

- **Checagem de tipo no cliente** para *evitar* chamar algo:
  ```csharp
  foreach (var bird in birds)
      if (!(bird is Penguin))   // ❌ o polimorfismo virou if/else disfarçado
          bird.Fly();
  ```
  Se o cliente precisa saber o **tipo concreto** para não quebrar, a abstração não é substituível.

- **Sobrescrita que "esvazia" o método** — corpo vazio ou *no-op* — quebrando o efeito que o pai
  prometia. O método existe, "funciona", mas não faz o que o contrato dizia.

- **Documentação do tipo "não use este método nesta subclasse".** Se você precisa **avisar** que um
  método herdado não vale aqui, o contrato **já foi quebrado**. Comentário não conserta LSP.

- **Retornar `null` onde o supertipo nunca retornava** — é enfraquecer a pós-condição na marra
  (visto na seção 3).

Todos esses cheiros dizem a mesma coisa: **o subtipo não é substituível pelo supertipo.**

---

## 5. Herança x composição (e a dosagem)

A boa notícia: a maioria das violações de LSP **desaparece** quando você para de forçar herança.

### "É-um" honesto vs. "comporta-se-como"

Herança (`class Square : Rectangle`) declara **"é-um"** e, com isso, promete **substituibilidade
comportamental**. Se essa promessa não se sustenta, você tem duas saídas melhores:

1. **Composição ("tem-um").** Em vez de herdar, o tipo *contém* o outro e expõe só o que faz sentido.
2. **Interfaces estreitas ("comporta-se-como").** Separe a **capacidade** do **tipo base**.

**Bird/Penguin, corrigido** — nem todo pássaro voa, então voar não pertence a `Bird`:

```csharp
public abstract class Bird { public abstract void Eat(); }

public interface IFlyingBird { void Fly(); }

public class Sparrow : Bird, IFlyingBird
{
    public override void Eat() { /* ... */ }
    public void Fly() { /* ... */ }
}

public class Penguin : Bird   // não implementa IFlyingBird — e está certo
{
    public override void Eat() { /* ... */ }
}
```

Agora o código que faz voar depende de `IFlyingBird`, e **um `Penguin` nunca chega lá**. Nenhuma
exceção, nenhum `is Penguin`. Repare que isso **liga com o ISP** (Módulo 05): a interface estreita
`IFlyingBird` evita que alguém dependa de um comportamento que a classe não tem.

**Retângulo/Quadrado, corrigido** — abandone a herança mútua. Opções:
- Tipos **imutáveis e independentes** (`record Rectangle(int Width, int Height)` e
  `record Square(int Side)`), sem um herdar do outro; ou
- Uma abstração comum de comportamento: `interface IShape { int Area(); }`, e cada figura calcula
  a sua área. Ninguém promete "setar largura não mexe na altura", então ninguém quebra.

### Dosagem: LSP **não** proíbe herança

Cuidado com o pêndulo. A leitura preguiçosa de "Retângulo/Quadrado dá ruim" vira "**herança é o
mal, componha sempre**". Isso é exagero.

- **LSP não bane herança — exige que ela seja honesta.** Se o subtipo realmente honra o contrato do
  supertipo (não fortalece pré, não enfraquece pós, preserva invariantes), a herança está **correta**
  e é ótima ferramenta de reuso e polimorfismo.
- **Evite hierarquias profundas e especulativas.** Herança criada "só por reuso de código", sem uma
  relação de substituibilidade real, costuma cobrar a fatura em LSP mais tarde.
- Pergunte-se antes de herdar: *"todo lugar que aceita o pai vai funcionar corretamente com este
  filho?"* Se a resposta é "sim, sempre", herança é legítima. Se é "quase sempre, exceto...", esse
  "exceto" é a violação de LSP — prefira composição ou interface estreita.

> 🎯 **Bússola:** herde quando o filho **é substituível** pelo pai em todo contexto; componha quando
> ele só **reaproveita** parte do comportamento.

---

## 6. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| LSP | Subtipos devem substituir o supertipo sem quebrar a corretude do programa. |
| Substituibilidade comportamental | Trocar o pai pelo filho mantém o comportamento esperado, não só compila. |
| Contrato | O comportamento prometido por um tipo: o que aceita, o que devolve, o que garante. |
| Pré-condição | O que um método exige para funcionar; o filho não pode exigir mais. |
| Pós-condição | O que um método garante ao terminar; o filho não pode entregar menos. |
| Invariante | Verdade que o tipo mantém sempre; o filho deve preservá-la. |
| "É-um" x "tem-um" | Herança (é-um, exige substituibilidade) vs. composição (tem-um, reuso). |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Por que `Square : Rectangle` viola LSP, se um quadrado "é" um retângulo? Qual invariante quebra?
2. Qual a diferença entre **fortalecer uma pré-condição** e **enfraquecer uma pós-condição**? Dê um
   exemplo de cada.
3. Um método herdado que faz `throw new NotSupportedException()` — por que isso é um smell de LSP?
4. Como você reescreveria `Bird`/`Penguin` para que "voar" nunca chegue num pinguim?
5. LSP significa "evite herança sempre"? Quando a herança **está certa**?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
