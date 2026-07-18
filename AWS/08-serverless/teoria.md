# Módulo 08 — Serverless (Teoria)

> Objetivo do módulo: entender **o que serverless significa de verdade**, dominar o **AWS Lambda**
> (o coração do serverless na AWS), colocar uma **API HTTP** na frente dele com o **API Gateway**,
> pensar em **arquitetura orientada a eventos** e — tão importante quanto — saber **quando
> serverless NÃO é a resposta**. Você já conhece EC2 (Módulo 04): agora vai ver o extremo oposto
> do espectro de gerenciamento.

---

## 1. O que é serverless, de verdade

Primeiro, vamos matar o mal-entendido do nome:

> **Serverless não é "sem servidor". É "sem GERENCIAR servidor".**

Os servidores continuam existindo — datacenters, racks, CPUs, tudo lá. A diferença é **quem cuida
deles**: a AWS. Você não escolhe instância, não aplica patch de SO, não configura auto scaling,
não paga por máquina ociosa. Você entrega **código** (ou configuração) e a AWS cuida de
provisionar, escalar e manter a infraestrutura por baixo.

Compare com o que você já viveu no curso:

| | EC2 (Módulo 04) | Lambda (este módulo) |
|---|---|---|
| Provisionar | Você escolhe tipo, AMI, disco | Nada — só sobe o código |
| SO / patches | Responsabilidade sua | Responsabilidade da AWS |
| Escalar | ASG que você configura (Módulo 05) | Automático, de 0 a milhares |
| Ocioso | Paga por hora **ligado**, mesmo sem uso | **Custo zero** sem invocações |
| Cobrança | Por hora/segundo de instância | Por **invocação + duração×memória** |

As três propriedades que definem um serviço serverless:

1. **Zero gerenciamento de infraestrutura** — sem SO, sem capacidade pra planejar.
2. **Escala automática** — inclusive **até zero** quando não há demanda.
3. **Pague pelo uso real** — nenhuma requisição = nenhuma cobrança (de compute).

> 💡 Serverless é uma **categoria**, não um serviço. Lambda é serverless, mas S3, DynamoDB, SQS,
> SNS, EventBridge e Step Functions também são: você não gerencia servidor em nenhum deles.

---

## 2. AWS Lambda — anatomia de uma função

O Lambda executa **funções**: pedaços de código que rodam **em resposta a eventos**. Você não
tem um processo rodando 24/7 — a AWS materializa um ambiente de execução quando um evento chega,
roda sua função e (eventualmente) descarta o ambiente.

### O handler

Todo código Lambda tem um **handler**: a função que a AWS chama a cada invocação. Em Python:

```python
def lambda_handler(event, context):
    # event  = o evento que disparou a função (dict) — o formato varia por fonte!
    # context = metadados da execução (request id, tempo restante, etc.)
    return {"statusCode": 200, "body": "olá!"}
```

- **`event`** é a estrela: se veio do S3, traz bucket e chave do objeto; se veio do API Gateway,
  traz método, path, headers e body; se veio do SQS, traz um lote de mensagens.
- O **retorno** só importa em invocações **síncronas** (quem chamou está esperando a resposta,
  ex.: API Gateway). Em invocações **assíncronas** (ex.: S3), ninguém lê o retorno.

### Runtimes

Você escolhe o **runtime**: Python, Node.js, Java, .NET, Ruby, Go/Rust (via provided.al2023),
ou uma **imagem de container** própria. Neste curso usamos **Python** — sem build, edita no
próprio console.

### Memória, CPU e timeout

- **Memória:** de **128 MB a 10.240 MB**. Detalhe importante: **a CPU escala junto com a
  memória** — não existe knob separado de CPU. Função lenta? Às vezes **aumentar a memória
  barateia** (roda mais rápido, cobra menos duração).
- **Timeout:** máximo de **15 minutos**. Passou disso, a execução é morta. Se seu trabalho leva
  mais que 15 min, Lambda não é a ferramenta (spoiler da seção 8).

### Execution role — a identidade da função

Toda função assume uma **IAM role** (a **execution role**) enquanto roda. É ela que define **o
que a função pode fazer na AWS**: escrever logs no CloudWatch, ler um bucket S3, publicar no
SNS... Você já sabe do Módulo 02: **least privilege** — dê à role só o que a função precisa.

> ⚠️ **Armadilha clássica:** "minha função dá `AccessDenied` ao acessar o S3". Não é o seu
> usuário que precisa da permissão — é a **execution role da função**. São identidades diferentes.

### Variáveis de ambiente

Configuração vai em **variáveis de ambiente** (chave/valor), não hardcoded no código: nome de
bucket, URL de fila, flags. Para segredos de verdade, o certo é **Secrets Manager / SSM Parameter
Store** (Módulo 13) — env var aparece em texto claro pra quem pode ler a config da função.

---

## 3. Cold start e o ciclo de vida

Quando chega uma invocação e **não existe ambiente pronto**, a AWS precisa: criar o
micro-ambiente, baixar seu código, iniciar o runtime e rodar seu código de inicialização (imports,
conexões). Isso é o **cold start** — uma latência extra (de ~dezenas de ms em Python até segundos
em runtimes pesados como Java) **só na primeira invocação** daquele ambiente.

Depois disso o ambiente fica **quente** por um tempo: invocações seguintes reutilizam ele
(**warm start**, sem latência extra). Consequências práticas:

- Código **fora do handler** (imports, clientes boto3) roda **uma vez por ambiente** — ponha
  inicializações caras lá fora pra reaproveitar.
- Tráfego constante ≈ quase tudo warm. Tráfego esporádico = cold starts frequentes.
- Se cold start é inaceitável (API de latência crítica), existe **Provisioned Concurrency**
  (paga pra manter ambientes sempre quentes) — mas aí você já está pagando por ocioso de novo.

### Concorrência

Cada ambiente processa **uma invocação por vez**. 100 requisições simultâneas = 100 ambientes em
paralelo. Há um limite de **concorrência por conta/região** (padrão histórico: 1.000 execuções
simultâneas; contas novas começam com menos e podem pedir aumento).

---

## 4. Limites e preço

### Limites que você precisa saber de cabeça

| Limite | Valor |
|--------|-------|
| Timeout máximo | **15 minutos** |
| Memória | 128 MB – **10.240 MB** (CPU proporcional) |
| Pacote de deploy | 50 MB zipado / 250 MB descompactado (imagem de container: até 10 GB) |
| Payload síncrono | 6 MB requisição/resposta |
| `/tmp` (disco efêmero) | 512 MB (expansível até 10 GB) |
| Concorrência (padrão) | ~1.000 execuções simultâneas por região |

### Preço: invocações + GB-segundo

Você paga **duas coisas**:

1. **Por invocação:** ~US$ 0,20 por **milhão** de requisições.
2. **Por duração × memória:** medida em **GB-segundo** (~US$ 0,0000167/GB-s em x86).
   Função com 512 MB rodando 1 s = 0,5 GB-s.

**Free Tier (sempre grátis):** **1 milhão de invocações + 400.000 GB-s por mês**. É por isso que
a prática deste módulo custa **US$ 0** — você não vai chegar nem perto disso.

> 💡 Faça a conta uma vez na vida: 1 milhão de invocações de 200 ms com 128 MB ≈ 25.000 GB-s ≈
> **menos de meio dólar**. Pra cargas com tráfego irregular, é imbatível. Pra carga **constante e
> alta**, um EC2/Fargate bem dimensionado pode sair mais barato (seção 8).

---

## 5. Event sources — quem dispara a função

Lambda sozinho não faz nada: **alguém precisa invocar**. As fontes de evento que você vai usar
no curso (e as que caem em prova):

| Fonte | Tipo de invocação | Exemplo de uso |
|-------|-------------------|----------------|
| **API Gateway** | Síncrona (cliente espera resposta) | API HTTP → função responde JSON |
| **S3** | Assíncrona (fire-and-forget, com retry) | Objeto criado → processar arquivo |
| **EventBridge** | Assíncrona | Agendamento (cron) ou eventos de apps/AWS |
| **SQS** | **Poll-based** (o Lambda busca em lotes) | Fila de trabalho desacoplada |
| Invocação direta | Síncrona ou assíncrona | `aws lambda invoke` (CLI/SDK) |

Três modelos diferentes:
- **Síncrono:** quem chama espera e recebe o retorno. Erro = quem chamou decide o que fazer.
- **Assíncrono:** o evento entra numa fila interna; o Lambda tenta, e **retenta 2x** em caso de
  erro. Dá pra configurar um destino de falha (DLQ/destinations — reencontraremos no Módulo 10).
- **Poll:** pra fontes de stream/fila (SQS, Kinesis, DynamoDB Streams), o próprio serviço Lambda
  fica **puxando lotes** e invocando sua função com eles.

---

## 6. API Gateway — sua porta HTTP

Lambda não tem URL própria "de fábrica"\*. O **API Gateway** é o serviço gerenciado que fica na
frente: recebe requisições HTTP da internet, roteia pra sua função e devolve a resposta —
cuidando de TLS, throttling, autorização e CORS.

\* *Existe o "Function URL", um endpoint HTTPS direto e simples pra casos básicos — mas sem os
recursos de roteamento, stages e autorização do API Gateway.*

### REST API vs. HTTP API

O API Gateway tem dois sabores principais (e essa escolha cai em toda prova):

| | **HTTP API** (o moderno) | **REST API** (o clássico) |
|---|---|---|
| Preço | ~US$ 1,00/milhão req | ~US$ 3,50/milhão req |
| Latência | Menor | Maior |
| Recursos | O essencial: rotas, JWT authorizer, CORS | Tudo: API keys, usage plans, request validation, caching, WAF |
| Quando usar | **Padrão pra APIs novas** com Lambda | Quando precisar dos recursos avançados |

Regra prática do curso: **comece com HTTP API**; migre pra REST API só se sentir falta de algo.

### Rotas e stages

- **Rota** = método + path → integração. Ex.: `GET /ola` → Lambda `m08-hello`. Existe a rota
  `$default` (pega tudo que não casou) e paths com parâmetros (`GET /itens/{id}`).
- **Stage** = um "ambiente publicado" da API (ex.: `dev`, `prod`), cada um com sua URL. No HTTP
  API, o stage `$default` com **auto-deploy** publica cada mudança na hora — perfeito pra estudo.

---

## 7. Arquitetura event-driven e Step Functions

### Pensar em eventos, não em chamadas

Na arquitetura **orientada a eventos**, os componentes não se chamam diretamente — eles **emitem
eventos** ("pedido criado", "arquivo subiu") e outros componentes **reagem**. O produtor não
conhece o consumidor. Ganhos: **desacoplamento** (trocar/adicionar consumidores sem tocar no
produtor), **resiliência** (consumidor caiu? o evento espera) e **escala independente**.

O fluxo clássico que você vai montar na prática é o átomo dessa ideia:

```
upload no S3  ──evento──▶  Lambda processa  ──▶  log/resultado
```

Ninguém orquestrou nada: o S3 emitiu, o Lambda reagiu. O Módulo 10 (SQS/SNS/EventBridge)
aprofunda os "correios" que transportam esses eventos.

### Step Functions — quando o fluxo tem várias etapas

E quando o processo tem **múltiplos passos com ordem, condições e tratamento de erro**? Ex.:
"validar pedido → cobrar cartão → se falhou, estornar → notificar". Encadear Lambdas na mão vira
espaguete. O **Step Functions** resolve: você desenha uma **state machine** (máquina de estados)
em JSON/visual — estados de tarefa (chamar Lambda ou outros serviços), escolhas (`Choice`),
paralelismo, esperas, **retries e catch por estado** — e o serviço **orquestra e persiste** o
andamento de cada execução, com histórico visual de onde parou/falhou.

Dois tipos: **Standard** (durável, até 1 ano, paga por transição de estado — orquestrações de
negócio) e **Express** (alto volume, curto, paga por duração — processamento de eventos). Neste
módulo é só visão geral: saiba **o que é e quando chamar** o Step Functions.

---

## 8. Quando serverless NÃO é a resposta

Serverless é ferramenta, não religião. Sinais de que Lambda é a escolha **errada**:

- **Execuções longas:** mais de 15 minutos? Impossível no Lambda. Use Fargate/ECS (Módulo 09) ou Batch.
- **Carga alta e constante:** se você tem tráfego pesado 24/7, pagar por invocação sai **mais
  caro** que instâncias/containers dimensionados — o ponto forte do Lambda é a irregularidade.
- **Latência ultrassensível + tráfego esporádico:** cold starts vão aparecer (mitigável com
  Provisioned Concurrency, pagando).
- **Estado local / conexões persistentes:** WebSockets de longa duração, processos com muito
  estado em memória, apps que dependem de disco local durável.
- **Dependência pesada de SO/GPU** ou binários exóticos: possível via container image, mas
  talvez você esteja lutando contra a ferramenta.
- **Lift-and-shift:** reescrever um monólito em 200 Lambdas raramente é o primeiro passo certo.

> 🎯 Modelo mental: **tráfego irregular/eventos → serverless brilha. Carga constante e pesada ou
> jobs longos → containers/instâncias**. E dá pra misturar: API serverless + worker no Fargate.

---

## 9. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Serverless | Você não gerencia servidores; escala automática (até zero); paga pelo uso real. |
| Lambda | Serviço de funções sob demanda disparadas por eventos. |
| Handler | A função do seu código que a AWS chama a cada invocação (`event`, `context`). |
| Cold start | Latência extra quando a AWS precisa criar um ambiente novo pra executar. |
| Execution role | IAM role que a função assume — define o que ela pode fazer na AWS. |
| GB-segundo | Unidade de cobrança de duração: memória (GB) × tempo (s). |
| Event source | Quem dispara a função: API Gateway, S3, SQS, EventBridge... |
| API Gateway | Porta HTTP gerenciada na frente do Lambda (HTTP API = moderno/barato; REST = completo). |
| Stage | Versão publicada de uma API com URL própria (dev, prod, `$default`). |
| Event-driven | Arquitetura onde componentes emitem eventos e outros reagem, desacoplados. |
| Step Functions | Orquestrador de fluxos multi-etapas via state machines (Standard/Express). |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Por que dizer que serverless é "sem gerenciar servidor" e não "sem servidor"? O que exatamente
   deixa de ser problema seu em relação ao EC2?
2. O que é **cold start**, quando ele acontece e por que colocar inicializações fora do handler ajuda?
3. Sua função Lambda recebe `AccessDenied` ao ler um bucket S3. Onde está o problema e onde se conserta?
4. Quais as **duas dimensões** da cobrança do Lambda? Por que aumentar memória às vezes **barateia**?
5. Cite dois cenários em que Lambda é a escolha errada — e o que você usaria no lugar.

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
