# Módulo 13 — Segurança Avançada (Teoria)

> Objetivo do módulo: subir o nível do que você aprendeu no Módulo 02. Você vai dominar
> **criptografia com KMS** (incluindo **envelope encryption**, o padrão que sustenta quase tudo),
> gerenciar segredos (**Secrets Manager** vs. **Parameter Store**), proteger a borda (**WAF** e
> **Shield**), detectar ameaças (**GuardDuty**, Security Hub, Inspector) e refinar o IAM
> (**permission boundaries**, políticas de sessão, condition keys). O fio condutor: **defesa em
> profundidade** — nenhuma camada sozinha basta.

---

## 1. Defesa em profundidade

Segurança boa não é um muro alto; é **várias camadas** independentes, cada uma assumindo que a
anterior pode falhar:

```
Borda        →  WAF / Shield (filtra tráfego malicioso antes de chegar)
Rede         →  VPC, security groups, NACLs (Módulo 03)
Identidade   →  IAM: quem pode o quê (Módulo 02 + avançado aqui)
Dados        →  Criptografia em repouso (KMS) e em trânsito (TLS)
Segredos     →  Secrets Manager / Parameter Store (nunca hardcoded)
Detecção     →  GuardDuty, CloudTrail, Security Hub (assuma que algo vai passar)
```

> 💡 Analogia do castelo: fosso, muralha, portões, guardas, cofre — e sentinelas vigiando por
> dentro. Se o invasor pula o fosso, ainda tem tudo o resto. Um bucket com criptografia, política
> restrita **e** monitoramento sobrevive ao erro que um bucket "só com senha boa" não sobrevive.

---

## 2. KMS — o serviço de chaves

O **AWS KMS** (Key Management Service) cria e guarda **chaves criptográficas** que **nunca saem
do serviço**. Você não recebe a chave; você pede pro KMS *usar* a chave por você (criptografar,
descriptografar, assinar) — e **cada uso passa pelo IAM e fica no CloudTrail**. Isso transforma
criptografia em controle de acesso auditável.

### 2.1 Tipos de chave

| Tipo | Quem gerencia | Custo | Controle |
|------|---------------|-------|----------|
| **AWS owned** | AWS, invisível pra você | Grátis | Nenhum (nem aparece na sua conta) |
| **AWS managed** (`aws/s3`, `aws/rds`...) | AWS, mas visível na sua conta | Grátis | Só visualização; a policy é fixa; rotação anual automática |
| **Customer managed (CMK)** | **Você** | **~US$ 1/mês por chave** + uso | Total: key policy, rotação, grants, agendamento de deleção |

> ⚠️ **Custo:** cada chave customer managed custa **US$ 1/mês** (pró-rata) só por existir, mais o
> uso (com 20 mil requisições/mês no free tier). Na prática vamos criar **uma** e **agendar a
> deleção** no teardown. Detalhe importante: chave KMS **não se apaga na hora** — você agenda a
> deleção com espera de **7 a 30 dias** (é proteção: apagar uma chave torna **irrecuperável** tudo
> que ela protege).

### 2.2 Key policies

Toda CMK tem uma **key policy** — uma resource policy própria da chave, que define quem pode
**administrá-la** e quem pode **usá-la**. Peculiaridade do KMS: a key policy é a **raiz** do
acesso — diferente de outros serviços, se a key policy não permitir (nem delegar ao IAM), **nem o
admin da conta usa a chave**. A boa prática separa papéis: administradores da chave (gerem, não
usam) ≠ usuários da chave (usam, não gerem).

### 2.3 Envelope encryption — entenda isso de verdade

O KMS tem uma limitação proposital: a API `Encrypt` só aceita até **4 KB**. Como criptografar um
arquivo de 1 GB? Resposta: **envelope encryption**, o padrão usado por S3, EBS, RDS e tudo mais.

**Criptografar:**
1. Você pede ao KMS: `GenerateDataKey` (referenciando sua CMK).
2. O KMS devolve **duas versões da mesma data key**: uma em **texto claro** e uma **criptografada
   pela CMK**.
3. Você criptografa **seu arquivo localmente** com a data key em claro (rápido, local, sem limite
   de tamanho — AES-256).
4. **Apaga a data key em claro da memória** e guarda a **versão criptografada junto do arquivo**
   (o "envelope": o dado lacrado + a chave do lacre, ela mesma lacrada).

**Descriptografar:**
1. Envia a data key **criptografada** pro KMS: `Decrypt` (o KMS sabe qual CMK usar — está nos metadados).
2. O KMS — **se o IAM/key policy permitir** — devolve a data key em claro.
3. Você descriptografa o arquivo localmente. Apaga a data key da memória.

Por que esse malabarismo?
- A **CMK nunca sai do KMS** — o segredo-mestre jamais viaja.
- Dados grandes são criptografados **localmente** (rápido); o KMS só processa a chavinha de 32 bytes.
- **Revogação centralizada:** sem permissão na CMK, ninguém abre data key nenhuma — milhões de
  arquivos ficam ilegíveis com **uma** mudança de policy.

> 💡 Analogia: o arquivo vai num **cofre** (data key); a chave do cofre é guardada dentro de um
> **envelope lacrado pelo mestre** (CMK), colado no próprio cofre. Só quem convence o mestre
> (KMS+IAM) consegue abrir o envelope — e o mestre nunca entrega o seu próprio segredo.

### 2.4 Rotação

- **AWS managed keys:** rotação **automática anual**, sem você fazer nada.
- **Customer managed:** rotação automática **opcional** (anual, habilitável). O KMS guarda as versões
  antigas do material — dados antigos continuam legíveis, novos usos pegam o material novo, e o
  ARN/ID da chave **não muda** (nada quebra nas aplicações).

---

## 3. Segredos: Secrets Manager vs. Parameter Store

Regra número zero: **segredo não vive em código, variável de ambiente commitada ou .env no Git**.
Vive num serviço de segredos, buscado em runtime com permissão IAM. As duas opções:

| Critério | **Secrets Manager** | **SSM Parameter Store** |
|----------|--------------------|-----------------------|
| Propósito | Segredos, com ciclo de vida completo | Configurações em geral (e segredos simples) |
| Preço | **US$ 0,40/secret/mês** + API | **Standard: grátis** (advanced: ~US$ 0,05/mês) |
| Criptografia | Sempre (KMS) | Opcional: tipo **SecureString** (KMS) |
| **Rotação automática** | **Sim, nativa** (Lambda; integração pronta com RDS etc.) | Não nativa (faça você mesmo) |
| Geração de senha | Sim (`get-random-password`) | Não |
| Deleção | Janela de recuperação 7–30 dias (bypass: `--force-delete-without-recovery`) | Imediata |

**Como escolher:** senha de banco de produção que precisa **girar sozinha** → Secrets Manager
(os US$ 0,40 pagam a rotação nativa). Configuração da aplicação, flags, endpoints — e até segredos
que você gira manualmente → Parameter Store **SecureString** (grátis, criptografado por KMS).
Muita gente usa os dois: Secrets pra credenciais críticas, Parameter Store pro resto.

> 💡 O Parameter Store organiza por **hierarquia de caminhos** (`/meuapp/prod/db-url`), o que
> permite dar permissão IAM por prefixo — `/meuapp/prod/*` só pra role de produção.

---

## 4. Criptografia em repouso e em trânsito (nos serviços que você já usa)

Dois momentos, duas proteções:

- **Em trânsito** — TLS/HTTPS no caminho. Toda API da AWS já é HTTPS; sua parte é garantir TLS
  **na sua aplicação** (ALB com certificado do ACM, forçar HTTPS no S3 via condition
  `aws:SecureTransport`, `require_secure_transport` no RDS...).
- **Em repouso** — dados criptografados no disco. Na AWS, é quase sempre **envelope encryption com
  KMS** por baixo:

| Serviço | Como fica |
|---------|-----------|
| **S3** | SSE-S3 (chave da AWS) é o **padrão desde 2023** — todo objeto novo já nasce criptografado; SSE-KMS quando você quer **sua** CMK (controle+auditoria por objeto). |
| **EBS** | Flag "encrypted" no volume (KMS). Dá pra ligar **encryption by default** na conta/região — ligue. Snapshots herdam. |
| **RDS** | Criptografia habilitada **na criação** (KMS). ⚠️ Não dá pra ligar depois num banco existente — o caminho é snapshot → copiar criptografando → restaurar. |

> ⚠️ **Armadilha de prova e de vida real:** criptografia em repouso do RDS/EBS protege contra
> acesso físico ao disco/snapshot — **não** substitui controle de acesso. Um `SELECT *` com
> credencial válida lê tudo normalmente; a criptografia é transparente pra quem tem permissão.

---

## 5. Proteção de borda: WAF e Shield

- **AWS WAF** — firewall de **camada 7** (HTTP/HTTPS). Você cria uma **Web ACL** com regras e a
  associa a um recurso de borda (CloudFront, ALB, API Gateway). Regras podem ser:
  - **Managed rules** — pacotes prontos (da AWS e de terceiros): core rule set OWASP, SQL injection,
    IPs de má reputação, bots. O jeito realista de começar.
  - **Suas regras** — por IP/CIDR, país, header, padrão na URL/corpo.
  - **Rate limiting** (rate-based rules) — bloqueia IPs que passem de N requisições em 5 minutos.
    Defesa básica contra brute force e scraping.
  - Custo: ~US$ 5/mês por Web ACL + ~US$ 1/regra + ~US$ 0,60/milhão de requisições.

- **AWS Shield** — proteção contra **DDoS**:
  - **Standard:** **grátis e automático** pra todo mundo — mitiga ataques comuns de camada 3/4
    (SYN floods, reflection) sem você fazer nada.
  - **Advanced:** ~US$ 3.000/mês — detecção avançada, time de resposta (SRT), proteção de custos
    (não paga o scaling causado pelo ataque). Pra quem é alvo de verdade (fintechs, e-commerce grande).

> 💡 Divisão do trabalho: **Shield** cuida do volume bruto (camadas 3/4); **WAF** cuida do tráfego
> malicioso *bem formado* (camada 7: SQLi, XSS, bots, brute force).

---

## 6. Detecção: GuardDuty, Security Hub, Inspector

Defesa em profundidade inclui **assumir que algo vai passar** — e detectar rápido:

- **GuardDuty** — detecção de ameaças **por ML/inteligência**: analisa CloudTrail, VPC Flow Logs e
  DNS logs sem você instalar nada. Achados típicos: credencial usada de IP anômalo, instância
  minerando cripto, porta sendo escaneada, chamada de API incomum. **Um clique pra ativar**,
  **30 dias de trial grátis**; depois, cobra por volume analisado. Achados podem disparar
  EventBridge → resposta automática (amarra com o Módulo 12).
- **Security Hub** — o **agregador**: junta achados do GuardDuty, Inspector, Macie etc. num painel
  só e roda **checagens de conformidade** contra padrões (AWS Foundational Security Best Practices,
  CIS). Responde "quão bem configurada está minha conta?" com score e lista do que corrigir.
- **Inspector** — **scanner de vulnerabilidades** de workloads: examina EC2, imagens de container
  no ECR e funções Lambda procurando CVEs conhecidos e exposição de rede, continuamente.

> 💡 Mapa mental: **GuardDuty** = comportamento suspeito acontecendo (detecção de ameaça);
> **Inspector** = vulnerabilidade conhecida no software (antes do ataque); **Security Hub** = o
> painel que agrega tudo e mede a postura.

---

## 7. IAM avançado

O Módulo 02 deu identity policies, groups e roles. Três peças mais finas:

### 7.1 Permission boundaries

Um **boundary** é uma policy anexada a um usuário/role que define o **teto** de permissões: a
permissão efetiva é a **interseção** entre as identity policies e o boundary. Uso clássico:
**delegação segura** — você deixa devs criarem as próprias roles, mas com um boundary obrigatório
que impede escalar privilégio (a role criada nunca poderá mais do que o teto, mesmo que a policy
anexada diga `Action: "*"`).

### 7.2 Políticas de sessão (session policies)

Passadas **na hora de assumir uma role** (`AssumeRole`): restringem *aquela sessão* específica —
de novo, interseção com as policies da role. Útil pra emitir credenciais temporárias **mais
estreitas** que a role (ex.: um serviço que gera acesso só ao prefixo S3 de um cliente).

> 💡 Regra que resolve qualquer questão: identity policies **concedem**; boundaries e session
> policies **apenas limitam** (nunca concedem nada sozinhas). Efetivo = interseção de todas as
> camadas — e um **Deny explícito ganha de tudo, sempre**.

### 7.3 Condition keys úteis

Conditions tornam a permissão sensível ao **contexto**:

```json
{
  "Effect": "Deny",
  "Action": "*",
  "Resource": "*",
  "Condition": { "BoolIfExists": { "aws:MultiFactorAuthPresent": "false" } }
}
```

| Condition key | O que faz |
|---------------|-----------|
| `aws:SourceIp` | Restringe pelo IP de origem (ex.: só do escritório/VPN). |
| `aws:MultiFactorAuthPresent` | Verdadeiro se a sessão autenticou com MFA — base do "sem MFA, sem ação sensível". |
| `aws:SecureTransport` | Verdadeiro se a chamada veio por HTTPS (forçar TLS em bucket policies). |
| `aws:RequestedRegion` | Trava em quais regiões as ações valem (evitar recurso "perdido" em região exótica). |
| `aws:PrincipalTag/...` | Decide com base em tags do principal (ABAC — acesso baseado em atributos). |

> ⚠️ **Armadilha real do MFA-Deny:** use `BoolIfExists`, não `Bool`. A key
> `aws:MultiFactorAuthPresent` **não existe** em alguns contextos (ex.: access keys de longo
> prazo); com `Bool` a condição não casa e o Deny **não pega** justamente o caso mais perigoso.
> `BoolIfExists` trata "ausente" como violação. Testaremos isso na prática.

### 7.4 Menor privilégio na prática

Menor privilégio não é escrever a policy perfeita de primeira; é um **processo**:
1. Comece estreito (só o serviço/recurso necessário) e **alargue sob demanda** (o erro `AccessDenied`
   diz exatamente o que faltou).
2. Use o **IAM Access Analyzer**: além de achar recursos expostos externamente, ele **gera policies**
   a partir do uso real registrado no CloudTrail — a policy que a aplicação *de fato* precisa.
3. Revise permissões não usadas (last accessed) e remova.
4. Prefira **roles com credenciais temporárias** a access keys de longa duração, sempre.

---

## 8. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Defesa em profundidade | Camadas independentes de proteção; cada uma assume que a anterior falha. |
| KMS / CMK | Serviço de chaves; CMK = chave gerenciada por você (US$ 1/mês, controle total). |
| Key policy | Resource policy da chave — a raiz de quem administra e quem usa. |
| Envelope encryption | Data key criptografa o dado localmente; a CMK criptografa a data key. |
| Data key | Chave simétrica gerada pelo KMS; versão em claro usa-e-apaga, versão cifrada fica guardada. |
| Rotação | Troca periódica do material da chave (automática anual, opcional nas CMKs). |
| Secrets Manager | Segredos com rotação automática nativa; US$ 0,40/secret/mês. |
| Parameter Store / SecureString | Configuração hierárquica; SecureString = parâmetro criptografado via KMS, grátis. |
| WAF / Web ACL | Firewall camada 7; conjunto de regras (managed, próprias, rate-based) num recurso de borda. |
| Shield Standard/Advanced | Anti-DDoS: grátis/automático vs. ~US$ 3 mil/mês com SRT e proteção de custos. |
| GuardDuty | Detecção de ameaças por ML sobre CloudTrail/VPC Flow/DNS logs; trial de 30 dias. |
| Security Hub / Inspector | Agregador de postura + score de conformidade / scanner de CVEs em EC2, ECR e Lambda. |
| Permission boundary | Teto de permissões: efetivo = interseção com as identity policies. |
| Session policy | Restrição extra passada no AssumeRole, válida só pra sessão. |
| `aws:MultiFactorAuthPresent` | Condition que exige MFA (com `BoolIfExists` no Deny!). |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Explique o **envelope encryption** de ponta a ponta: por que a data key existe, o que se guarda
   junto do arquivo, e por que a CMK nunca sai do KMS?
2. Sua aplicação tem a senha do RDS (que deve girar sozinha) e 20 parâmetros de configuração.
   Onde vai cada coisa, e quanto custa?
3. Por que deletar uma chave KMS exige **agendamento de 7–30 dias**? O que se perderia num delete
   imediato errado?
4. Qual a diferença entre o que o **GuardDuty**, o **Inspector** e o **Security Hub** detectam/mostram?
5. Num Deny de ações sem MFA, por que `Bool` é um bug e `BoolIfExists` é o correto?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
