# Módulo 05 — Escalabilidade & Balanceamento (Teoria)

> Objetivo do módulo: entender como uma aplicação sai de "um servidor sozinho rezando pra não cair"
> para uma **frota elástica e resiliente**: escalar horizontalmente com **Auto Scaling Groups**,
> padronizar instâncias com **Launch Templates** e distribuir tráfego com **Elastic Load Balancing**.
> Este é o módulo em que a promessa da nuvem — *elasticidade* — vira arquitetura concreta.
>
> Pré-requisitos: Módulo 03 (VPC, subnets, security groups) e Módulo 04 (EC2, AMIs, user data).

---

## 1. Escalabilidade vertical vs. horizontal

Quando sua aplicação não dá mais conta da carga, há dois caminhos:

| | **Vertical (scale up/down)** | **Horizontal (scale out/in)** |
|---|---|---|
| O que é | Trocar por uma máquina **maior** (mais CPU/RAM) | Adicionar **mais máquinas** iguais |
| Analogia | Trocar o fusca por um caminhão | Contratar mais entregadores de fusca |
| Limite | O teto do maior tipo de instância | Praticamente ilimitado |
| Downtime | Geralmente exige parar/reiniciar a instância | Zero — máquinas entram/saem ao vivo |
| Ponto único de falha | **Sim** — continua sendo 1 máquina | **Não** — a frota sobrevive à perda de membros |
| Exemplo AWS | `t3.micro` → `m5.2xlarge` | 2 instâncias → 10 instâncias atrás de um ELB |

**Regra mental:** vertical é simples mas tem teto e continua sendo um ponto único de falha.
Horizontal é o caminho da nuvem — mas **exige que a aplicação aceite rodar em várias cópias**
(ser *stateless*, ou externalizar o estado pra um banco/cache/S3). É por isso que arquitetura
importa: sessão gravada no disco local da instância = dor na hora de escalar horizontalmente.

> 💡 **Armadilha clássica:** escalar horizontalmente uma aplicação que guarda estado local
> (uploads no disco, sessão em memória). O usuário loga numa instância e "desloga" quando a
> requisição seguinte cai em outra. Solução: estado fora da instância (ElastiCache, DynamoDB, S3)
> — não *sticky sessions* como primeira opção (elas só adiam o problema).

---

## 2. Launch Templates — a "receita" da instância

Pra criar máquinas automaticamente, alguém precisa saber **como** criar cada uma. Esse alguém é o
**Launch Template**: um modelo versionado com tudo que você preencheria à mão ao lançar um EC2:

- AMI (imagem), tipo de instância (ex.: `t3.micro`), key pair;
- security groups, configurações de rede;
- **user data** (script de bootstrap — ex.: instalar e subir o nginx);
- tags, perfil IAM (instance profile), configurações de EBS, etc.

Pontos-chave:

- Launch Templates são **versionados**: mudou a receita, cria a versão 2 e aponta o ASG pra ela.
  Deu problema? Volta pra versão 1. (Isso é *rollback* de infraestrutura de graça.)
- Substituem as antigas **Launch Configurations** (deprecadas — não dá mais pra criar novas).
  Em 2025+, é Launch Template e ponto.
- Um template pode ser usado pra lançar instâncias avulsas, por ASGs, por Spot Fleets…

> 💡 O **user data** roda **uma vez, no primeiro boot**. É ali que você transforma uma AMI genérica
> na *sua* máquina (instalar pacotes, subir o serviço). Alternativa mais rápida de boot: assar uma
> **AMI customizada** ("golden AMI") com tudo pré-instalado — user data fica só pro ajuste fino.

---

## 3. Auto Scaling Groups (ASG) — a frota que se gerencia sozinha

O **Auto Scaling Group** é o serviço que mantém uma **frota de instâncias EC2** com o tamanho certo,
saudável e distribuída. Ele responde três perguntas:

1. **Quantas instâncias?** — `min`, `max` e `desired capacity`.
2. **Como criá-las?** — usando o Launch Template.
3. **Onde?** — nas subnets/AZs que você indicar (espalhe por **múltiplas AZs**!).

### min / max / desired

| Parâmetro | Significado |
|-----------|-------------|
| **Minimum** | O ASG nunca deixa a frota cair abaixo disso. |
| **Maximum** | O ASG nunca passa disso (sua trava de custo!). |
| **Desired** | Quantas ele quer **agora**. As políticas de scaling mexem neste número, sempre dentro de [min, max]. |

Exemplo: min=2, max=6, desired=2. Tráfego sobe → política aumenta desired pra 4 → ASG lança 2
instâncias. Tráfego cai → desired volta pra 2 → ASG termina 2 (scale in).

### O superpoder silencioso: auto-healing

Mesmo **sem nenhuma política de scaling**, um ASG já vale ouro: se uma instância falha o health
check (ou alguém a termina), o ASG **substitui automaticamente** pra manter o desired. É a
diferença entre "acordar às 3h pra subir o servidor" e "a plataforma repôs sozinha".

### Políticas de scaling (quando e quanto escalar)

| Política | Como funciona | Quando usar |
|----------|---------------|-------------|
| **Target tracking** | "Mantenha a CPU média em 50%" — o ASG calcula sozinho quantas instâncias precisa. Funciona como um termostato. | **Padrão recomendado.** Simples e eficaz. |
| **Step scaling** | Alarmes do CloudWatch com degraus: CPU > 70% → +2; CPU > 90% → +4. | Quando você quer controle fino da reação. |
| **Simple scaling** | Alarme dispara → ação única → espera o cooldown. | Legado; prefira as anteriores. |
| **Scheduled** | Escala por horário: "às 8h, desired=10; às 20h, desired=2". | Carga previsível (horário comercial, batch). |
| **Predictive** | ML analisa o histórico e escala **antes** do pico. | Padrões cíclicos bem definidos. |

> ⚠️ **Cooldown / warmup:** depois de escalar, o ASG espera um período antes de reagir de novo
> (instância nova demora pra ficar pronta e pra aparecer nas métricas). Sem isso, você teria
> *flapping*: escala pra cima, métrica ainda alta, escala mais, aí sobra máquina, escala pra baixo…

### Health checks do ASG

- **EC2 (padrão):** a instância está rodando? (checagem de hardware/hipervisor.)
- **ELB:** o load balancer considera o **target saudável**? Muito mais útil — pega o caso da
  máquina ligada mas com a aplicação morta.

> 💡 **Armadilha clássica:** ASG atrás de um ALB usando só health check **EC2**. A aplicação trava,
> a instância continua "running", o ASG acha tudo lindo — e o ALB fica sem targets saudáveis.
> **Sempre habilite o health check ELB quando houver load balancer.**

---

## 4. Elastic Load Balancing (ELB) — distribuindo o tráfego

Com várias instâncias, alguém precisa ficar na porta distribuindo as requisições. É o **load
balancer**: um ponto de entrada único (um DNS name) que espalha o tráfego entre **targets**
saudáveis, em múltiplas AZs.

### Os três tipos que importam

| | **ALB** (Application) | **NLB** (Network) | **GWLB** (Gateway) |
|---|---|---|---|
| Camada OSI | 7 (HTTP/HTTPS) | 4 (TCP/UDP/TLS) | 3 (IP) |
| Enxerga | URLs, headers, métodos, host | Conexões TCP/UDP | Pacotes IP (GENEVE) |
| Roteamento | Por **path**, **host**, header, query string | Por porta/protocolo | Encadeia appliances |
| Performance | Ótima | **Extrema** — milhões de req/s, latência ultrabaixa | — |
| IP fixo | Não (DNS name) | **Sim** (Elastic IP por AZ) | — |
| Uso típico | **Aplicações web / APIs / microsserviços** | Jogos, IoT, TCP puro, IP fixo exigido | Firewalls e appliances de inspeção de terceiros |

**Como escolher:** aplicação web/HTTP → **ALB** (99% dos casos deste curso). Precisa de TCP/UDP puro,
latência mínima ou IP estático → **NLB**. Precisa inserir um firewall/IDS de terceiro no caminho do
tráfego → **GWLB**. (O antigo **Classic Load Balancer** foi aposentado — não use.)

### A anatomia de um ALB: listeners, regras e target groups

Três peças que você precisa saber montar (e vai montar na prática):

1. **Listener** — "em qual porta/protocolo eu escuto?" Ex.: HTTP:80, HTTPS:443. É no listener
   HTTPS que mora o certificado TLS (via ACM).
2. **Regras (rules)** — "pra onde mando cada requisição?" Avaliadas em ordem de prioridade:
   - `path = /api/*` → target group dos backends;
   - `host = admin.exemplo.com` → target group do admin;
   - regra **default** → target group principal.
   Também dá pra responder direto (fixed response) ou redirecionar (HTTP→HTTPS).
3. **Target group** — o conjunto de destinos (instâncias, IPs ou funções Lambda) + a configuração
   de **health check**. O ALB só envia tráfego pra targets **healthy**.

### Health checks do ALB

O ALB testa cada target periodicamente: faz uma requisição (ex.: `GET /` ou `GET /health`) e espera
um código de sucesso (ex.: 200). Parâmetros: intervalo, timeout, **healthy threshold** (quantos
sucessos seguidos pra voltar a receber tráfego) e **unhealthy threshold** (quantas falhas pra sair
de rotação).

> 💡 Crie um endpoint `/health` **barato** (sem tocar no banco a cada check) mas **honesto** (que
> falhe se a aplicação realmente não consegue servir). Health check que sempre responde 200 é
> enfeite.

### Connection draining (deregistration delay)

Quando um target vai sair (scale in, deploy, falha), o ALB para de mandar **novas** requisições pra
ele, mas dá um prazo — o **deregistration delay** (padrão: 300s) — pras requisições **em andamento**
terminarem. Sem isso, todo scale in derrubaria conexões no meio. Pra apps de resposta rápida, reduzir
pra 30–60s acelera deploys e scale in sem cortar ninguém.

---

## 5. ASG + ALB: o casamento

A arquitetura clássica de alta disponibilidade na AWS junta as peças:

```
                Internet
                   │
              ┌────▼────┐
              │   ALB   │  (em 2+ AZs, subnets públicas)
              └────┬────┘
          listener HTTP:80 → target group "web"
                   │
        ┌──────────┴──────────┐
   ┌────▼────┐           ┌────▼────┐
   │ EC2 #1  │           │ EC2 #2  │   ← ASG (min=2, desired=2, max=4)
   │  AZ-a   │           │  AZ-b   │      Launch Template + user data
   └─────────┘           └─────────┘
```

Como se integram:

- Você **anexa o target group ao ASG**. A partir daí, toda instância que o ASG lança é
  **registrada automaticamente** no target group; toda que ele termina é desregistrada
  (respeitando o draining). Você nunca registra instância na mão.
- Com health check **ELB** habilitado no ASG, o ciclo fecha: app morre → ALB marca unhealthy →
  ASG termina e **repõe** a instância → a nova se registra sozinha → tráfego normalizado.
  Tudo sem intervenção humana.
- Usuário acessa **o DNS do ALB** (ou um alias no Route 53) — nunca o IP de uma instância.

> ⚠️ **Armadilha de security group:** o SG das instâncias deve aceitar tráfego na porta da app
> **vindo do SG do ALB** (referencie o SG, não `0.0.0.0/0`). O SG do ALB é que fica aberto pra
> internet (80/443). Health check falhando com app no ar? 9 em 10 vezes é SG bloqueando o ALB.

> ⚠️ **Armadilha de custo:** o ALB cobra **por hora de existência** (~US$ 0,0225/h em `us-east-1`,
> ± US$ 16/mês) + LCUs de uso. **Não fica de graça parado.** Na prática deste módulo, o teardown é
> obrigatório e rigoroso.

---

## 6. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Scale up/out | Vertical (máquina maior) / horizontal (mais máquinas). |
| Launch Template | Receita versionada de como lançar uma instância (AMI, tipo, user data…). |
| ASG | Frota de EC2 auto-gerenciada: mantém tamanho, saúde e distribuição por AZs. |
| min/max/desired | Piso, teto e alvo atual da frota; políticas mexem no desired. |
| Target tracking | Política "termostato": mantém uma métrica no alvo (ex.: CPU 50%). |
| ELB | Família de load balancers gerenciados da AWS. |
| ALB / NLB / GWLB | Camada 7 (HTTP) / camada 4 (TCP-UDP, IP fixo) / camada 3 (appliances). |
| Listener | Porta/protocolo em que o LB escuta (ex.: HTTP:80). |
| Target group | Conjunto de destinos + health check; o LB só envia pra targets healthy. |
| Deregistration delay | Prazo pras conexões em andamento terminarem antes do target sair (draining). |
| Auto-healing | ASG repõe sozinho instâncias que falham o health check. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Por que escalar **horizontalmente** exige que a aplicação seja (quase) stateless?
2. Num ASG com min=2, desired=3, max=6: o que acontece se você terminar uma instância na mão?
3. Quando você escolheria um **NLB** em vez de um **ALB**? Cite duas razões.
4. Por que um ASG atrás de ALB deve usar health check **ELB** e não só **EC2**?
5. O que o **deregistration delay** evita durante um scale in?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
