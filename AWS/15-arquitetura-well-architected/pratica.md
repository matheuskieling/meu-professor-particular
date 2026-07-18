# Módulo 15 — Arquitetura & Well-Architected (Prática Guiada)

> Objetivo desta prática: **exercitar o músculo de arquiteto**. Este módulo é de **DESENHO, não de
> provisionamento** — você não vai subir recursos; vai projetar soluções pra cenários reais,
> justificar cada escolha, e depois rodar uma **revisão Well-Architected de verdade** na ferramenta
> gratuita do console.
>
> **Abordagem:** exercícios no papel primeiro (com o Claude como revisor), console depois
> (Well-Architected Tool). Cada cenário tem os requisitos — a resposta certa **decorre deles**.
>
> ⏱️ Tempo estimado: 60–90 min. 💵 Custo: **US$ 0** — o Well-Architected Tool é gratuito e nenhum
> recurso de infraestrutura será criado.

---

## ⚠️ Antes de começar — leia isto

- Pegue **papel e caneta** (ou uma ferramenta de diagrama — draw.io, Excalidraw, o que preferir).
  Desenhar à mão vale mais que parecer bonito: o objetivo é **raciocinar em caixas e setas**.
- Não existe **uma** resposta certa nos exercícios — existe resposta **bem justificada**. O Claude
  vai fazer o papel de revisor: apresente seu desenho e **defenda os trade-offs**.
- Regra do jogo: pra cada componente do desenho, você deve saber dizer **qual requisito ele atende**
  e **o que acontece se ele falhar**.

---

## Parte A — Exercícios de arquitetura no papel

Para cada cenário: (1) liste os requisitos que enxerga, (2) desenhe, (3) aponte os trade-offs,
(4) apresente pro Claude e discuta. Só então leia as "pistas".

### Exercício 1 — E-commerce com picos

> **Cenário:** um e-commerce brasileiro médio. Tráfego normal: ~200 req/s. Na Black Friday: até
> 20× por algumas horas. Catálogo com muitas imagens. Checkout **não pode cair** nem perder pedidos.
> Orçamento consciente: pagar 20× a capacidade o ano todo está fora de questão.

Perguntas que seu desenho precisa responder:
- Como absorver 20× **sem pagar 20× sempre**?
- Onde entram **cache e CDN** pra tirar carga do backend?
- Como o **checkout** sobrevive a um pico acima do esperado (dica: o que uma fila faz com um pico?)
- O que é Multi-AZ aqui e o que é escala?

<details><summary>💡 Pistas (abra só depois de desenhar)</summary>

- CloudFront + S3 pras imagens/estático (a maior parte das requisições nem chega no servidor).
- ALB + ASG (scaling por métrica; a elasticidade é literalmente este requisito) em 2+ AZs.
- Cache de sessão/catálogo em ElastiCache; RDS Multi-AZ + réplicas de leitura pro catálogo.
- Pedido do checkout → **SQS** → workers: o pico vira fila com backlog, não erro 500. DLQ pra
  pedidos problemáticos.
- Pilares em tensão: custo × confiabilidade — e a resposta é elasticidade + desacoplamento.
</details>

### Exercício 2 — API global de baixa latência

> **Cenário:** uma API de consulta (leitura pesada, escrita rara) usada por apps móveis no Brasil,
> EUA e Europa. Requisito: **p95 < 100 ms** em todas as geografias. Dados mudam poucas vezes ao dia.

Perguntas que seu desenho precisa responder:
- Uma região só resolve p95 < 100 ms na Europa? (Física: RTT transatlântico já come o orçamento.)
- Como o usuário chega na **região certa**? (Lembra do módulo 14?)
- Leitura pesada + escrita rara + dados quase estáticos = que oportunidade gigante de **cache**?
- Serverless ou servidores? Justifique pelo perfil de carga.

<details><summary>💡 Pistas</summary>

- Multi-região (ex.: `sa-east-1`, `us-east-1`, `eu-west-1`) com **Route 53 latency routing**.
- CloudFront cacheando respostas da API (dados mudam pouco → TTL generoso + invalidação no deploy).
- DynamoDB **global tables** (réplicas multi-região, escrita em qualquer uma) ou Aurora global —
  discuta consistência eventual com o Claude.
- API Gateway + Lambda casa bem: carga variável por fuso, sem frota pra operar em 3 regiões.
</details>

### Exercício 3 — Batch noturno barato

> **Cenário:** processamento de relatórios que roda **1× por noite**, dura ~2 h, é pesado de CPU,
> e **pode ser interrompido e retomado** (processa arquivos independentes de uma fila). Prioridade
> absoluta: **menor custo possível**. Atraso de 1–2 h é aceitável.

Perguntas que seu desenho precisa responder:
- Servidor ligado 24 h pra rodar 2 h é qual anti-padrão?
- "Pode ser interrompido" + "menor custo" apontam pra qual tipo de instância? (Módulo 04/17!)
- De onde vem a lista de trabalho e pra onde vão os resultados?
- O que dispara o processamento no horário?

<details><summary>💡 Pistas</summary>

- **Spot instances** (até ~90% de desconto) — o requisito "interruptível" é o passe livre pro Spot.
- Arquivos em S3, lista de trabalho em SQS (retry de graça se a Spot for retomada), resultados no S3.
- EventBridge Scheduler dispara à noite; ASG (ou AWS Batch) sobe as instâncias, processa, e **escala
  a zero** ao terminar.
- Pilar dominante: custo — e repare como “relaxar” requisitos (latência, interrupção) derruba o preço.
</details>

### Exercício 4 — Crítica de arquitetura (caça aos anti-padrões)

O Claude vai te apresentar este desenho **defeituoso**. Ache **pelo menos 5 problemas** e proponha a correção:

> Uma única EC2 `m5.4xlarge` numa **subnet pública** roda app + banco MySQL local. Backup: um
> `mysqldump` semanal **guardado na própria instância**. Deploy: SSH + `git pull` na mão. SG
> liberando **22, 80 e 3306 pra 0.0.0.0/0**. Sem alarmes. Quando a carga sobe, o dono aumenta o
> tamanho da instância.

<details><summary>💡 Gabarito parcial</summary>

AZ única + instância única (SPOF) · banco junto do app e exposto (3306 público!) · backup na mesma
máquina que pode morrer (e nunca testado) · pet + deploy manual (sem IaC/CI-CD) · SSH aberto pro
mundo · escala vertical como única saída · sem observabilidade. Correção: o desenho de referência
da teoria, seção 4.
</details>

---

## Parte B — Revisão real no Well-Architected Tool (Console)

Agora a ferramenta oficial, de graça, com um workload de verdade: **a infraestrutura que você
construiu ao longo do curso** (ou o desenho do Exercício 1, se preferir).

### Passo 1 — Criar o workload
1. Console → busque **AWS Well-Architected Tool** → **Define workload**.
2. **Name:** `curso-aws-webapp` · **Description:** breve descrição da sua app do curso.
3. **Environment:** `Pre-production` · **Regions:** `us-east-1`.
4. **Lenses:** deixe só o **AWS Well-Architected Framework** (a lente padrão).
5. **Define workload**.

### Passo 2 — Responder o pilar de Confiabilidade
1. Abra o workload → **Start reviewing** → escolha o pilar **Reliability**.
2. Responda com **honestidade** as perguntas (ex.: *"How do you design your workload to withstand
   component failures?"*). Marque só as práticas que você **realmente** aplicou nos módulos
   (Multi-AZ? health checks? backups testados? auto scaling?).
3. Use o painel de ajuda de cada pergunta — os links são documentação de primeira.
4. Não precisa responder os 6 pilares agora; confiabilidade basta pro exercício (uns 20–30 min).

### Passo 3 — Ler o relatório
1. Volte ao workload → veja o **overview**: contagem de **High risks (HRIs)** e **Medium risks**.
2. Abra **Improvement plan**: a lista priorizada do que melhorar, com links.
3. Escolha **2 HRIs** e discuta com o Claude: *o risco é real pro seu caso? qual seria o custo de
   resolver? vale a pena AGORA?* — isso é pensamento de arquiteto (trade-off, de novo).
4. (Opcional) **Save milestone** (ex.: `revisao-modulo-15`) — a foto pra comparar no futuro.

> 💡 Repare no espírito da ferramenta: ela não te dá nota nem bloqueia nada. Ela **provoca as
> perguntas certas**. O relatório é o começo da conversa, não o fim.

---

## Parte C — CLI (bônus rápido)

O Well-Architected Tool também tem API — útil pra inventariar revisões em muitas contas:

```bash
aws wellarchitected list-workloads \
  --query "WorkloadSummaries[].{Nome:WorkloadName,Riscos:RiskCounts}" --output json

aws wellarchitected get-lens-review \
  --workload-id SEU-WORKLOAD-ID --lens-alias wellarchitected \
  --query "LensReview.PillarReviewSummaries[].{Pilar:PillarName,Riscos:RiskCounts}"
```

> `list-workloads` te dá o `WorkloadId`. Repare nos contadores de risco por pilar — é o mesmo
> relatório do console, em JSON (dá pra automatizar acompanhamento entre milestones).

---

## 🔥 Teardown

Nada pago foi criado 🎉 — o Well-Architected Tool é gratuito. Higiene mesmo assim:

1. Se não quiser guardar a revisão: workload → **Delete workload** (ou mantenha como referência —
   não custa nada e é um bom retrato do seu aprendizado).
2. Confirme que **nenhum recurso de infraestrutura** foi criado por engano durante os exercícios.

---

## ✅ Checklist de conclusão do módulo

- [ ] Sabe citar os **6 pilares** e o princípio central de cada um.
- [ ] Desenhou e defendeu o **e-commerce com picos** (elasticidade + fila no checkout).
- [ ] Desenhou e defendeu a **API global** (latency routing + cache + multi-região).
- [ ] Desenhou e defendeu o **batch noturno** (Spot + SQS + escala a zero).
- [ ] Achou 5+ anti-padrões no desenho defeituoso do Exercício 4.
- [ ] Criou um workload no **Well-Architected Tool** e respondeu o pilar de confiabilidade.
- [ ] Leu o improvement plan e discutiu 2 HRIs (resolver ou aceitar? por quê?).
- [ ] Workload de teste deletado (ou mantido conscientemente — é grátis).

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-15/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-15/`) e para o **Módulo 16 — CI/CD & DevOps**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 15" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
