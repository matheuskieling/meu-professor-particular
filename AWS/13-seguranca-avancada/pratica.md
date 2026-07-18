# Módulo 13 — Segurança Avançada (Prática Guiada)

> Objetivo desta prática: usar as peças de segurança de verdade — criar uma **chave KMS** e
> criptografar/descriptografar arquivos (vendo o **envelope encryption** por dentro, com data
> keys), guardar segredos no **Secrets Manager** e no **Parameter Store**, ativar o **GuardDuty**
> e escrever uma **policy com condition de MFA** (testando a pegadinha do `BoolIfExists`).
>
> **Abordagem:** Console primeiro (pra ver), CLI depois (pra fixar).
>
> ⏱️ Tempo estimado: 60–90 min.
> 💵 Custo: **quase zero, mas NÃO zero — leia os avisos**:
> - **KMS:** chave customer managed custa **US$ 1/mês (pró-rata)**. Criaremos **1** e **agendaremos
>   a deleção (7 dias)** no teardown → centavos no total.
> - **Secrets Manager:** **US$ 0,40/secret/mês (pró-rata)**. Criaremos **1** e apagaremos com
>   `--force-delete-without-recovery` no teardown.
> - **GuardDuty:** **30 dias de trial grátis** — ativaremos e **desativaremos no teardown**.
> - Parameter Store (standard) é grátis.

---

## ⚠️ Antes de começar — leia isto

- O teardown deste módulo **não é opcional nem simbólico**: KMS e Secrets Manager cobram por
  existência. Reserve 5 minutos no final.
- Os "segredos" desta prática são **de mentira** (inventados pra aula). Jamais coloque segredos
  reais em exemplos, chats ou repositórios.
- Trabalhe em `~/lab-seguranca/` (fora do repo) e na região **us-east-1**.

```bash
mkdir -p ~/lab-seguranca && cd ~/lab-seguranca
```

---

## Parte A — KMS: criar a chave (Console)

### Passo 1 — Criar a customer managed key
1. Console → **KMS** (Key Management Service) → **Customer managed keys** → **Create key**.
2. Tipo: **Symmetric**, uso: **Encrypt and decrypt** → Next.
3. Alias: `lab-seguranca` → Next.
4. **Key administrators:** selecione seu usuário → Next.
5. **Key users:** selecione seu usuário de novo → Next.
   > Repare na separação: **administrar** a chave ≠ **usar** a chave. Aqui você é os dois; numa
   > empresa, seriam grupos diferentes.
6. Revise a **key policy** gerada (leia! veja os statements de admin e de uso) → **Finish**.

7. Abra a chave criada e explore as abas: **Key policy**, **Key rotation** (habilite a rotação
   automática anual — é grátis e boa prática).

### Passo 2 — Criptografar/descriptografar direto na API (CLI)

O jeito "simples" (só até 4 KB — guarde isso):

```bash
echo "dado sensivel do modulo 13" > segredo.txt

# criptografar
aws kms encrypt \
  --key-id alias/lab-seguranca \
  --plaintext fileb://segredo.txt \
  --query CiphertextBlob --output text | base64 -d > segredo.txt.cifrado

# olhar o resultado (ilegível)
file segredo.txt.cifrado

# descriptografar (repare: nem precisa dizer a chave — está nos metadados do blob)
aws kms decrypt \
  --ciphertext-blob fileb://segredo.txt.cifrado \
  --query Plaintext --output text | base64 -d
```

✅ Deve imprimir o texto original. **Cada uma dessas chamadas passou pelo IAM e está no CloudTrail**
(quer conferir? Event history → `Decrypt`). Criptografia virou controle de acesso auditável.

---

## Parte B — Envelope encryption com data keys (CLI)

Agora o padrão de verdade, pra dados de qualquer tamanho.

### Passo 3 — Gerar a data key
```bash
aws kms generate-data-key \
  --key-id alias/lab-seguranca \
  --key-spec AES_256 \
  --output json > datakey.json

cat datakey.json
```
> Observe o retorno: **`Plaintext`** (a data key em claro, base64) e **`CiphertextBlob`** (a mesma
> data key criptografada pela sua CMK). Duas versões da mesma chave — o coração do envelope.

Separe as duas:
```bash
python3 -c "import json;d=json.load(open('datakey.json'));open('dk.b64','w').write(d['Plaintext']);open('dk-cifrada.bin','wb').write(__import__('base64').b64decode(d['CiphertextBlob']))"
base64 -d dk.b64 > dk.bin
```

### Passo 4 — Criptografar um arquivo GRANDE localmente
```bash
# um arquivo de 50 MB — impossível pro kms encrypt (limite 4 KB)
dd if=/dev/urandom of=arquivo-grande.bin bs=1M count=50

# criptografa LOCALMENTE com a data key (openssl, AES-256)
openssl enc -aes-256-cbc -pbkdf2 -in arquivo-grande.bin -out arquivo-grande.cifrado \
  -pass file:./dk.bin

# o ritual do envelope: apagar a data key em claro; guardar SÓ a versão cifrada
rm -f dk.bin dk.b64 datakey.json
ls -la    # sobraram: arquivo cifrado + dk-cifrada.bin (o envelope)
```

### Passo 5 — Descriptografar: abrir o envelope
```bash
# 1. pedir ao KMS pra abrir o envelope (decrypt da data key)
aws kms decrypt \
  --ciphertext-blob fileb://dk-cifrada.bin \
  --query Plaintext --output text | base64 -d > dk.bin

# 2. descriptografar o arquivo localmente
openssl enc -d -aes-256-cbc -pbkdf2 -in arquivo-grande.cifrado -out arquivo-recuperado.bin \
  -pass file:./dk.bin

# 3. conferir que é idêntico ao original
sha256sum arquivo-grande.bin arquivo-recuperado.bin

# 4. apagar a data key em claro de novo
rm -f dk.bin
```

> 🎯 Você acabou de fazer **na mão** o que S3 (SSE-KMS), EBS e RDS fazem por baixo em cada objeto,
> volume e página de banco. E percebeu o superpoder: se a permissão de `kms:Decrypt` na CMK for
> revogada, o passo 1 falha — e **todos** os arquivos lacrados por ela viram tijolos ilegíveis.
> Revogação centralizada de milhões de objetos com uma mudança de policy.

---

## Parte C — Secrets Manager e Parameter Store

### Passo 6 — Guardar e ler um secret (Secrets Manager)

> 💵 Lembrete: US$ 0,40/secret/mês, pró-rata. Este secret morre no teardown.

```bash
aws secretsmanager create-secret \
  --name lab/db-credenciais \
  --description "Secret de exemplo do modulo 13 (fake)" \
  --secret-string '{"username":"app","password":"S3nh4-Fake-Do-Lab"}'

# como uma aplicação leria em runtime:
aws secretsmanager get-secret-value \
  --secret-id lab/db-credenciais \
  --query SecretString --output text
```

No Console (**Secrets Manager**), abra o secret e explore a aba **Rotation**: é aqui que se
configura a **rotação automática** (uma Lambda que troca a senha no banco e no secret — integração
pronta pra RDS). Só olhe, não habilite (exigiria um RDS vivo).

### Passo 7 — Parâmetro SecureString (Parameter Store)

```bash
aws ssm put-parameter \
  --name /lab/config/api-token \
  --type SecureString \
  --value "token-fake-do-lab-13"

# ler SEM descriptografar (vem o blob)
aws ssm get-parameter --name /lab/config/api-token

# ler descriptografando (exige permissão no KMS também!)
aws ssm get-parameter --name /lab/config/api-token --with-decryption \
  --query Parameter.Value --output text
```

> 💡 Sem `--key-id`, o SecureString usa a chave gerenciada `aws/ssm` (grátis). Compare os dois
> mundos que você acabou de tocar: rotação automática nativa (Secrets, US$ 0,40/mês) vs. grátis e
> manual (SecureString). Agora a tabela da teoria é experiência sua.

---

## Parte D — GuardDuty (Console)

> 💵 **Trial de 30 dias grátis.** Vamos ativar, conhecer, e **desativar no teardown** (se esquecer
> ligado após o trial, cobra por volume de logs analisados).

### Passo 8 — Ativar e explorar
1. Console → **GuardDuty** → **Get started** → **Enable GuardDuty**.
2. Pronto — é isso mesmo, um clique: ele já está analisando CloudTrail, VPC Flow Logs e DNS logs.
3. Explore **Findings** (provavelmente vazio — bom sinal). Em **Settings**, ache **Generate sample
   findings** e clique: dezenas de achados de exemplo aparecem.
4. Abra um sample finding (ex.: `Backdoor:EC2/...` ou `UnauthorizedAccess:IAMUser/...`): veja
   severidade, recurso afetado, e a explicação do que teria acontecido.

> 🎯 Conecte com o Módulo 12: findings do GuardDuty viram eventos no **EventBridge** — dá pra
> notificar por SNS ou disparar uma Lambda de resposta automática (isolar instância, revogar chave).

---

## Parte E — Policy com condition de MFA

### Passo 9 — Escrever e entender a policy

Crie `~/lab-seguranca/deny-sem-mfa.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "NegaTudoSemMFA",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "BoolIfExists": { "aws:MultiFactorAuthPresent": "false" }
      }
    }
  ]
}
```

**Leia com atenção antes de criar:** é um **Deny** de tudo **quando não há MFA** na sessão.
E o detalhe que separa júnior de sênior: **`BoolIfExists`** — porque em sessões de access key de
longo prazo a key `aws:MultiFactorAuthPresent` **nem existe**; com `Bool` simples, a condição não
casaria e o Deny deixaria passar **exatamente o caso mais perigoso**.

### Passo 10 — Criar como managed policy (sem anexar a você!)

> ⚠️ **NÃO anexe esta policy ao seu próprio usuário agora**: sua CLI usa access keys **sem MFA** —
> você trancaria a si mesmo pra fora (todo comando viraria AccessDenied). Vamos criá-la e validá-la;
> anexar seria o passo final num usuário de terceiros/grupo, com sessões MFA configuradas.

```bash
aws iam create-policy \
  --policy-name lab-deny-sem-mfa \
  --policy-document file://deny-sem-mfa.json

# conferir
aws iam list-policies --scope Local \
  --query "Policies[].PolicyName" --output table
```

(Se quiser *sentir* o efeito com segurança: crie um usuário de teste descartável, anexe a policy
nele, gere access keys e veja qualquer comando falhar com `AccessDenied` — depois delete o usuário.)

---

## Parte F — 🔥 Teardown (OBRIGATÓRIO — aqui tem custo real)

```bash
# 1. Secret — deleção forçada, sem janela de recuperação (senão cobraria durante a espera)
aws secretsmanager delete-secret \
  --secret-id lab/db-credenciais \
  --force-delete-without-recovery

# 2. Parâmetro
aws ssm delete-parameter --name /lab/config/api-token

# 3. Chave KMS — agendar deleção com o MÍNIMO de espera (7 dias)
KEY_ID=$(aws kms describe-key --key-id alias/lab-seguranca --query KeyMetadata.KeyId --output text)
aws kms schedule-key-deletion --key-id "$KEY_ID" --pending-window-in-days 7
aws kms delete-alias --alias-name alias/lab-seguranca
# a chave fica PendingDeletion (inutilizável, sem cobrança de uso) e some em 7 dias

# 4. GuardDuty — desativar (Console: Settings → Disable GuardDuty)
#    ou via CLI:
DETECTOR=$(aws guardduty list-detectors --query "DetectorIds[0]" --output text)
aws guardduty delete-detector --detector-id "$DETECTOR"

# 5. Policy do IAM (policies não custam, mas higiene é higiene)
POLICY_ARN=$(aws iam list-policies --scope Local \
  --query "Policies[?PolicyName=='lab-deny-sem-mfa'].Arn" --output text)
aws iam delete-policy --policy-arn "$POLICY_ARN"

# 6. Arquivos locais do lab
cd ~ && rm -rf ~/lab-seguranca

# 7. Conferir
aws kms describe-key --key-id "$KEY_ID" --query KeyMetadata.KeyState   # PendingDeletion
aws secretsmanager list-secrets --query "SecretList[].Name" --output table
aws guardduty list-detectors
```

> 💡 Por que a chave KMS não morre na hora? Proteção contra desastre: apagar uma chave torna
> **irrecuperável** tudo que ela criptografou. Os 7–30 dias são a chance de arrependimento
> (`cancel-key-deletion`). Durante a espera, a chave não funciona — e a cobrança do US$ 1/mês para.

---

## ✅ Checklist de conclusão do módulo

- [ ] Criou a CMK `lab-seguranca` com admin/usuários separados e leu a **key policy**.
- [ ] Habilitou a rotação automática anual da chave.
- [ ] Criptografou e descriptografou via `kms encrypt/decrypt` (e viu no CloudTrail).
- [ ] Gerou uma **data key** e identificou as duas versões (Plaintext × CiphertextBlob).
- [ ] Fez **envelope encryption** completo num arquivo de 50 MB (cifrar local → apagar chave clara
      → guardar envelope → reabrir via `kms decrypt` → sha256 idêntico).
- [ ] Criou e leu um secret no **Secrets Manager**; espiou a aba Rotation.
- [ ] Criou e leu (com `--with-decryption`) um **SecureString** no Parameter Store.
- [ ] Ativou o **GuardDuty** e explorou sample findings.
- [ ] Escreveu a policy **Deny sem MFA** e explicou por que `BoolIfExists`.
- [ ] **Teardown completo:** secret force-deleted, parâmetro apagado, chave em `PendingDeletion`
      (7 dias), GuardDuty desativado, policy removida.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-13/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-13/`) e para o **Módulo 14 — DNS & Entrega de conteúdo**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 13" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
