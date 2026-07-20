# Módulo 01 — Fundamentos de Design & por que SOLID existe (Teoria)

> Objetivo do módulo: dar o **vocabulário** que os cinco princípios vão usar. Antes de aprender a
> *curar* um design ruim (SRP, OCP, LSP, ISP, DIP), você precisa aprender a *diagnosticá-lo*: o que é
> design, por que ele importa, quais são os **sintomas** de um design apodrecendo, o que são
> **acoplamento** e **coesão**, e quais **code smells** anunciam cada violação. Este módulo é o
> exame; os próximos são o tratamento.

---

## 1. O que é design de software e por que ele importa

**Design** aqui não é a interface visual. É a **estrutura interna** do código: como você divide o
sistema em classes, como elas se relacionam, onde ficam as fronteiras. É a diferença entre *o que* o
programa faz (todos os designs entregam a mesma feature) e *como ele está organizado por dentro*.

Por que isso importa tanto? Por causa de um fato incômodo:

> **Código é lido e mudado muito mais vezes do que é escrito.**

Você escreve uma classe uma vez. Depois ela é lida dezenas de vezes, e mudada sempre que um requisito
muda — e requisitos **sempre** mudam. O custo real de um sistema não está na primeira versão; está em
todos os meses seguintes de manutenção. Um estudo clássico estima que a maior parte do custo total de
software vai para manutenção, não para o desenvolvimento inicial.

Daí a métrica que define design **bom** vs. **ruim**:

| | Design bom | Design ruim |
|---|---|---|
| Fazer uma mudança | barata, localizada, sem medo | cara, espalhada, assustadora |
| Adicionar uma feature | encaixa numa extensão | exige mexer em código que já funcionava |
| Onde bate o custo | você paga uma vez, no começo | você paga sempre, a cada mudança |

**SOLID não é sobre "código bonito" nem sobre agradar o linter.** É sobre uma coisa só: **baixar o
custo de mudar**. Toda vez que um princípio parecer abstrato, volte a esta pergunta — *"isso torna a
próxima mudança mais barata ou mais cara?"*. Se a resposta for "mais cara", o princípio não se aplica ali.

---

## 2. Os quatro sintomas do design podre

Robert C. Martin ("Uncle Bob") descreveu quatro **cheiros** de um design que está apodrecendo. São os
sintomas que você sente *antes* de conseguir nomear a doença. Aprenda a reconhecê-los — eles são o
alarme.

### Rigidez (Rigidity)

O sistema é **difícil de mudar** porque uma mudança pequena obriga uma cascata de outras mudanças.
Você quer alterar uma coisa e descobre que precisa mexer em cinco arquivos, recompilar meio mundo, e
avisar três times. A estimativa de "vai ser rapidinho" vira uma semana.

> Exemplo: mudar o formato de uma data exige tocar na camada de UI, no serviço, no repositório e no
> relatório — porque todos formatam a data por conta própria.

### Fragilidade (Fragility)

Você muda **aqui** e quebra **ali** — num lugar que aparentemente não tinha nada a ver. O sistema
quebra em pontos inesperados a cada alteração. O sintoma clássico: "consertei o bug X e apareceram os
bugs Y e Z". Ninguém confia em mexer no código.

> Exemplo: você corrige o cálculo de frete e o relatório de vendas passa a dar número errado, porque
> ambos dependiam de um mesmo campo mutável escondido.

### Imobilidade (Immobility)

Existe uma parte **útil e reaproveitável** dentro do sistema, mas o custo de **desgrudá-la** é alto
demais. Você gostaria de reusar aquele módulo de e-mail em outro projeto, mas ele vem colado a banco de
dados, configuração e vinte dependências. É mais barato reescrever do que extrair.

### Viscosidade (Viscosity)

Quando fazer a coisa **certa** é mais difícil do que fazer a **gambiarra**, o design tem alta
viscosidade — ele *empurra* o desenvolvedor para o caminho errado. Se a maneira correta de adicionar
um caso exige criar uma classe, registrar num lugar e escrever teste, mas dá pra "resolver" jogando
mais um `if` no método gigante, a pressão do prazo garante que o `if` vence. O design piora sozinho.

> Há também a **viscosidade do ambiente**: build lento, testes que demoram, ferramentas ruins — que
> também empurram pra atalhos. Mas o foco aqui é a viscosidade do *design*.

**Resumo:** rigidez = mudar é caro; fragilidade = mudar quebra coisas; imobilidade = reusar é caro;
viscosidade = o design premia a gambiarra. Se você sente qualquer um deles, há dívida de design — e
algum princípio SOLID provavelmente está sendo violado.

---

## 3. Acoplamento x Coesão

Estes dois conceitos são a **raiz** de quase tudo em SOLID. Se você entender os dois, o resto vira
consequência.

### Acoplamento — queremos BAIXO

**Acoplamento** é o quanto uma parte do código **depende** de outra. Duas classes estão fortemente
acopladas quando você não consegue mexer/entender/testar uma sem arrastar a outra junto.

- **Baixo acoplamento** = peças de LEGO: cada uma se conecta por um encaixe simples e padrão; você
  troca uma sem desmontar as vizinhas.
- **Alto acoplamento** = um bloco de cimento: tudo está fundido; pra trocar um pedaço você quebra o
  bloco inteiro.

Alto acoplamento é a causa direta da **fragilidade** (mudar aqui quebra ali) e da **imobilidade**
(não dá pra desgrudar). Exemplo em C# de acoplamento excessivo:

```csharp
public class PedidoService
{
    public void Finalizar(Pedido p)
    {
        // acoplado a uma classe CONCRETA de e-mail: instancia com "new"
        var email = new SmtpEmailSender("smtp.gmail.com", 587);
        email.Enviar(p.ClienteEmail, "Pedido confirmado");
        // acoplado ao SQL Server direto, sem abstração
        var conn = new SqlConnection("Server=...;");
        conn.Open();
        // ...
    }
}
```

`PedidoService` está grudado ao SMTP e ao SQL Server *concretos*. Não dá pra testar sem um servidor
real, não dá pra trocar o provedor de e-mail, e mudar a conexão obriga a mexer aqui dentro. O `new`
espalhado é o cheiro do acoplamento.

### Coesão — queremos ALTA

**Coesão** é o quanto uma unidade (classe, método) está **focada numa única ideia**. Uma classe
altamente coesa faz *uma coisa* e tudo dentro dela existe pra servir a essa coisa.

- **Alta coesão** = uma caixa de ferramentas de marceneiro: tudo ali serve pra trabalhar madeira.
- **Baixa coesão** = uma gaveta de tranqueiras: martelo, conta de luz, pilha velha e um chiclete.

Baixa coesão gera a **classe God** — aquela `Utils`/`Manager`/`Helper` que faz de tudo um pouco.
Exemplo:

```csharp
public class Cliente
{
    public string Nome { get; set; }
    public decimal CalcularDesconto() { /* regra de negócio */ return 0; }
    public void SalvarNoBanco() { /* acesso a dados */ }
    public string GerarHtmlDoPerfil() { /* apresentação */ return ""; }
    public void EnviarEmailBoasVindas() { /* infraestrutura */ }
}
```

`Cliente` mistura **regra de negócio**, **persistência**, **apresentação** e **infraestrutura de
e-mail** — quatro ideias que mudam por razões diferentes, todas na mesma classe. Coesão baixíssima.

> **A régua-mestra do curso:** queremos **baixo acoplamento** (partes independentes) e **alta coesão**
> (partes focadas). Praticamente todo princípio SOLID é uma técnica para chegar num desses dois. Guarde
> essa frase — vamos repeti-la em todos os módulos.

---

## 4. Code smells que anunciam violação de SOLID

Um **code smell** não é um bug — o programa funciona. É um **sinal na superfície** de que há um
problema de design embaixo. Aprender a farejar os smells é o objetivo prático deste módulo, porque
cada smell tende a ser atacado por um princípio específico (que veremos a seguir).

| Smell | Como reconhecer | Princípio que ataca |
|---|---|---|
| **Classe God** | uma classe enorme que faz "tudo" (`Manager`, `Utils`) | **SRP** (Mód. 02) |
| **Método gigante** | um método de 200 linhas com muitos níveis de `if` | **SRP** (Mód. 02) |
| **`switch`/`if` sobre tipo** | um `switch (tipo)` que cresce a cada caso novo | **OCP** (Mód. 03) |
| **Flag booleana de comportamento** | `Processar(bool ehVip)` que muda o *que* o método faz | **OCP** (Mód. 03) |
| **Herança que quebra expectativa** | subclasse que joga exceção ou ignora um método herdado | **LSP** (Mód. 04) |
| **Interface gorda** | uma interface com 15 métodos; implementadores usam 3 | **ISP** (Mód. 05) |
| **`new` espalhado** | dependências concretas instanciadas dentro da classe | **DIP** (Mód. 06) |

Vamos aos dois mais traiçoeiros:

O **`switch` sobre tipo** é o smell que grita OCP:

```csharp
decimal CalcularFrete(Pedido p) => p.Tipo switch
{
    "normal"  => p.Peso * 2m,
    "expresso"=> p.Peso * 5m,
    "retirada"=> 0m,
    _         => throw new ArgumentException()
};
```

Toda vez que surgir um novo tipo de frete, você **edita** esse método — código que já funcionava. É
frágil e viscoso. O OCP vai transformar isso em polimorfismo (uma classe por tipo).

A **flag booleana de comportamento** é o mesmo mal disfarçado: `Salvar(bool comLog)` ou
`Notificar(bool porSms)` — o booleano acende/apaga *caminhos de comportamento* dentro do método, em
vez de você ter comportamentos separados.

> Não confunda "smell" com "erro". O código roda. O smell é um aviso de que a **próxima mudança** vai
> doer. Se não haverá próxima mudança, talvez o smell nem importe — o que nos leva à dosagem.

---

## 5. De onde vem SOLID, visão dos 5 e dosagem

### Origem

Os princípios foram **consolidados por Robert C. Martin (Uncle Bob)** por volta do fim dos anos 1990,
reunindo ideias de vários autores (Bertrand Meyer, Barbara Liskov, entre outros). O **acrônimo SOLID**
foi cunhado depois por **Michael Feathers**, reordenando as iniciais numa palavra fácil de lembrar.
Não são invenções de uma pessoa só nem "regras da Microsoft" — são padrões destilados de décadas de
experiência com OO.

### Os cinco, em uma linha cada (visão de mapa)

Aqui só apresentamos o mapa; **cada um ganha um módulo inteiro** depois.

| Letra | Princípio | Em uma frase | Ataca |
|---|---|---|---|
| **S** | **SRP** — Single Responsibility | uma classe deve ter uma só razão para mudar | classe God, método gigante |
| **O** | **OCP** — Open/Closed | aberto para extensão, fechado para modificação | `switch`/flag que cresce |
| **L** | **LSP** — Liskov Substitution | um subtipo deve poder substituir o supertipo sem surpresa | herança que quebra contrato |
| **I** | **ISP** — Interface Segregation | ninguém deve depender de métodos que não usa | interface gorda |
| **D** | **DIP** — Dependency Inversion | dependa de abstrações, não de implementações concretas | `new` espalhado, acoplamento a concreto |

Note o fio condutor: **quase todos existem para baixar acoplamento ou subir coesão** — exatamente a
régua da seção 3.

### Dosagem: princípios são heurísticas, não leis

Este é um tema que **volta em todo módulo**, então grave desde já:

> **SOLID mal aplicado vira over-engineering — e over-engineering é tão ruim quanto código rígido.**

Cada princípio é uma **heurística** a serviço do objetivo (mudança barata), não uma lei que você
obedece cegamente. Sinais de que você está exagerando:

- Criar uma interface `ICliente` com um único implementador `Cliente` "por via das dúvidas".
- Uma pirâmide de fábricas, estratégias e adaptadores para um código que muda uma vez por ano.
- Dividir uma classe coesa em cinco micro-classes anêmicas que só se chamam em cadeia.

O antídoto é o **YAGNI** — *You Aren't Gonna Need It*: não adicione flexibilidade **especulativa**.
Aplique um princípio quando houver **dor real ou mudança provável**, não pela estética. Abstrair cedo
demais congela o design errado e paga o custo da indireção sem colher o benefício.

A régua prática: **aplique o princípio quando ele reduzir o custo da mudança que você realmente
espera**. Se não há mudança à vista, o código simples e direto pode ser o *melhor* design — mesmo que
"viole" um princípio no papel.

---

## 6. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Design | A estrutura interna do código (fronteiras, classes, dependências). |
| Rigidez | Mudar é caro: um ajuste vira cascata. |
| Fragilidade | Mudar quebra coisas em lugares inesperados. |
| Imobilidade | Reaproveitar é caro: não dá pra desgrudar. |
| Viscosidade | O design premia a gambiarra sobre o caminho certo. |
| Acoplamento | Quão dependentes as partes são (queremos baixo). |
| Coesão | Quão focada uma unidade é (queremos alta). |
| Code smell | Sinal na superfície de um problema de design (não é bug). |
| Classe God | Classe que faz "de tudo"; baixa coesão. |
| SOLID | Os 5 princípios (SRP/OCP/LSP/ISP/DIP) consolidados por Uncle Bob. |
| YAGNI | "You Aren't Gonna Need It": não abstraia por especulação. |
| Over-engineering | Aplicar abstração/flexibilidade demais, sem necessidade real. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Por que "barato de mudar" é a métrica que decide se um design é bom? O que isso tem a ver com o fato
   de código ser lido/mudado mais do que escrito?
2. Diferencie **rigidez** de **fragilidade** com um exemplo de cada.
3. Qual a diferença entre **acoplamento** e **coesão**? Qual queremos alto e qual queremos baixo?
4. Cite três **code smells** e diga qual princípio SOLID cada um tende a atacar.
5. O que é **over-engineering** e como o **YAGNI** ajuda a evitar aplicar SOLID em excesso?

Quando estiver confortável com essas respostas, siga para **`pratica.md`** — lá você vai *diagnosticar*
um código de verdade.
