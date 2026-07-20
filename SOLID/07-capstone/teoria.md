# Módulo 07 — Capstone: SOLID na prática, os 5 juntos (Teoria)

> Objetivo do módulo: **costurar** os cinco princípios num raciocínio só. Até aqui você viu SRP,
> OCP, LSP, ISP e DIP **isolados**. Na vida real eles quase nunca aparecem sozinhos — eles se
> **reforçam**. Aqui você vai entender **como um puxa o outro**, qual a **ordem mental** de
> refatorar um código bagunçado, como os **Design Patterns** são SOLID "com nome" e — o mais
> importante — **como dosar**: SOLID é heurística, não lei. Este é o último módulo do curso.

---

## 1. A teia: como os 5 princípios se reforçam

O erro mais comum de quem estuda SOLID é decorar cinco regras soltas. SOLID não é uma lista — é uma
**teia**. Cada princípio puxa o outro, e quando você aplica um de verdade, os outros aparecem quase
sozinhos.

O fio condutor de todos é o que você viu no **Módulo 01**: **baixo acoplamento** e **alta coesão**,
a serviço da **mudança**. Todo princípio SOLID é uma forma diferente de dizer "faça o código
resistir à mudança".

### As conexões, uma a uma

- **SRP → coesão.** Separar por *razão de mudar* (por ator) gera naturalmente classes **pequenas e
  coesas**. Uma classe que faz uma coisa só é fácil de nomear, testar e mudar.
- **ISP é o SRP das interfaces.** É a mesma ideia de coesão, mas aplicada ao **contrato** em vez da
  classe: uma interface deve ter um só motivo pra existir (um papel), não ser um catálogo de tudo.
- **OCP precisa de polimorfismo.** "Estender sem modificar" só funciona se houver um ponto de
  extensão polimórfico (uma abstração com várias implementações).
- **LSP torna o polimorfismo SEGURO.** De nada adianta o ponto de extensão do OCP se um subtipo
  **mente** sobre o contrato (estoura exceção, muda a semântica). LSP é a garantia de que trocar uma
  implementação por outra **não quebra** quem chama. Sem LSP, o OCP é uma bomba-relógio.
- **DIP fornece as abstrações.** Tanto o OCP quanto o ISP dependem de **abstrações** — e é o DIP que
  diz "dependa da abstração, não do concreto". Você estende contra uma interface (OCP), injeta uma
  interface enxuta (ISP+DIP), e substitui implementações com segurança (LSP).

> 💡 **A moral:** na prática você quase nunca aplica **um** princípio. Separar uma God class (SRP)
> costuma expor um `switch` que quer virar polimorfismo (OCP), que pede uma abstração (DIP) enxuta
> (ISP) e substituível (LSP). Eles vêm **em cascata**.

### Mapa smell → princípio

Guarde esta tabela: dado um cheiro, ela aponta o princípio que ataca. É o seu "raio-X" de código.

| Code smell (o cheiro) | Princípio que ataca | A cura, em uma frase |
|-----------------------|---------------------|----------------------|
| **God class** que faz de tudo (calcula, salva, notifica) | **SRP** | Separar por ator/razão de mudar |
| **`switch`/`if` por tipo** que cresce a cada variante | **OCP** | Polimorfismo (Strategy): nova variante = nova classe |
| **Subtipo que estoura** exceção ou muda a semântica | **LSP** | Rever a hierarquia; composição no lugar de herança |
| **Fat interface** que o cliente só usa pela metade | **ISP** | Quebrar em interfaces por papel |
| **`new` de concreto** de fronteira no meio da lógica | **DIP** | Depender de abstração e injetar no construtor |

---

## 2. A ordem mental de refatoração

Quando você abre um arquivo bagunçado, por onde começar? Existe um **roteiro mental** que funciona
bem. Repare: **não é uma receita rígida** — é uma sequência que ajuda porque **cada passo prepara o
próximo**.

1. **SRP — separe.** Pergunta: *quantas razões diferentes essa classe tem pra mudar?* Identifique os
   **atores** (quem pede mudança em quê: o financeiro pede mudança no cálculo, o time de infra no
   e-mail...) e quebre em classes por responsabilidade. Isso **revela** onde estão as costuras.
2. **OCP — estenda.** Agora olhe onde há **variação por tipo** (o `switch (tipoCliente)`, a cadeia de
   `if`). Crie um **ponto de extensão** polimórfico: uma abstração com uma implementação por variante.
3. **LSP — substitua.** Cada implementação/subtipo que você criou **honra o contrato**? Nenhuma pode
   estourar `NotSupportedException` nem devolver algo que quebre quem chama. Se um "subtipo" não é de
   verdade um substituto, prefira **composição** a herança.
4. **ISP — enxugue.** As interfaces que surgiram estão coesas **por papel**? Um cliente que só
   notifica deve depender de `INotificador`, não de uma interface que também salva e cobra.
5. **DIP — inverta.** Por fim, as dependências de **fronteira** (banco, e-mail, gateway de pagamento,
   relógio, sistema de arquivos) apontam pra classes concretas? Inverta pra **abstrações** e
   **injete** pelo construtor. Pronto pra DI do .NET e — de brinde — pronto pra **teste** (você
   troca o real por um fake).

> 🎯 **Por que essa ordem:** separar (SRP) **expõe** a variação (OCP); a variação vira uma abstração
> que precisa ser substituível (LSP) e enxuta (ISP); e essa abstração é o que você inverte e injeta
> (DIP). Um passo alimenta o outro. Mas se num caso concreto fizer mais sentido começar pelo `switch`
> gritante, comece por ele — o roteiro é um mapa, não um trilho.

---

## 3. A ponte para Design Patterns

Aqui está um segredo que economiza meses de estudo: **muitos dos padrões GoF (Gang of Four) são
SOLID "materializado"**. Eles são **soluções nomeadas e reconhecíveis** para respeitar um princípio.
Quando você entende o princípio, o padrão vira quase óbvio — e você para de decorar catálogo.

| Padrão | Princípio(s) que materializa | O que faz (e por quê é SOLID) |
|--------|------------------------------|-------------------------------|
| **Strategy** | OCP + DIP | Injeta o algoritmo por uma interface. Adicionar variante = nova classe, sem tocar no cliente. É **literalmente** o "depois" do `switch` do OCP. |
| **Factory Method / Abstract Factory** | DIP + OCP | Isola o `new` de concreto num único lugar, pra o resto do código depender só da abstração. |
| **Adapter** | LSP + ISP | Encaixa uma interface **incompatível** (uma lib de terceiro) na interface que seu código espera, sem quebrar o contrato de quem chama. |
| **Decorator** | OCP | Adiciona comportamento **envolvendo** o objeto (log, cache, retry) — estende sem modificar a classe original. |
| **Template Method** | OCP | Fixa o esqueleto de um algoritmo e deixa **passos** variáveis para subclasses/estratégias. |
| **Observer** | OCP + DIP | Desacopla quem **avisa** de quem **reage**; adicionar um novo "ouvinte" não mexe no emissor. |

Repare no **Strategy**: no Módulo 03 (OCP) você trocou um `switch (tipoDesconto)` por uma interface
`IDescontoStrategy` com implementações. Isso **tem um nome**: é o padrão Strategy. Você já aplicava
o padrão sem saber — porque entendeu o **princípio**.

```csharp
// Strategy = OCP+DIP com nome. A interface é o ponto de extensão; a implementação é injetada.
public interface IDescontoStrategy { decimal Calcular(decimal total); }

public sealed class SemDesconto      : IDescontoStrategy { public decimal Calcular(decimal t) => t; }
public sealed class DescontoVip      : IDescontoStrategy { public decimal Calcular(decimal t) => t * 0.90m; }
public sealed class DescontoBlackFri : IDescontoStrategy { public decimal Calcular(decimal t) => t * 0.70m; }

// Nova promoção? Nova classe. O código que USA a strategy não muda (OCP).
```

> 💡 **Moral:** **não decore** os 23 padrões. Entenda o **princípio por trás** de cada um. Quando
> alguém disser "use um Adapter aqui", você vai pensar "ah, é pra encaixar uma interface incompatível
> sem quebrar o contrato — LSP/ISP". O próximo curso natural depois deste é justamente **Design
> Patterns**, e você vai chegar lá com a base que faz os padrões fazerem sentido.

---

## 4. Dosagem final: SOLID é heurística, não lei

Este é o ponto **mais importante do curso inteiro**. Leia com atenção.

> **SOLID é uma HEURÍSTICA — um conjunto de bons palpites —, não uma lei.** Código **simples e
> direto** quase sempre vence código "SOLID" cheio de indireção. A abstração que você não precisava é
> **dívida**, não patrimônio.

O engenheiro júnior lê os 5 princípios e sai "solidificando" tudo: interface pra cada classe, fábrica
pra cada objeto, camadas que só repassam chamada. O resultado é um código que ninguém entende, com
seis arquivos pra fazer o que caberia em um. Isso é **over-engineering** — e é tão ruim quanto o God
class que ele estava tentando evitar.

### Quando aplicar um princípio: por DOR, não preventivamente

Aplique um princípio quando a **dor real** aparecer:

- **Duplicação real** — o mesmo código repetido, mudando junto. (E mesmo assim: veja a Regra dos Três.)
- **Mudança que dói** — toda vez que um requisito muda, você edita 5 arquivos e reza.
- **Necessidade de testar** — você não consegue testar a lógica porque ela faz `new SmtpClient()`
  no meio (aí sim, inverta e injete: DIP a serviço do teste).

Se **nenhuma** dessas dores existe, **não invente a abstração**.

### YAGNI e a Regra dos Três

- **YAGNI** (*You Aren't Gonna Need It*): não crie o ponto de extensão pra uma variação que talvez
  **nunca exista**. "E se um dia precisarmos de outro gateway de pagamento?" — quando precisar, você
  refatora (leva 10 minutos). Até lá, a abstração só atrapalha.
- **Regra dos Três**: só abstraia na **terceira** repetição. Uma ocorrência é uma ocorrência. Duas
  podem ser coincidência. Três é um padrão — aí vale a abstração, porque agora você **sabe** qual é a
  variação (você tem três exemplos dela), em vez de **adivinhar**.

> ⚠️ **Abstração errada é mais cara que duplicação.** Sandi Metz: *"duplication is far cheaper than
> the wrong abstraction"*. Apagar código repetido é trivial. **Desfazer** uma interface mal desenhada,
> que já tem 4 implementações e 20 chamadores, é uma reforma dolorosa. Na dúvida, **duplique e espere**
> — a abstração certa aparece quando você tem exemplos suficientes.

### O checklist honesto do PR

Antes de "solidificar" algo, faça a si mesmo estas perguntas:

1. **Estou aplicando por dor real** (mudança/teste/duplicação) **ou por dogma** ("o livro mandou")?
2. Essa **interface tem uma implementação só** e nenhuma outra à vista? (Se sim, provavelmente é
   indireção inútil — YAGNI.)
3. Consigo **explicar a indireção** sem dizer só "é SOLID"? Se a única justificativa é a sigla, é
   dogma.
4. Essa camada/fábrica **faz algo** ou só repassa a chamada adiante?

### Sinais de over-engineering (pare quando ver isso)

- Interfaces com **uma implementação só** e nenhuma segunda no horizonte.
- **Fábricas** pra construir objetos triviais (`new Pedido()` não precisa de `PedidoFactory`).
- Camadas de "serviço" que só **repassam** a chamada pra o repositório, sem lógica nenhuma.
- Um `IEnumerable<IStrategyFactoryProvider>` pra resolver um `if` de duas linhas.

> 🎯 **A régua final:** o objetivo nunca foi "ter SOLID". O objetivo é **código que resiste à
> mudança**. Se a indireção **não reduz** uma dor real, ela **é** a dor. Julgamento > dogma.

---

## 5. Recap do curso inteiro + checklist de code review

### Os 5, em uma frase cada

| Princípio | Em uma frase | Smell que ataca |
|-----------|--------------|-----------------|
| **SRP** | Uma classe, uma razão para mudar (um ator). | God class |
| **OCP** | Aberta para extensão, fechada para modificação. | `switch` por tipo que cresce |
| **LSP** | O subtipo substitui o supertipo **sem surpresas**. | Subtipo que estoura/mente |
| **ISP** | Interface por **papel**; ninguém depende do que não usa. | Fat interface |
| **DIP** | Dependa de **abstrações**, não de concretos; injete. | `new` de concreto de fronteira |

A grande lição que amarra tudo: **os princípios servem à MUDANÇA**. Reduzir acoplamento, aumentar
coesão, pra o código **resistir ao tempo** — sempre **dosando**, porque abstração demais também é
acoplamento (à indireção).

### Checklist de code review à luz de SOLID

Estas são as perguntas que você passa a fazer **em todo PR** (o seu e o dos outros):

- **SRP:** esta classe tem **mais de uma razão** para mudar? Dá pra nomeá-la sem usar "e"/"gerenciador"?
- **OCP:** este `switch`/`if` por tipo vai **crescer**? Uma variante nova exige editar código existente?
- **LSP:** este subtipo/implementação **honra o contrato**? Algum método estoura ou muda a semântica?
- **ISP:** algum cliente depende de uma interface e **usa só um pedaço** dela?
- **DIP:** isto faz **`new` de um concreto de fronteira** (banco, e-mail, HTTP, relógio) no meio da lógica?
- **Dosagem (o contrapeso, sempre junto):** isto resolve uma **dor real** ou é **dogma**? A interface
  tem mais de uma implementação? A indireção se **paga**?

> Um bom review não é "cadê o SOLID?" — é "esse código vai **doer** quando mudar? e a solução proposta
> **dói menos** que o problema?".

---

## 6. Glossário do módulo

| Termo | Em uma frase |
|-------|--------------|
| A "teia" do SOLID | Os 5 princípios se reforçam; aplicar um costuma exigir os outros. |
| Ordem de refatoração | Roteiro mental SRP→OCP→LSP→ISP→DIP (mapa, não trilho). |
| Design Pattern | Solução nomeada e recorrente; muitos são SOLID materializado. |
| Strategy | Padrão que injeta o algoritmo por interface (OCP+DIP). |
| Factory | Padrão que isola o `new` de concreto (DIP+OCP). |
| Adapter | Padrão que encaixa uma interface incompatível na esperada (LSP+ISP). |
| Decorator | Padrão que estende comportamento envolvendo o objeto (OCP). |
| Heurística | Bom palpite/guia, não regra absoluta — o que SOLID é. |
| YAGNI | "Você não vai precisar disso": não abstraia pra o futuro imaginado. |
| Regra dos Três | Só abstraia na terceira repetição, quando a variação é conhecida. |
| Over-engineering | Indireção que não paga uma dor real (interface com 1 impl, fábrica trivial). |

---

## Checagem de entendimento

Antes de ir pra prática (a maior do curso), tente responder:

1. Por que o **OCP depende do LSP**? O que acontece com o polimorfismo do OCP se um subtipo violar o
   contrato?
2. Em que sentido **ISP é "o SRP das interfaces"**?
3. Qual a **ordem mental** de refatoração e por que cada passo prepara o próximo?
4. Cite um **Design Pattern** e diga qual princípio ele materializa. Por que "não decorar patterns"?
5. Quando você **NÃO** deve aplicar um princípio? Explique YAGNI e a Regra dos Três, e por que
   "abstração errada é mais cara que duplicação".

Quando estiver confortável com essas respostas, siga para **`pratica.md`** — a refatoração
integradora que costura os cinco.
