# Módulo 05 — ISP: Segregação de Interfaces (Teoria)

> Objetivo do módulo: entender o **I** de SOLID — o **Interface Segregation Principle**. Você vai
> aprender a reconhecer a **"fat interface"** (interface gorda), por que forçar alguém a implementar
> métodos que não usa apodrece o design, e como **segregar** interfaces por **papel** (role
> interfaces) — sem cair no extremo oposto de pulverizar tudo em uma interface por método.

---

## 1. A definição: não depender do que você não usa

A formulação clássica do princípio (Robert C. "Uncle Bob" Martin):

> **Nenhum cliente deve ser forçado a depender de métodos que não usa.**

Repare na palavra **cliente**. Aqui "cliente" é **quem depende da interface** — e são dois:

- **Quem CHAMA** a interface (o consumidor que recebe `IAlgo` como parâmetro/dependência).
- **Quem IMPLEMENTA** a interface (a classe que precisa fornecer todos os métodos declarados).

O ISP diz que interfaces devem ser **pequenas e específicas ao papel de quem as consome** — as
chamadas **role interfaces** ("interfaces de papel"). Uma interface deve descrever **um papel
coeso** ("eu sei imprimir"), não um catálogo genérico de tudo que um dispositivo *poderia* fazer.

### Ligando com o Módulo 01

Interface enxuta = **menos acoplamento**. Quem depende de uma interface pequena não é **arrastado**
por mudanças que não lhe dizem respeito. Se a interface é gorda e um método que você **nem usa**
muda de assinatura, você recompila e possivelmente quebra — acoplamento puro e desnecessário.

### O primo do ISP é o SRP

Guarde esta frase, ela amarra o módulo:

> **ISP é o lado da _interface_ do mesmo cuidado que o SRP tem no lado da _classe_.**

O SRP (Módulo 02) diz: uma classe, **uma razão para mudar**. O ISP diz o mesmo para o contrato: uma
interface deve servir a **um papel/cliente**, não a vários com necessidades diferentes.

---

## 2. O smell central: a "fat interface"

O cheiro que o ISP ataca tem nome: **fat interface** (interface gorda). É uma interface **grande**,
que **várias classes implementam**, mas em que **cada implementação só usa parte** dos métodos.

O exemplo canônico é o dispositivo multifuncional:

```csharp
public interface IMultiFunctionDevice
{
    void Print(Documento doc);
    void Scan(Documento doc);
    void Fax(Documento doc);
}
```

Uma multifuncional de escritório de fato faz as três coisas. Mas e a **impressora simples**, que só
imprime? Ela é **forçada** a implementar `Scan()` e `Fax()` que **não faz**:

```csharp
public class SimplePrinter : IMultiFunctionDevice
{
    public void Print(Documento doc) { /* imprime de verdade */ }

    // Métodos que a impressora simples NÃO faz — mas é obrigada a "implementar":
    public void Scan(Documento doc) => throw new NotSupportedException("Não tem scanner.");
    public void Fax(Documento doc)  => throw new NotSupportedException("Não tem fax.");
}
```

Esse `throw new NotSupportedException()` (ou `NotImplementedException`) é o **sintoma clássico** do
ISP violado — e é **veneno duplo**:

1. **Mente sobre o contrato.** A interface promete que quem a implementa **sabe** escanear. A
   `SimplePrinter` diz "eu sou um `IMultiFunctionDevice`" mas **estoura** se você chamar `Scan()`.
   Isso é **violação de LSP** (Módulo 04): o subtipo não substitui o supertipo de verdade — tem um
   método **"proibido"** que explode em runtime.
2. **Infla a classe com código morto.** Métodos falsos, stubs, comentários "não suportado" — ruído
   que ninguém quer manter.

### Outro exemplo clássico: o trabalhador

```csharp
public interface IWorker
{
    void Work();
    void Eat();   // faz sentido para humano; e para um robô?
}

public class RobotWorker : IWorker
{
    public void Work() { /* trabalha */ }
    public void Eat()  => throw new NotSupportedException("Robô não come.");
}
```

De novo: `Eat()` foi **empurrado** para dentro de `RobotWorker` porque a interface era gorda. O robô
trabalha, mas foi **forçado a depender** de um método que não faz sentido para o seu papel.

### Por que dói (mesmo quando "funciona")

| Sintoma | Consequência prática |
|---------|----------------------|
| Stubs `NotSupportedException` | Contrato mentiroso → bug em runtime → **fere LSP** |
| Método que você não usa muda | Você **recompila** e pode quebrar, sem motivo |
| Interface gorda em mock de teste | Precisa **stubar métodos irrelevantes** → teste inchado |
| "É um `IMultiFunctionDevice`" | Acoplamento a um contrato **maior do que você precisa** |

---

## 3. A solução: segregar em role interfaces

A cura é **quebrar** a interface gorda em interfaces **pequenas, por papel**:

```csharp
public interface IPrinter { void Print(Documento doc); }
public interface IScanner { void Scan(Documento doc); }
public interface IFax     { void Fax(Documento doc);   }
```

Agora cada classe implementa **só o que realmente faz**. Em C# uma classe pode implementar
**várias interfaces** — então a multifuncional **compõe** as três:

```csharp
// A simples implementa SÓ o papel que exerce:
public class SimplePrinter : IPrinter
{
    public void Print(Documento doc) { /* imprime */ }
}

// A multifuncional compõe vários papéis:
public class MultiFunctionMachine : IPrinter, IScanner, IFax
{
    public void Print(Documento doc) { /* imprime */ }
    public void Scan(Documento doc)  { /* escaneia */ }
    public void Fax(Documento doc)   { /* envia fax */ }
}
```

E — o ponto central do ISP — o **cliente depende só da fatia que precisa**:

```csharp
// Antes: dependia da interface inteira, mesmo só imprimindo.
public void EmitirRecibo(IMultiFunctionDevice dev) => dev.Print(recibo);

// Depois: declara SÓ o papel que exerce.
public void EmitirRecibo(IPrinter printer) => printer.Print(recibo);
```

O que ganhamos com o "depois":

- **Some o stub falso.** `SimplePrinter` não tem mais `Scan()`/`Fax()` fajutos.
- **Some o risco de LSP.** Não existe mais método "proibido" que estoura.
- **Some o acoplamento inútil.** Mudar a assinatura de `Fax()` **não recompila** nem quebra quem só
  imprime — porque quem só imprime nunca dependeu de `IFax`.

---

## 4. Relação com SRP e LSP, e composição de interfaces

O ISP não vive sozinho — ele conversa direto com dois princípios que você já viu:

### ISP × SRP (coesão)

São **primos**. O SRP separa a **classe** por razão de mudar; o ISP separa a **interface** por
**cliente/papel**. Ambos perseguem **coesão**: cada peça faz uma coisa e serve a um interessado. Uma
interface que serve a três clientes diferentes tem, na prática, **três razões para mudar** — é o
SRP gritando do lado do contrato.

### ISP × LSP (o método "proibido")

A fat interface **empurra** a violação de LSP. Quando você é obrigado a implementar um método que
não faz, a saída tentadora é o `throw NotSupportedException` — e pronto, você criou um subtipo que
**não substitui** o supertipo (Módulo 04). **Segregar a interface remove a tentação do stub falso**:
se `SimplePrinter` implementa só `IPrinter`, não há `Scan()` para estourar. **ISP previne uma classe
inteira de violações de LSP.**

### Composição de interfaces em C#

C# torna a segregação barata: uma classe soma **várias interfaces pequenas** sem herança gorda.

```csharp
public class MultiFunctionMachine : IPrinter, IScanner, IFax { /* ... */ }
```

E o consumidor declara **exatamente o papel** que precisa, ficando **imune** a mudanças nos outros:

```csharp
void Digitalizar(IScanner s)  => s.Scan(doc);   // não conhece IPrinter nem IFax
void Imprimir(IPrinter p)     => p.Print(doc);  // não conhece IScanner nem IFax
```

Isso já aponta para o **DIP** (Módulo 06): dependa de uma **abstração pequena e certeira**, não de
uma genérica que carrega peso morto.

---

## 5. Dosagem: segregar por papel, não por método

**Aqui mora o julgamento** — e é a parte que separa quem entende ISP de quem vira dogmático.

### O extremo errado

Levar o ISP ao pé da letra e criar **uma interface por método, sempre**:

```csharp
// Over-engineering: nenhuma dessas descreve um "papel", só uma assinatura solta.
public interface IHasName    { string Name { get; } }
public interface IHasEmail   { string Email { get; } }
public interface IHasAge     { int Age { get; } }
```

Isso **pulveriza** o design: multiplica arquivos, espalha o que era coeso e **não descreve papel
nenhum**. `IHasName` não é um papel — é uma propriedade. Segregar assim é o **oposto** de coesão.

### O gatilho certo

A pergunta que dispara o ISP é **uma só**:

> **Existe algum cliente que só usa um _pedaço_ desta interface?**

- **Se sim** → esse pedaço quer virar uma **interface própria** (um papel real).
- **Se não** (todos os clientes usam a interface **inteira**) → **ela não é gorda**. Mantê-la unida
  é **coeso**; quebrá-la seria **over-engineering**.

### A regra de dosagem

- Segregue por **papel/cliente real** ("sei imprimir", "sei escanear"), **não** mecanicamente por
  assinatura de método.
- ISP resolve **dor concreta**: stub falso (`NotSupportedException`), recompilação desnecessária,
  mock inchado. **Sem essa dor, não invente a segregação.**
- Se todos os implementadores implementam tudo **de verdade** e todos os consumidores usam tudo, a
  interface está **certa como está**.

> 🎯 **Julgamento > dogma.** O ISP é sobre **remover peso morto real**, não sobre atingir uma
> métrica de "interfaces minúsculas". Uma interface pequena que ninguém precisava não é uma vitória.

---

## 6. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| ISP | Nenhum cliente deve ser forçado a depender de métodos que não usa. |
| Fat interface | Interface grande que várias classes implementam, mas cada uma só usa parte. |
| Role interface | Interface pequena que descreve **um papel** coeso ("sei imprimir"). |
| Cliente (da interface) | Quem depende dela: tanto quem **chama** quanto quem **implementa**. |
| `NotSupportedException` | Sintoma clássico de ISP violado (método que a classe é forçada a "ter"). |
| Composição de interfaces | Uma classe C# implementa várias interfaces pequenas de uma vez. |
| Over-segregation | O exagero: uma interface por método, sem descrever papel — over-engineering. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Em uma frase, o que o ISP proíbe — e quem é o "cliente" a que ele se refere?
2. Por que um `throw new NotSupportedException()` num método de interface é um **sintoma** de ISP
   violado, e como isso também **fere o LSP**?
3. Dado `IMultiFunctionDevice { Print(); Scan(); Fax(); }` e uma impressora que só imprime: qual é a
   segregação correta, e como a multifuncional fica no "depois"?
4. Como o ISP se relaciona com o SRP? E como ele **previne** violações de LSP?
5. Qual é o **gatilho** para segregar uma interface — e quando **NÃO** dividir (para não cair em
   over-engineering)?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
