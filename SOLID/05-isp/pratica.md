# Módulo 05 — ISP: Segregação de Interfaces (Prática Guiada)

> Objetivo desta prática: pegar uma **interface gorda** com implementações que **estouram** em
> métodos que não usam, reconhecer o cheiro, e **segregar** em role interfaces — sem pulverizar em
> uma interface por método.
>
> **Abordagem:** refatoração de código **conduzida no chat**. Não há código para rodar — é
> raciocínio de design. Você propõe o próximo passo, o Claude critica e guia. As dicas abaixo são
> progressivas: tente antes de abrir a próxima.
>
> ⏱️ Tempo estimado: 20–30 min. 💵 Custo: **US$ 0** (é só código).

---

## O código de partida

Um sistema de agendamento tem um "posto de trabalho" que pode receber tarefas de vários tipos. O time
começou com **uma** interface para "qualquer estação de trabalho":

```csharp
public interface IWorkstation
{
    void Imprimir(Documento doc);
    void Escanear(Documento doc);
    void EnviarFax(Documento doc, string numero);
    void Grampear(Documento doc);
}
```

E surgiram três dispositivos que a implementam:

```csharp
// 1) Uma multifuncional de escritório — faz tudo.
public class MultifuncionalDeEscritorio : IWorkstation
{
    public void Imprimir(Documento doc)                 { /* imprime */ }
    public void Escanear(Documento doc)                 { /* escaneia */ }
    public void EnviarFax(Documento doc, string numero) { /* envia fax */ }
    public void Grampear(Documento doc)                 { /* grampeia */ }
}

// 2) Uma impressora doméstica simples — SÓ imprime.
public class ImpressoraDomestica : IWorkstation
{
    public void Imprimir(Documento doc)                 { /* imprime */ }
    public void Escanear(Documento doc)                 => throw new NotSupportedException("Sem scanner.");
    public void EnviarFax(Documento doc, string numero) => throw new NotSupportedException("Sem fax.");
    public void Grampear(Documento doc)                 => throw new NotSupportedException("Sem grampeador.");
}

// 3) Um scanner de mesa — SÓ escaneia.
public class ScannerDeMesa : IWorkstation
{
    public void Imprimir(Documento doc)                 => throw new NotSupportedException("Não imprime.");
    public void Escanear(Documento doc)                 { /* escaneia */ }
    public void EnviarFax(Documento doc, string numero) => throw new NotSupportedException("Sem fax.");
    public void Grampear(Documento doc)                 => throw new NotSupportedException("Não grampeia.");
}
```

E um consumidor que só precisa **imprimir** um recibo:

```csharp
public class EmissorDeRecibo
{
    public void Emitir(IWorkstation estacao, Documento recibo)
    {
        estacao.Imprimir(recibo);   // usa SÓ Imprimir — mas depende da interface inteira
    }
}
```

**Seu desafio:** refatore aplicando o ISP.

**Antes de mexer no código, responda:**
1. Qual é o **sintoma** que grita "ISP violado" aqui? (Dica: procure o que se repete.)
2. Quem são os **clientes** dessa interface, e qual **pedaço** cada um realmente usa?
3. Por que `EmissorDeRecibo` receber `IWorkstation` é acoplamento **desnecessário**?

---

## Dicas progressivas

<details>
<summary><b>Dica 1 — Onde está o cheiro</b></summary>

Conte os `throw new NotSupportedException()`. Cada um é uma prova de que aquela classe foi
**forçada** a implementar um método que **não faz**. `ImpressoraDomestica` só imprime, mas carrega
três stubs falsos; `ScannerDeMesa` só escaneia, e carrega outros três. A interface `IWorkstation` é
uma **fat interface**: junta quatro papéis distintos que quase nenhum dispositivo exerce por inteiro.
</details>

<details>
<summary><b>Dica 2 — Segregue por PAPEL, não por classe</b></summary>

Liste os **papéis** que aparecem: *imprimir*, *escanear*, *enviar fax*, *grampear*. Cada papel vira
uma **role interface** pequena:

```csharp
public interface IImpressora  { void Imprimir(Documento doc); }
public interface IScanner     { void Escanear(Documento doc); }
public interface IFax         { void EnviarFax(Documento doc, string numero); }
public interface IGrampeador  { void Grampear(Documento doc); }
```

Repare que segregamos por **papel real** (quatro papéis que existem no domínio), **não** mecanicamente
"uma por método porque sim". Aqui, coincidentemente, cada papel tem um método — mas o critério foi o
papel, não a contagem de assinaturas.
</details>

<details>
<summary><b>Dica 3 — Componha na implementação e enxugue no consumidor</b></summary>

Em C# uma classe implementa **várias** interfaces. A rica **compõe** os papéis que exerce; a pobre
implementa **só o seu**. E o consumidor declara **só a fatia** que usa:

```csharp
public class ImpressoraDomestica : IImpressora { /* só Imprimir */ }

public class EmissorDeRecibo
{
    public void Emitir(IImpressora impressora, Documento recibo)
        => impressora.Imprimir(recibo);   // agora depende só de IImpressora
}
```

Depois de segregar, verifique: **sumiu algum `NotSupportedException`?** Se sim, o ISP fez efeito.
</details>

---

## Solução de referência (comentada)

> Não abra antes de tentar. A ideia é você **decidir** a segregação; isto é uma referência.

```csharp
// --- Role interfaces: cada uma descreve UM papel coeso ---
public interface IImpressora  { void Imprimir(Documento doc); }
public interface IScanner     { void Escanear(Documento doc); }
public interface IFax         { void EnviarFax(Documento doc, string numero); }
public interface IGrampeador  { void Grampear(Documento doc); }

// --- A multifuncional COMPÕE os papéis que realmente exerce ---
public class MultifuncionalDeEscritorio : IImpressora, IScanner, IFax, IGrampeador
{
    public void Imprimir(Documento doc)                 { /* imprime */ }
    public void Escanear(Documento doc)                 { /* escaneia */ }
    public void EnviarFax(Documento doc, string numero) { /* envia fax */ }
    public void Grampear(Documento doc)                 { /* grampeia */ }
}

// --- Cada dispositivo simples implementa SÓ o seu papel: zero stub falso ---
public class ImpressoraDomestica : IImpressora
{
    public void Imprimir(Documento doc) { /* imprime */ }
}

public class ScannerDeMesa : IScanner
{
    public void Escanear(Documento doc) { /* escaneia */ }
}

// --- O consumidor depende SÓ da fatia que usa ---
public class EmissorDeRecibo
{
    public void Emitir(IImpressora impressora, Documento recibo)
        => impressora.Imprimir(recibo);
}
```

**Por que isso respeita o ISP:**

- **Sumiram todos os `NotSupportedException`.** Nenhuma classe é forçada a implementar o que não faz —
  e, com isso, **some também o risco de LSP** (não há mais método "proibido" que estoura em runtime).
- **`EmissorDeRecibo` depende só de `IImpressora`.** Se amanhã `IFax` mudar de assinatura, o emissor
  de recibo **não recompila e não quebra** — ele nunca dependeu de fax.
- **Composição natural em C#.** A multifuncional soma quatro papéis sem herança gorda; um dispositivo
  novo (uma copiadora, digamos) implementa só as interfaces que fizerem sentido para ele.

### A parte do julgamento (dosagem)

Note o que **não** fizemos: não criamos `IImprimirColorido`, `IImprimirDuplex`, `IImprimirA3` só
porque `Imprimir` "poderia" variar. Segregamos por **papel que já existe e já tem cliente próprio**.

Pergunta-guia para fechar: **existe cliente que usa só um pedaço?** Sim — o `EmissorDeRecibo` só
imprime, e há dispositivos que só escaneiam. Por isso a segregação se pagou. Se **todos** os
dispositivos fizessem tudo e **todos** os consumidores usassem tudo, `IWorkstation` unida estaria
**certa**, e quebrá-la seria over-engineering.

---

## ✅ Checklist de conclusão da prática

- [ ] Identifiquei o cheiro (os `NotSupportedException` repetidos) como **fat interface**.
- [ ] Mapeei os **papéis** e quais **clientes** usam cada pedaço.
- [ ] Segreguei em **role interfaces** por papel (não uma por método "porque sim").
- [ ] A implementação rica **compõe** várias interfaces; as pobres implementam só a sua.
- [ ] O consumidor passou a depender **só da fatia** que usa.
- [ ] Confirmei que **sumiram os stubs falsos** (e com eles o risco de LSP).
- [ ] Sei enunciar o gatilho do ISP e **quando NÃO** segregar.

Quando fechar o checklist, você está pronto para o **quiz do módulo** (`SOLID/apps/modulo-05/`) e
depois a **prova** (`SOLID/provas/modulo-05/`).

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 5" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão.
