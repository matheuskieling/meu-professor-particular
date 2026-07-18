# Módulo 14 — DNS & Entrega de Conteúdo (Prática Guiada)

> Objetivo desta prática: colocar um **CloudFront na frente do seu bucket S3** (o do módulo 06),
> com o bucket **100% privado via OAC**, ver o **cache funcionando** (Hit/Miss) e fazer uma
> **invalidação**. Depois, criar uma **hosted zone privada** e testá-la de dentro da VPC.
> Há uma seção **opcional** para quem tiver (ou quiser comprar) um domínio próprio.
>
> **Abordagem:** Console web primeiro (pra ver), CLI depois (pra fixar). Cada passo explica o *porquê*.
>
> ⏱️ Tempo estimado: 60–90 min. 💵 Custo: **~US$ 0** no caminho principal (CloudFront tem free tier
> generoso; a hosted zone **privada** custa US$ 0,50/mês, mas vamos apagá-la no teardown — fração de
> centavo por algumas horas). Comprar domínio (opcional) custa a partir de ~US$ 14/ano.

---

## ⚠️ Antes de começar — leia isto

- **Pré-requisito:** o bucket S3 do **módulo 06** com alguns arquivos (um `index.html` e uma imagem
  bastam). Se apagou, crie um bucket novo e suba um `index.html` simples.
- O **caminho principal NÃO usa domínio próprio** (comprar domínio é pago e é seu pra sempre — não
  é "teardownável"). Vamos usar o domínio `*.cloudfront.net` da distribuição, que é grátis.
- **Hosted zone (pública ou privada) custa US$ 0,50/mês por zona.** Criaremos **uma privada**, de
  teste, e **apagaremos no teardown** (a cobrança é proporcional — centavos).
- Distribuições CloudFront **demoram alguns minutos** pra criar/atualizar (propagação pras edges).
  É normal. Aproveite as esperas pra revisar a teoria.

---

## Parte A — CloudFront + S3 privado com OAC (Console)

### Passo 1 — Garantir que o bucket está PRIVADO
1. Console → **S3** → seu bucket do módulo 06.
2. Aba **Permissions** → confirme **Block all public access = On**. Se você deixou o bucket público
   ou com website hosting no módulo 06, **reative o bloqueio total** agora.
3. Se havia uma bucket policy de acesso público, **delete-a**.

> **Por quê:** o ponto da prática é provar que dá pra servir conteúdo de um bucket **fechado**.
> O único leitor autorizado será o CloudFront, via OAC.

### Passo 2 — Criar a distribuição CloudFront
1. Console → **CloudFront** → **Create distribution**.
2. **Origin domain:** selecione seu bucket na lista (use a opção do bucket S3 direto, **não** o
   endpoint de website — OAC não funciona com website endpoint).
3. **Origin access:** selecione **Origin access control settings (recommended)** →
   **Create new OAC** → aceite o padrão (Sign requests) → **Create**.
4. Vai aparecer um aviso: *"You must update the S3 bucket policy"* — deixe marcado para o
   CloudFront **copiar/aplicar a policy** ou copie-a você mesmo (veremos no passo 3).
5. **Viewer protocol policy:** `Redirect HTTP to HTTPS`.
6. **Cache policy:** `CachingOptimized` (a padrão pra S3).
7. **WAF:** `Do not enable` (evitar custo; WAF foi o módulo 13).
8. **Default root object:** `index.html`.
9. **Create distribution**. Status ficará **Deploying** por ~5–10 min.

### Passo 3 — Conferir a bucket policy do OAC
1. Volte ao **S3** → bucket → **Permissions** → **Bucket policy**. Deve haver algo assim:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowCloudFrontServicePrincipal",
    "Effect": "Allow",
    "Principal": { "Service": "cloudfront.amazonaws.com" },
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::SEU-BUCKET/*",
    "Condition": {
      "StringEquals": {
        "AWS:SourceArn": "arn:aws:cloudfront::SUA-CONTA:distribution/SUA-DISTRIBUICAO"
      }
    }
  }]
}
```

> **Leia a policy em voz alta:** "permita que o **serviço CloudFront** leia objetos, **mas só**
> quando a requisição vier da **minha** distribuição". É o least privilege do módulo 02 aplicado:
> nem público, nem aberto pra todo o CloudFront do mundo — só a sua distribuição.

### Passo 4 — Testar: o bucket fechado, a distribuição aberta
1. Copie o **Distribution domain name** (ex.: `d1a2b3c4.cloudfront.net`).
2. Acesse `https://dXXXX.cloudfront.net/` no navegador → deve servir seu `index.html`. 🎉
3. Agora tente acessar o objeto **direto no S3**:
   `https://SEU-BUCKET.s3.amazonaws.com/index.html` → deve dar **403 Access Denied**.

> Esse contraste é a foto do módulo: **origem trancada, entrega só pela CDN**.

### Passo 5 — Ver o cache trabalhando (Hit/Miss)
No terminal:

```bash
curl -sI https://dXXXX.cloudfront.net/index.html | grep -i x-cache
```

- 1ª vez: `X-Cache: Miss from cloudfront` (a edge foi buscar na origem).
- Rode de novo: `X-Cache: Hit from cloudfront` (veio do cache da edge!).

> 💡 Repare também no header `Age` (segundos desde que a edge cacheou) e `Via` (qual edge atendeu).
> Se você pedir de outra rede/local, pode cair em outra edge e ver `Miss` de novo — cada edge tem o
> **seu** cache.

### Passo 6 — Invalidação (Console)
1. Edite seu `index.html` local (mude um texto) e suba de novo pro S3 (Console ou
   `aws s3 cp index.html s3://SEU-BUCKET/`).
2. Recarregue `https://dXXXX.cloudfront.net/` → **ainda a versão antiga** (cache!).
3. CloudFront → sua distribuição → aba **Invalidations** → **Create invalidation** → caminho `/*`.
4. Aguarde concluir (~1 min) e recarregue → **versão nova**.

> **Custo:** as primeiras **1.000 invalidações/mês são grátis** — e `/*` conta como 1. Mas lembre da
> boa prática: em produção, versione os assets e invalide raramente.

---

## Parte B — O mesmo, via CLI (fixar)

Nenhum comando abaixo cria recurso novo — só inspeciona e opera o que você já criou.

### Listar distribuições e achar a sua
```bash
aws cloudfront list-distributions \
  --query "DistributionList.Items[].{Id:Id,Domain:DomainName,Status:Status}" --output table
```

### Ver a configuração da origem (repare no OAC)
```bash
aws cloudfront get-distribution-config --id SUA-DISTRIBUICAO \
  --query "DistributionConfig.Origins.Items[0].{Origem:DomainName,OAC:OriginAccessControlId}"
```

### Criar uma invalidação pela CLI
```bash
aws cloudfront create-invalidation --distribution-id SUA-DISTRIBUICAO --paths "/index.html"
aws cloudfront list-invalidations --distribution-id SUA-DISTRIBUICAO --output table
```

> `--paths "/index.html"` invalida só um caminho — mais cirúrgico que `/*`. Na CLI fica óbvio que
> invalidação é um **recurso assíncrono**: você cria e acompanha o status (`InProgress` → `Completed`).

---

## Parte C — Hosted zone privada + registros na VPC (Console + CLI)

Sem domínio próprio dá pra praticar Route 53 do mesmo jeito — com uma zona **privada**, que só
existe dentro da sua VPC (e aceita **qualquer nome**, já que não vai pra internet).

> 💵 **Custo:** US$ 0,50/mês por zona, cobrado proporcionalmente. Algumas horas = < US$ 0,01.
> Mesmo assim: **teardown no final.**

### Passo 7 — Criar a hosted zone privada
1. Console → **Route 53** → **Hosted zones** → **Create hosted zone**.
2. **Domain name:** `curso.interno` (qualquer nome — não precisa existir na internet).
3. **Type:** **Private hosted zone**.
4. Associe à sua **VPC** do módulo 03 (região `us-east-1`).
5. **Create**.

### Passo 8 — Criar registros
1. Dentro da zona → **Create record**:
   - Nome: `app.curso.interno` · Tipo **A** · Valor: `10.0.1.50` (um IP qualquer da sua subnet) · TTL 300.
2. Crie um segundo: nome `site.curso.interno` · tipo **CNAME** · valor: `dXXXX.cloudfront.net`.

Pela CLI, o segundo registro seria:
```bash
aws route53 list-hosted-zones --query "HostedZones[].{Id:Id,Nome:Name,Privada:Config.PrivateZone}" --output table

aws route53 change-resource-record-sets --hosted-zone-id SUA-ZONA --change-batch '{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "site.curso.interno",
      "Type": "CNAME",
      "TTL": 300,
      "ResourceRecords": [{"Value": "dXXXX.cloudfront.net"}]
    }
  }]
}'
```

### Passo 9 — Testar de DENTRO da VPC
Resolução de zona privada **só funciona de dentro da VPC associada**. Se você ainda tem uma
instância EC2 dos módulos anteriores (ou suba uma `t3.micro` rapidinho — free tier — e **termine
depois**), conecte nela (SSM/SSH) e rode:

```bash
dig app.curso.interno +short      # deve responder 10.0.1.50
dig site.curso.interno +short     # deve responder o domínio do CloudFront (e o IP da edge)
```

Da sua máquina local, `dig app.curso.interno` **falha** — e é esse o ponto: a zona é **privada**.

> 💡 Quem responde essas consultas é o **resolver da VPC** (o famoso IP `.2` da faixa da VPC, ex.:
> `10.0.0.2`) — por isso funciona sem internet e sem NS público.

---

## Parte D — 🎁 OPCIONAL: com domínio próprio (custa dinheiro de verdade)

> ⚠️ **Esta seção inteira é OPCIONAL e paga.** Registrar domínio custa a partir de ~US$ 14/ano
> (`.com` no Route 53) e **não tem teardown** — é uma assinatura anual. Hosted zone **pública**:
> US$ 0,50/mês enquanto existir. Só siga se você **quer** um domínio seu. O restante do curso
> **não depende** disto.

1. **Registrar:** Route 53 → **Registered domains** → **Register domain** → escolha e pague. A AWS
   cria automaticamente a **hosted zone pública** com os NS corretos. (Alternativa BR: registre no
   Registro.br e aponte os **name servers** pra uma hosted zone pública que você criar.)
2. **Certificado:** Console → **Certificate Manager (ACM)** — **⚠️ mude a região para
   `us-east-1`!** → **Request certificate** → `meusite.com` e `www.meusite.com` → validação **DNS**
   → botão **Create records in Route 53** → aguarde `Issued` (minutos).
3. **CloudFront:** distribuição → **Edit** → **Alternate domain names (CNAMEs):** `meusite.com`,
   `www.meusite.com` → **Custom SSL certificate:** selecione o do ACM → salve.
4. **DNS:** na hosted zone, crie um registro **A — Alias** para `meusite.com` → **Alias to
   CloudFront distribution** → selecione a sua. Repita pra `www`.
5. Teste `https://meusite.com` → seu site, com **seu domínio e cadeado verde**, servido de um bucket
   privado. Este é o combo de produção.

---

## 🔥 Parte E — Teardown (obrigatório)

A ordem importa. Distribuição CloudFront **não pode ser deletada ligada** — primeiro desabilita,
espera propagar, depois deleta:

1. **CloudFront:** distribuição → **Disable** → aguarde o status sair de "Deploying" (**5–15 min**;
   é a propagação do "desligado" pra todas as edges do mundo — paciência, é normal).
2. Com o status `Disabled`, selecione → **Delete**.
3. **Route 53:** na zona `curso.interno`, **delete os registros** que você criou (A e CNAME) —
   os registros NS/SOA não precisam (somem com a zona) → **Delete hosted zone**.
4. Se subiu uma **EC2 de teste** na Parte C → **Terminate**.
5. Se fez a parte opcional e **não quer manter**: remova alternate domain names da distribuição e
   delete o certificado ACM (o domínio registrado é seu por 1 ano de qualquer forma; desative o
   **auto-renew** se não quiser renovar).
6. O **bucket S3 fica** (é o do módulo 06 e custa centavos por GB) — mas confira que voltou a ser
   **privado e sem policy** do CloudFront (pode remover a policy do OAC, já que a distribuição morreu).

Confira em **Billing → Bills** nos próximos dias: deve estar em ~US$ 0.

---

## ✅ Checklist de conclusão do módulo

- [ ] Bucket S3 confirmado **privado** (Block Public Access ligado).
- [ ] Distribuição CloudFront criada com **OAC** apontando pro bucket.
- [ ] Bucket policy do OAC conferida e entendida (principal + SourceArn).
- [ ] Site servido via `https://dXXXX.cloudfront.net`; acesso direto ao S3 dá **403**.
- [ ] `X-Cache: Miss` → `Hit` observado com `curl -I`.
- [ ] Objeto atualizado + **invalidação** feita (Console e CLI).
- [ ] Hosted zone **privada** criada com registros A e CNAME.
- [ ] Resolução testada **de dentro da VPC** (e falhando fora dela).
- [ ] (Opcional) Domínio próprio + ACM em `us-east-1` + alias no apex.
- [ ] 🔥 **Teardown completo**: distribuição desabilitada e deletada, hosted zone apagada.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-14/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-14/`) e para o **Módulo 15 — Arquitetura & Well-Architected**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 14" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
