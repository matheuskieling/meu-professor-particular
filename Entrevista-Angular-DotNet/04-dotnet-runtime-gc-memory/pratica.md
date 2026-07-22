# Prática — Simulação de entrevista (Módulo 04)

Este arquivo é o roteiro da **simulação de entrevista**. O agente faz cada pergunta, o aluno responde
**sem olhar a teoria**, e o agente critica: o que faltou, o que ficou impreciso, e como soar mais
sênior. A regra de ouro em toda resposta: **resposta direta primeiro**, depois o **detalhe técnico**
que impressiona.

---

### Pergunta 1 — Qual a diferença entre .NET Framework e .NET Core / .NET 8?

**Resposta-modelo:**
".NET Framework é o legado: só Windows, acoplado ao SO, em manutenção — não recebe features novas.
.NET Core foi a reescrita cross-platform (Windows, Linux, macOS), open source, modular via NuGet e
mais performática. A partir do .NET 5, a Microsoft dropou o 'Core' do nome e virou 'só .NET',
unificando tudo — desktop, web, mobile — numa base única; .NET 8 é o LTS atual. Migro pra .NET
moderno por cross-platform, performance e por Framework estar em fim de linha."

**Erros comuns:**
- Dizer só "Core é mais novo/melhor" sem os eixos concretos (cross-platform, open source, modular,
  performance).
- Não saber que o "Core" saiu do nome no .NET 5.
- Confundir **.NET Standard** (contrato de API) com um runtime.

---

### Pergunta 2 — O que é o .NET Standard e quando ele importa?

**Resposta-modelo:**
".NET Standard não é um runtime — é uma especificação de API, um contrato. Uma biblioteca que mira
`netstandard2.0` consegue rodar tanto em .NET Framework quanto em .NET Core/5+. Hoje ele importa
basicamente pra dar suporte a Framework legado; código novo que só roda em .NET 6+ mira o TFM do
runtime direto, tipo `net8.0`."

**Erros comuns:**
- Tratar .NET Standard como se fosse uma versão do runtime.
- Não saber para que serve (compartilhar código entre Framework e Core).

---

### Pergunta 3 — O que acontece entre escrever C# e a CPU executar? Fale de IL e JIT.

**Resposta-modelo:**
"O compilador C#, o Roslyn, não gera código de máquina no build — gera IL, um bytecode independente
de CPU, empacotado no assembly com metadados. Em runtime, o JIT do CLR compila esse IL pra código
nativo, método a método, na primeira chamada de cada método, e cacheia. Código gerenciado é o que
roda sob o CLR, com GC e type safety. Se eu quero startup instantâneo em container, uso Native AOT,
que compila tudo pra nativo antes, sem JIT."

**Erros comuns:**
- Dizer que C# é "interpretado" ou que "compila direto pra nativo no build".
- Não distinguir código gerenciado de unmanaged.
- Não citar JIT como o passo de runtime.

---

### Pergunta 4 — Diferença entre value type e reference type. E stack vs heap?

**Resposta-modelo:**
"Value type — struct, int, enum, DateTime — guarda o valor direto e tem semântica de cópia por
valor: copiei, mexi na cópia, o original não muda. Reference type — class, string, array — guarda uma
referência pro objeto no heap; copiar copia só a referência, então dois nomes apontam pro mesmo
objeto. Como regra, value type local vive na stack, que é rápida e liberada ao sair do método, e
objeto de class vive no heap, gerenciado pelo GC."

**Erros comuns:**
- Não saber a diferença de **semântica de cópia**.
- Achar que `string` é value type (é reference, mas imutável).
- Não mencionar que o GC gerencia o heap.

---

### Pergunta 5 — "Struct sempre vive na stack." Verdadeiro ou falso?

**Resposta-modelo:**
"Impreciso. Um value type como variável local vive na stack, sim. Mas se ele é campo de uma class,
ele mora no heap junto com o objeto; se é capturado por uma closure ou sofre boxing, também vai pro
heap. Então o que decide é onde a variável mora, não só o tipo. A frase certa é: 'value type como
variável local vive na stack'."

**Erros comuns:**
- Responder "verdadeiro" sem ressalva — é a pegadinha.
- Não dar um caso concreto (campo de classe, boxing, closure).

---

### Pergunta 6 — O que é boxing? Qual o custo e como evitar?

**Resposta-modelo:**
"Boxing é empacotar um value type dentro de um objeto no heap pra tratá-lo como object ou interface —
aloca no heap e copia o valor. Unboxing é extrair de volta com cast explícito. O custo é uma alocação
no heap por operação, que pressiona o GC e vira gargalo em loop quente. Evito com generics: `List<int>`
não faz boxing porque T é resolvido pro tipo concreto, mas `ArrayList` faz porque guarda object.
Também cuido de Equals, interpolação de string e chamadas de interface em structs, que fazem boxing
escondido."

**Erros comuns:**
- Achar que `List<int>` faz boxing (não faz — é o ponto dos generics).
- Não citar o custo (alocação + pressão no GC).
- Não saber onde acontece escondido (coleções não-genéricas, `object.Equals`).

---

### Pergunta 7 — Como funciona o Garbage Collector? Por que ele existe?

**Resposta-modelo:**
"Existe porque a memória é gerenciada: eu não dou free, o GC libera automaticamente o que não é mais
alcançável, o que elimina leaks de esquecimento e dangling pointers. Ele parte das raízes — variáveis
locais na stack, campos static, handles — e marca tudo que consegue alcançar por referência. O que
não marcou é lixo, e ele recupera essa memória; depois compacta os objetos vivos pra desfragmentar o
heap, atualizando as referências. É não-determinístico, uso tracing por alcançabilidade, não contagem
de referência — então ciclos de referência são coletados normalmente."

**Erros comuns:**
- Dizer que o GC usa **contagem de referência** (é tracing).
- Não citar as raízes nem o mark-sweep-compact.
- Esquecer que é não-determinístico.

---

### Pergunta 8 — O que são as gerações do GC e por que existem?

**Resposta-modelo:**
"Existem por causa da hipótese geracional: empiricamente, a maioria dos objetos morre jovem — DTOs de
request, temporários. Então, em vez de varrer o heap inteiro toda vez, o GC particiona por idade e
coleta principalmente a Gen0, que é barato e frequente, recuperando quase todo o lixo com pouco
trabalho. Gen0 é o recém-alocado, Gen1 é um buffer, Gen2 são os longevos, com coleta cara e rara —
sobreviveu a uma coleta, é promovido. Gen2 é o teto, e coletar Gen2 é um full GC, que inclui Gen0 e
Gen1."

**Erros comuns:**
- Não saber explicar **por que** (a hipótese geracional é o que impressiona).
- Achar que existe Gen3, Gen4.
- Não saber que sobreviventes são promovidos.

---

### Pergunta 9 — O que é o LOH? E workstation vs server GC?

**Resposta-modelo:**
"O LOH, Large Object Heap, guarda objetos com 85 KB ou mais. Ele é logicamente Gen2 — só é coletado
em GC de Gen2 — e por padrão não é compactado, porque mover objetos grandes é caro; o preço disso é
fragmentação, e dá pra forçar compactação pontual com GCSettings. Sobre os modos: workstation GC é
o padrão em apps client, otimiza latência e usa um heap. Server GC usa vários heaps e threads de GC,
um por CPU lógica, otimiza throughput — é o padrão típico em ASP.NET Core em servidor multi-core."

**Erros comuns:**
- Não saber o limiar de ~85 KB.
- Não saber que o LOH não compacta por padrão.
- Confundir workstation (latência) com server (throughput).

---

### Pergunta 10 — Existe memory leak em .NET? Se sim, como acontece?

**Resposta-modelo:**
"Existe, sim. O GC só coleta o que não é mais alcançável, então basta eu deixar de usar um objeto mas
mantê-lo referenciado por alguma raiz viva. O caso clássico é event handler: `publisher.Evento +=
handler` faz o publisher segurar o subscriber; se o publisher vive muito e eu esqueço o `-=`, o
subscriber nunca é coletado. Outros: static que só cresce, cache sem eviction, closure capturando
objeto, timer não cancelado, e IDisposable não liberado, que segura recurso unmanaged. Diagnostico com
dotnet-counters pra ver o heap subir e nunca descer, e tiro um gcdump pra achar o caminho de raiz que
retém o objeto."

**Erros comuns:**
- Responder "não existe leak porque tem GC" — errado.
- Não saber explicar o mecanismo (algo ainda alcançável).
- Não dar o exemplo do event handler.

---

### Pergunta 11 — O que é Span<T> e por que ele aparece em código de performance?

**Resposta-modelo:**
"Span<T> é uma view sobre memória contígua — um array, uma string, um buffer de stackalloc — que
deixa fatiar e parsear sem copiar e sem alocar novos objetos, reduzindo a pressão no GC. Isso importa
em caminho quente: parsing, serialização, hot loops — menos alocação, menos GC, mais throughput. Ele
é um ref struct, então só vive na stack: não pode ser campo de classe nem ser usado em método async.
Quando preciso disso, uso Memory<T>, que vive no heap e me dá .Span quando preciso da view."

**Erros comuns:**
- Não saber que é um ref struct (só stack).
- Tentar usar Span<T> em async — não compila; aí é Memory<T>.
- Não conectar com redução de alocação / pressão no GC.

---

### Pergunta 12 — O que é stackalloc e quando você usaria?

**Resposta-modelo:**
"stackalloc aloca um buffer na stack em vez do heap gerenciado, então tem zero pressão no GC. Uso pra
buffers pequenos e de vida curta em caminho quente — tipicamente combinado com Span<T>, tipo
`Span<byte> buf = stackalloc byte[128]`. Cuidados: tamanho, porque buffer grande causa stack overflow,
e escopo, porque a memória não pode escapar do método. É uma otimização pontual, não default."

**Erros comuns:**
- Achar que stackalloc aloca no heap.
- Não citar os riscos (stack overflow, escopo).
- Não mencionar a combinação com Span<T>.
