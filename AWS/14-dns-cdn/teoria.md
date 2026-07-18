# Módulo 14 — DNS & Entrega de Conteúdo (Teoria)

> Objetivo do módulo: entender **como o DNS funciona** de verdade, dominar o **Route 53** (o DNS
> da AWS) e suas **políticas de roteamento**, e colocar uma **CDN (CloudFront)** na frente do seu
> conteúdo com **HTTPS gratuito (ACM)**. Ao final, você saberá responder: "como o navegador acha
> meu servidor?" e "como entrego conteúdo rápido pro mundo inteiro sem multiplicar servidores?".

---

## 1. Recap: como o DNS funciona

DNS (Domain Name System) é a "lista telefônica" da internet: traduz **nomes** (`www.exemplo.com`)
em **endereços IP** (`52.94.13.7`). Sem ele, você digitaria IPs no navegador.

Quando você acessa `www.exemplo.com`, acontece (simplificando):

1. O navegador pergunta ao **resolver** (geralmente do seu provedor, ou 8.8.8.8/1.1.1.1).
2. O resolver pergunta aos **root servers** → "quem cuida de `.com`?"
3. Os servidores do **TLD** `.com` respondem → "quem cuida de `exemplo.com` é o name server X".
4. O **name server autoritativo** (ex.: Route 53) responde com o registro final: o IP.
5. O resolver **cacheia** a resposta pelo tempo do **TTL** e devolve ao navegador.

### Tipos de registro que você precisa conhecer

| Tipo | Aponta para | Exemplo de uso |
|------|-------------|----------------|
| **A** | Endereço IPv4 | `www.exemplo.com → 52.94.13.7` |
| **AAAA** | Endereço IPv6 | `www.exemplo.com → 2600:1f18::...` |
| **CNAME** | Outro **nome** (apelido) | `blog.exemplo.com → app.hospedagem.com` |
| **TXT** | Texto livre | Verificação de domínio, SPF/DKIM (e-mail), validação do ACM |
| **MX** | Servidor de e-mail | `exemplo.com → mail.google.com (prioridade 10)` |
| **NS** | Name servers da zona | Delegação: quem responde por esse domínio |

### TTL (Time To Live)

Cada registro tem um **TTL em segundos**: por quanto tempo os resolvers podem **cachear** a
resposta. TTL alto (ex.: 86400 = 1 dia) → menos consultas, mais barato, **mas mudanças demoram a
propagar**. TTL baixo (ex.: 60) → mudanças rápidas, mais consultas.

> 💡 **Truque de profissional:** vai fazer uma migração de IP? **Baixe o TTL dias antes** (ex.: pra
> 60s), migre, confirme, e depois suba o TTL de novo. "Propagação de DNS" lenta é quase sempre
> cache antigo respeitando um TTL alto.

> ⚠️ **Limitação clássica do CNAME:** pelo padrão do DNS, o **apex/raiz do domínio**
> (`exemplo.com`, sem `www`) **não pode ser CNAME** — ele precisa coexistir com registros NS/SOA.
> Guarde isso: é exatamente o problema que o **alias record** do Route 53 resolve.

---

## 2. Route 53 — o DNS da AWS

**Route 53** é o serviço de DNS gerenciado da AWS (o nome vem da porta 53, a porta do DNS). É um
serviço **global** (como IAM e CloudFront) e faz três coisas distintas — não confunda:

1. **Registro de domínio** — comprar/renovar domínios (ex.: `meusite.com` por ~US$ 14/ano).
2. **Hospedagem de DNS (hosted zones)** — responder às consultas DNS do seu domínio.
3. **Health checks** — monitorar endpoints e reagir (essencial para failover).

Você pode usar cada parte separadamente: dá pra registrar o domínio no Registro.br ou GoDaddy e
hospedar o DNS no Route 53 (apontando os NS), ou vice-versa.

### Hosted zones: públicas vs. privadas

| | Hosted zone **pública** | Hosted zone **privada** |
|---|---|---|
| Responde para | A internet inteira | Só **dentro das VPCs associadas** |
| Uso típico | Seu site/domínio público | Nomes internos (`db.interno.local`) |
| Precisa de domínio registrado? | Sim (pra funcionar de verdade) | **Não** — qualquer nome serve |
| Custo | **US$ 0,50/mês por zona** | US$ 0,50/mês por zona |

> 💡 A hosted zone privada é ótima pra dar nomes amigáveis a recursos internos: em vez do endpoint
> gigante do RDS (`meudb.abc123.us-east-1.rds.amazonaws.com`), sua app usa `db.interno.local` —
> e se o endpoint mudar, você troca **num lugar só**.

### Alias records — a diferença crucial pra CNAME

O **alias** é uma extensão **proprietária do Route 53** que aponta um nome para um **recurso AWS**
(CloudFront, ALB, S3 website, API Gateway, outra hosted zone...). Parece um CNAME, mas:

| | CNAME | Alias (Route 53) |
|---|---|---|
| Funciona no **apex** (`exemplo.com`)? | ❌ Não (padrão DNS proíbe) | ✅ **Sim** |
| Custo das consultas | Cobradas | **Grátis** quando aponta pra recurso AWS |
| Aponta para | Qualquer nome DNS | Recursos AWS (e registros da mesma zona) |
| Como responde | Devolve o nome (resolver segue) | Devolve **direto o(s) IP(s)** do recurso |
| Acompanha mudança de IP do recurso | — | ✅ Automático (a AWS atualiza) |

**Regra mental:** apontando pra recurso AWS dentro do Route 53 → **use alias, sempre**. CNAME fica
pra apontar pra nomes fora da AWS ou quando você não usa Route 53.

### Health checks

O Route 53 pode monitorar um endpoint (HTTP/HTTPS/TCP) de vários pontos do mundo e marcá-lo como
saudável/doente. Isso alimenta a política de **failover** (abaixo): se o primário morrer, o DNS
passa a responder com o secundário. Health checks de endpoints AWS são baratos; com opções
avançadas (HTTPS, string matching) custam um pouco mais.

---

## 3. Políticas de roteamento do Route 53

Ao criar um registro, você escolhe **como** o Route 53 responde quando há múltiplas opções:

| Política | Como responde | Caso de uso |
|----------|---------------|-------------|
| **Simple** | Sempre o(s) mesmo(s) valor(es) | O padrão; um site, um destino |
| **Weighted** | Distribui por **pesos** (ex.: 90/10) | Canary/teste A-B: mandar 10% pro ambiente novo |
| **Latency** | O recurso com **menor latência** pro usuário | App multi-região: brasileiro → `sa-east-1`, europeu → `eu-west-1` |
| **Failover** | Primário enquanto saudável; **secundário se o health check falhar** | DR: site principal + página estática de contingência no S3 |
| **Geolocation** | Baseado na **localização** do usuário (país/continente) | Conteúdo por país, conformidade legal, idioma |

> 💡 Existem ainda **Geoproximity** (distância + "bias" ajustável) e **Multivalue answer** (até 8
> respostas saudáveis, um "mini balanceamento" via DNS). Para o exame e para a vida, domine as 5 da
> tabela.

> ⚠️ **DNS não é load balancer.** Weighted/multivalue distribuem *resoluções*, mas o cache dos
> resolvers e dos clientes torna a distribuição imprecisa e o failover lento (TTL!). Para balancear
> de verdade, use ELB (módulo 05); o DNS decide **pra qual região/endpoint** ir, o ELB balanceia
> **dentro** dele.

---

## 4. CloudFront — a CDN da AWS

**CloudFront** é a **CDN (Content Delivery Network)** da AWS: uma rede com **centenas de edge
locations** pelo mundo (lembra do módulo 01?) que **cacheia seu conteúdo perto do usuário**.

O fluxo:

1. Usuário em Tóquio acessa `d1234.cloudfront.net/logo.png`.
2. O DNS o direciona à **edge location mais próxima** (Tóquio).
3. A edge tem o objeto em cache? **Hit** → entrega na hora (latência mínima).
4. Não tem? **Miss** → busca na **origem** (seu S3/servidor), entrega **e guarda em cache** para
   os próximos.

Benefícios: latência menor no mundo todo, menos carga (e menos custo de requisições) na origem,
proteção extra (absorve tráfego, integra com WAF/Shield — módulo 13), HTTPS na borda.

### Conceitos de uma distribuição

- **Distribuição (distribution)** — a unidade do CloudFront. Ganha um domínio `dXXXX.cloudfront.net`.
- **Origem (origin)** — de onde o conteúdo vem:
  - **S3** — o caso clássico pra conteúdo estático (site, imagens, vídeos, downloads);
  - **Custom origin** — qualquer HTTP: um ALB, API Gateway, ou servidor fora da AWS.
- **Behavior (comportamento)** — regras por padrão de caminho (`/api/*` → origem A sem cache;
  `/static/*` → origem B com cache longo). Toda distribuição tem o behavior padrão `*`.
- **TTLs de cache** — quanto tempo a edge guarda o objeto (min/default/max), controlado por **cache
  policies** e pelos headers `Cache-Control` que a origem envia.

### OAC — Origin Access Control (S3 privado atrás do CloudFront)

O problema: se o bucket S3 é público, qualquer um pode **contornar o CloudFront** e bater direto no
bucket (sem cache, sem WAF, sem HTTPS custom, sem seus controles). A solução moderna:

> **OAC (Origin Access Control):** o bucket fica **100% privado** e a bucket policy autoriza
> **somente o serviço CloudFront** (via principal `cloudfront.amazonaws.com`, condicionado ao ARN da
> sua distribuição) a ler os objetos. O CloudFront **assina** as requisições à origem (SigV4).

Resultado: o único caminho até seu conteúdo é **através da distribuição**. 

> 💡 OAC é o sucessor do **OAI (Origin Access Identity)**, o método legado. Em material antigo você
> verá OAI; em tudo novo (e no exame atual), a resposta é **OAC** — suporta SSE-KMS, todas as
> regiões e métodos HTTP, o que o OAI não suportava direito.

### Invalidações

Subiu uma versão nova do `index.html` mas as edges ainda servem a antiga (TTL não expirou)? Você
pode **invalidar** caminhos (`/index.html` ou `/*`), forçando as edges a buscar de novo na origem.

- **As primeiras 1.000 invalidações de caminho por mês são grátis**; depois, US$ 0,005 por caminho.
- `/*` conta como **1 caminho** — e é o "botão de pânico" mais comum.

> 💡 **Boa prática de verdade:** em vez de invalidar toda hora, **versione os nomes dos assets**
> (`app.v2.js`, hashes no nome do arquivo — todo bundler faz isso). Nome novo = objeto novo = nunca
> precisa invalidar; só o `index.html` fica com TTL curto.

> ⚠️ **Custo do CloudFront:** o free tier do CloudFront é generoso (1 TB de transferência/mês e
> 10 milhões de requisições **sempre grátis**). Para estudo, é efetivamente US$ 0. O que custa em
> produção: transferência acima disso e invalidações em excesso.

---

## 5. ACM — certificados TLS gratuitos

**AWS Certificate Manager (ACM)** emite e **renova automaticamente** certificados TLS **públicos e
gratuitos** para usar em serviços AWS (CloudFront, ALB, API Gateway).

- **Validação:** você prova que controla o domínio. O método recomendado é **por DNS** — o ACM te dá
  um registro **CNAME de validação**; se a zona está no Route 53, um botão cria o registro pra você.
  Enquanto o CNAME existir, a **renovação é automática e eterna**. (Alternativa: por e-mail — evite,
  renovação manual.)
- **Não dá pra baixar** a chave privada de certificados públicos do ACM — eles só funcionam
  **acoplados a serviços AWS**. Pra usar num servidor próprio, seria Let's Encrypt ou similar.

> ⚠️ **A pegadinha nº 1 do módulo (cai em prova e na vida real):** para usar um certificado no
> **CloudFront**, ele **TEM que estar em `us-east-1`** (N. Virginia). Não importa onde está sua
> origem ou seus usuários — CloudFront é global e só enxerga certificados de `us-east-1`. Para um
> **ALB**, o certificado deve estar **na mesma região** do ALB.

Com as três peças juntas, o combo clássico de site estático profissional:
**S3 privado (OAC) ← CloudFront (cache + HTTPS) ← Route 53 (alias no seu domínio) + ACM (certificado em us-east-1)**.

---

## 6. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Registro A / AAAA | Nome → IP (v4 / v6). |
| CNAME | Nome → outro nome; **proibido no apex** do domínio. |
| TTL | Quanto tempo os resolvers podem cachear a resposta. |
| Hosted zone | O "banco de registros" de um domínio no Route 53 (pública ou privada). |
| Alias record | Extensão do Route 53: aponta pra recurso AWS, funciona no apex, consultas grátis. |
| Política de roteamento | Como o Route 53 escolhe a resposta (simple, weighted, latency, failover, geolocation). |
| Health check | Monitoramento de endpoint que alimenta o failover. |
| Edge location | Ponto de presença da CDN, perto do usuário. |
| Distribuição / origem / behavior | A unidade do CloudFront / de onde vem o conteúdo / regras por caminho. |
| OAC | Bucket privado que só o CloudFront consegue ler (sucessor do OAI). |
| Invalidação | Forçar as edges a descartar o cache de um caminho (1.000/mês grátis). |
| ACM | Certificados TLS gratuitos e auto-renováveis; pro CloudFront, **sempre em us-east-1**. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Por que o **apex** do domínio não pode ter CNAME, e como o **alias** do Route 53 resolve isso?
2. Você vai migrar um serviço de IP. O que faz com o **TTL** antes e depois — e por quê?
3. Qual política de roteamento você usaria para: (a) mandar 5% do tráfego pra uma versão nova;
   (b) direcionar cada usuário à região mais rápida; (c) chavear pra um site de contingência?
4. O que o **OAC** garante que um bucket público atrás do CloudFront não garante?
5. Onde deve estar um certificado ACM usado por uma distribuição CloudFront? E por um ALB em `sa-east-1`?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
