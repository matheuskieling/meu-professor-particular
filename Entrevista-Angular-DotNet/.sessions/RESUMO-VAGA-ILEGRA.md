# 🎯 RESUMO DA VAGA — Ilegra (Fullstack Pleno) — reler antes das 18h (22/07)

> Rodada extra em cima do **perfil da vaga** (a base Angular+.NET está no RESUMO-PARA-AMANHA.md).
> Stack da vaga: **Angular** + C#/.NET Core · AWS (ECS, EC2, RDS/Aurora, DynamoDB, S3, SQS, CloudWatch)
> · microsserviços · RabbitMQ/Kafka · PostgreSQL · GitHub Actions · SOLID/Patterns · **DataDog/APM**.
> ⚠️ Eles usam **Angular** (não Next). Se perguntarem: "tenho Next em produção e Angular em produção também".

---

## ⭐ Os 4 pontos amarelos desta rodada (maior prioridade)

### 1. Kafka vs Fila (SQS/RabbitMQ) — **está no meu CV, quase certo perguntarem**
- **Fila (SQS/RabbitMQ)** = "faça esta tarefa": mensagem é **consumida e some** (ack → apaga); vai pra **um** worker.
  Uso: email, relatório, pagamento — trabalho pontual.
- **Kafka** = "isto aconteceu": **log append-only persistente**; mensagem **fica** (dias); **vários consumidores**
  leem a **mesma** no seu ritmo (offset); dá pra **reprocessar**. Uso: streaming, event sourcing, alto throughput,
  muitos sistemas reagindo ao mesmo evento.
- 🔑 Frase: **"fila some, Kafka fica"**. Escolho Kafka quando: muitos consumidores do mesmo evento · reprocessar
  histórico · throughput altíssimo · auditoria/retenção.

### 2. Observabilidade / APM — **está na minha carta (DataDog, correlação de logs)**
- **Logs** = eventos discretos com contexto ("14:03, request X falhou") → investigar um caso.
- **Métricas** = números agregados no tempo (req/s, latência p95, taxa de erro) → dashboard + alerta.
- **Traces** = caminho de UMA request pelos microsserviços (spans + tempo por salto) → achar o gargalo.
- **APM** (Application Performance Monitoring — DataDog/New Relic) = **junta os 3** e **correlaciona**:
  da métrica que alertou → trace da request lenta → log da causa raiz. Isso é a "correlação de logs" da minha carta.

### 3. Fluxo AWS ponta a ponta (relatório pesado assíncrono)
1. API (ECS) publica na **SQS** e responde **202 Accepted** na hora com `jobId`.
2. **Worker** (ECS ou Lambda) consome, gera o relatório (30s).
3. Salva resultado no **S3**; atualiza status (ex.: DynamoDB `jobId → done + link`).
4. Usuário recupera por **polling** ou **push** (WebSocket/SignalR/email com **presigned URL**).
- Por que SQS: **desacopla** (worker cai → mensagem fica), **absorve pico**, **escala worker sozinho**. + **DLQ** pras falhas.

### 4. Síncrono vs Assíncrono entre microsserviços
- Pergunta-chave: **o chamador precisa da resposta AGORA pra continuar?**
- **Síncrono (REST)**: queries/validação que bloqueiam a tela. Trade-off: **acoplamento temporal** (B fora → A falha);
  mitiga com timeout, retry, **circuit breaker**.
- **Assíncrono (broker)**: evento "fire and forget", outros reagem quando puderem. Trade-off: complexidade +
  **consistência eventual** (dado não sincroniza na hora). → NÃO é "99% async"; síncrono é certo pra query.

---

## ✅ Fui bem (entre confiante)
- **Design Pattern com história real:** Downloader → **Factory** (cria a Strategy certa por tipo) + **Strategy**
  (cada `IDownloader.Download()` diferente) → tirou os `if`, ficou **OCP** (aberto extensão / fechado modificação).
- **DIP:** injeto `IEmailSender` em vez de `new SmtpEmailSender()` → troco impl sem tocar no service, mock no teste.
  É a base da DI do .NET. **ISP:** interfaces pequenas, ninguém implementa método que não usa.
- **SQS + worker** pra desacoplar processamento pesado (instinto certo).

---

## 🎯 Postura na entrevista
- **Conte histórias reais:** Downloader (Factory), microsserviços na Progress Rail (Rabbit/Kafka, times em inglês),
  AWS no dia a dia (ECS/SQS/RDS/Dynamo), pool de conexões (DbContext/Dispose).
- **Puxe a nuance você mesmo:** "async melhora throughput não latência", "DbContext já é UoW", "consistência eventual é o preço do async".
- **Se travar, pensa em voz alta** — mostram o raciocínio.

> Reler: este arquivo + RESUMO-PARA-AMANHA.md (seção "🎯 Reforçar"). Respira. Você está pronto. 🚀
