# Módulo 19 — Projeto Final (Capstone) — BRIEFING

> Este módulo é diferente de todos os outros: **não há conteúdo novo**. Há um desafio.
> Você vai **projetar, estimar, construir, operar e destruir** uma aplicação completa na AWS,
> aplicando tudo dos Módulos 01–18. O Claude deixa de ser professor e vira **mentor de projeto**:
> revisa seu design, questiona decisões, destrava bloqueios — mas **quem decide e executa é você**.
> Este arquivo é o **briefing oficial**. O passo a passo por fases está em `pratica.md`.

---

## 1. O cenário

Você é a pessoa de engenharia da **"linkz.br"**, uma startup fictícia que quer lançar um
**encurtador de URLs** com estatísticas de acesso. O produto:

- Qualquer pessoa cola uma URL longa e recebe uma curta (`https://<seu-dominio-ou-alb>/r/Ab3xK9`).
- Acessar a URL curta **redireciona** (HTTP 301/302) pra URL original.
- Cada acesso é **contabilizado** (contador de cliques por link).
- Uma página/endpoint de estatísticas mostra os links mais acessados.

> 💡 **Alternativa aceita:** se preferir, troque por uma **galeria de fotos com upload**
> (upload → S3, listagem, thumbnail opcional). Os requisitos não-funcionais e a rubrica são os
> mesmos. O encurtador é o cenário de referência por ser pequeno no código e rico em arquitetura —
> o **produto é uma desculpa; o que está sendo avaliado é a infraestrutura**.

Por que esse cenário é bom de propósito:
- **Leitura >> escrita** — cria-se um link uma vez, acessa-se milhares (pensa em cache e em índices).
- **Dado simples** — chave→valor com um contador; qualquer banco do curso serve, e a escolha vira
  uma discussão de trade-off, não de sobrevivência.
- **Tráfego irregular** — picos quando um link viraliza (elasticidade tem que aparecer no design).
- **Todo mundo entende o produto em 10 segundos** — zero energia gasta explicando o domínio.

---

## 2. Requisitos funcionais (o mínimo que o produto faz)

| # | Requisito |
|---|-----------|
| RF1 | `POST /links` com uma URL longa → retorna o código curto (JSON). |
| RF2 | `GET /r/{codigo}` → redireciona (301/302) pra URL original. |
| RF3 | Cada redirecionamento incrementa o contador de cliques do link. |
| RF4 | `GET /stats` → top 10 links por cliques (JSON ou HTML simples). |
| RF5 | `GET /health` → healthcheck que **verifica a dependência de dados** (não só "estou vivo"). |

A aplicação em si pode ser minimalista (Python/Flask, Node/Express, o que você dominar —
50–150 linhas resolvem). **Não gaste seu tempo no código; gaste na infraestrutura.**

> Por que o RF5 insiste em "tocar o dado"? Porque um `/health` que só devolve `200 OK` fixo faz o
> ALB considerar saudável uma instância que perdeu o banco — e você aprendeu no Módulo 05/18 que
> health check ruim = failover que não acontece (ou acontece pro lugar errado).

---

## 3. Requisitos não-funcionais (onde o curso inteiro aparece)

| # | Requisito | Módulos que cobram |
|---|-----------|--------------------|
| RNF1 | **HA multi-AZ**: sobreviver à perda de uma AZ sem intervenção (ALB + ASG em 2+ AZs; dado replicado) | 03, 05, 07, 18 |
| RNF2 | **IaC**: 100% da infra descrita em código (Terraform ou CloudFormation) — zero recurso "de clique" no estado final | 11 |
| RNF3 | **CI/CD**: push na branch principal → pipeline testa e faz deploy sem passos manuais | 16 |
| RNF4 | **Observabilidade**: dashboard com métricas-chave, logs centralizados **com retenção**, e ≥ 2 alarmes acionáveis com notificação | 12 |
| RNF5 | **Segurança least-privilege**: roles por função (app, pipeline), SGs mínimos, dado privado, secrets fora do código, **zero credencial hardcoded** | 02, 13 |
| RNF6 | **Custo controlado**: estimativa prévia no Pricing Calculator, tags de alocação, budget do projeto; alvo de operação ≤ **US$ 5** no período do projeto | 17 |
| RNF7 | **Recuperabilidade**: backup automático do dado com **restauração testada** (provar RPO/RTO) | 18 |

### As decisões que são SUAS (e serão questionadas no design review)

O briefing **não** define compute, banco, edge, ferramenta de IaC nem de CI/CD — de propósito.
**Não existe resposta única**; existe decisão **justificada** por requisito, custo e simplicidade.
Os dois caminhos de referência (e é legítimo misturar):

| Dimensão | Caminho A — "clássico" | Caminho B — "serverless" |
|----------|------------------------|--------------------------|
| Compute | EC2 + ASG atrás de ALB | Lambda + API Gateway (ou Lambda + ALB) |
| Banco | RDS Multi-AZ | DynamoDB (PITR ligado) |
| HA multi-AZ | Você monta (subnets, ASG, Multi-AZ) | Vem de fábrica |
| Custo por dia parado | ALB + instâncias + RDS ≈ US$ 1,50–2,50/dia | ~centavos (pague por request) |
| O que exercita | Mais módulos do curso (rede, EC2, ASG, RDS) | Módulos 08/16; arquitetura mais atual |
| Riscos | Custo corre por dia; mais peças pra errar | Menos "mão na massa" de infra clássica |

Dica honesta: serverless tende a ganhar em custo pra este cenário; o clássico rende mais
aprendizado de infraestrutura. **Ambos aceitos — o que vale é o ADR justificando.**

---

## 4. Entregáveis

1. **Diagrama de arquitetura** — VPC/AZs (se houver), componentes, fluxo das requisições e do
   deploy. Ferramenta livre (draw.io, Mermaid, papel fotografado — conteúdo > estética).
2. **Repositório com IaC** — a infra completa como código, com README de como subir/destruir
   (`apply`/`destroy` documentados). Estrutura organizada, sem secrets no Git.
3. **Pipeline funcionando** — evidência de um deploy disparado por push (histórico do pipeline).
4. **Dashboard de observabilidade** — métricas-chave visíveis + alarmes configurados.
5. **Runbook de incidente** — 1 página: "app fora do ar → o que checar, em que ordem, comandos
   prontos" + procedimento de **restauração de backup** com RPO/RTO medidos.
6. **Estimativa de custo** — link/export do Pricing Calculator + comparação com o custo real
   observado no Cost Explorer ao final.
7. **Evidência do teste de falha** (fase 6) e do **teardown total** (fase 7).

Sobre o runbook (o entregável mais subestimado): escreva-o como se fosse pra **outra pessoa, às
3h da manhã, em pânico**. Ordem de verificação, comandos prontos pra colar, critérios de decisão
("se X, então Y"). No teste de falha da fase 6 você vai **usá-lo de verdade** — runbook que não
sobrevive ao próprio teste volta pra bancada.

---

## 5. Rubrica de avaliação

Em cada dimensão: **Insuficiente / Bom / Excelente**. Meta: **Bom em todas**; Excelente é bônus.

| Dimensão | Bom (esperado) | Excelente (bônus) |
|----------|----------------|-------------------|
| **Arquitetura & HA** | Multi-AZ real; sem SPOF óbvio; diagrama fiel ao implantado | Sobrevive ao teste de falha sem downtime perceptível; decisões documentadas (mini-ADRs) |
| **IaC** | Infra 100% em código; apply/destroy limpos e reproduzíveis | Módulos/parametrização; `plan` sem drift; state remoto |
| **CI/CD** | Push → deploy automático com etapa de teste | Deploy sem downtime (rolling/blue-green); rollback documentado |
| **Observabilidade** | Dashboard + 2 alarmes úteis + logs com retenção | Alarme pegou o teste de falha antes de você; métrica de negócio (redirects/min) |
| **Segurança** | Least-privilege nas roles; dado privado; secrets gerenciados | Justificativa por permissão; varredura de segredos no pipeline |
| **Custos** | Estimativa prévia; tags; budget; operação ≤ US$ 5 | Estimativa vs. real comparados e explicados; otimização aplicada e medida |
| **Resiliência** | Backup + restauração testada com RPO/RTO anotados | Runbook executado no teste de falha como roteiro real |
| **Teardown** | Conta zerada, checklist de caça completo | Destroy via IaC em um comando + varredura CLI provando o zero |

Como ler a rubrica: **"Insuficiente" em Segurança, Custos ou Teardown reprova o projeto**
independente do resto — são os hábitos inegociáveis do curso. Nas outras dimensões, um
"Insuficiente" vira item de retrabalho antes da retro final.

---

## 6. As fases (visão geral)

O projeto avança em **7 fases com marcos verificáveis** — detalhes e comandos em `pratica.md`:

| Fase | Nome | Marco de saída |
|------|------|----------------|
| 1 | **Design & estimativa** | Diagrama + decisões justificadas + estimativa de custo |
| — | **Design review com o Claude** | Design aprovado (ou revisado) antes de gastar 1 centavo |
| 2 | **Fundação: rede + dados (IaC)** | `apply` cria rede e camada de dados; backup já configurado |
| 3 | **App + compute** | Aplicação no ar atrás do ALB/endpoint, multi-AZ, health check verde |
| 4 | **CI/CD** | Push → deploy automático comprovado |
| 5 | **Observabilidade + alarmes** | Dashboard + alarmes testados (um disparo provocado) |
| 6 | **Teste de falha & recuperação** | Falha injetada, comportamento observado, backup restaurado |
| 7 | **TEARDOWN TOTAL + retro** | Conta zerada com evidência + retrospectiva com o Claude |

### Regras do jogo

- **Nada de recurso antes do design review.** Errar no papel é grátis; errar no `apply` custa.
- **Uma fase por vez**, com o marco batido antes da próxima — o Claude é o verificador.
- **⚠️ Custo:** este é o único módulo com recursos ligados por **dias** (ALB ~US$ 0,60/dia,
  NAT Gateway ~US$ 1,10/dia + instâncias/banco). Vigie o budget do projeto **diariamente**;
  entre sessões de trabalho, considere desligar o que puder. O alvo ≤ US$ 5 é parte da nota.
- **Trave a região** (`us-east-1`) e tagueie **tudo** com `Projeto=capstone` desde o primeiro recurso.
- **Git desde a fase 1** — diagrama, ADRs e IaC versionados. O repositório é um entregável.

### Ritmo sugerido (2–5 sessões)

| Sessão | Conteúdo |
|--------|----------|
| 1 | Fase 1 completa + design review (custo zero — sem pressa) |
| 2 | Fases 2 e 3 (a partir daqui o relógio de custo corre) |
| 3 | Fases 4 e 5 |
| 4 | Fase 6 + Fase 7 (falha, recuperação, teardown, retro) |

Se precisar pausar dias entre sessões: `destroy` no fim da sessão e `apply` na seguinte — IaC
reproduzível transforma "recurso ligado esquecido" em "30 segundos de re-provisionamento".

---

## 7. O papel do Claude (e o seu)

**O Claude vai:**
- Conduzir o **kickoff** e o **design review** (perguntas duras: "o que acontece se essa AZ
  cair?", "por que essa role tem `s3:*`?", "quanto custa isso por dia?").
- **Verificar cada marco** antes de liberar a fase seguinte — com evidências, não com "confia".
- Ajudar a depurar quando você **travar de verdade** (depois de você ter tentado).
- Propor o cenário do **teste de falha** e conduzir o post-mortem e a **retrospectiva final**.

**O Claude NÃO vai:**
- Escrever seu IaC inteiro, nem decidir sua arquitetura por você.
- Pular verificações de marco "pra agilizar".
- Aceitar "funcionou na minha máquina" como evidência. 😄

Se você pedir a resposta pronta, espere receber uma pergunta de volta. **A autonomia é o diploma
deste curso** — o projeto é onde você prova que ela existe.

---

## 8. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Capstone | Projeto final integrador: aplica todos os módulos numa entrega única. |
| ADR | Architecture Decision Record — registro curto de uma decisão e seu trade-off. |
| Design review | Revisão crítica do projeto ANTES de construir; barato de errar, caro de pular. |
| SPOF | Single Point of Failure — componente único cuja queda derruba o sistema. |
| Marco (milestone) | Critério verificável de saída de uma fase. |
| Runbook | Roteiro operacional de incidente: o que checar, em que ordem, com comandos prontos. |
| GameDay / teste de falha | Falha injetada de propósito pra validar HA, alarmes e runbook. |
| Retrospectiva | Análise final: o que funcionou, o que surpreendeu, o que fica de hábito. |

---

## Checagem de entendimento (antes do kickoff)

1. Explique o cenário e os 5 requisitos funcionais **sem olhar** o briefing.
2. Quais RNFs você acha que vão consumir mais tempo? Por quê?
3. Qual dupla compute+banco você está inclinado a escolher, e que trade-off ela carrega?
4. Quanto (estimado) custa por dia deixar a fase 3 no ar com a sua escolha?
5. Por que um `/health` que devolve `200` fixo é um requisito reprovado?
6. Quais três dimensões da rubrica reprovam o projeto sozinhas se ficarem "Insuficiente"?
7. O que precisa estar pronto **antes** de criar o primeiro recurso na AWS?

Pronto? Abra **`pratica.md`** e comece a Fase 1 — ou peça o kickoff ao Claude.
