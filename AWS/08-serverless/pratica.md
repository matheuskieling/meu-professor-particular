# Módulo 08 — Serverless (Prática Guiada)

> Objetivo desta prática: criar suas **primeiras funções Lambda** (Console e CLI), colocar uma
> **HTTP API** na frente com o API Gateway e testar com `curl`, montar o clássico **trigger
> S3 → Lambda** e acompanhar tudo pelos **logs do CloudWatch**. No fim, teardown completo.
>
> **Abordagem:** Console primeiro (pra ver), CLI depois (pra fixar). Cada passo explica o *porquê*.
>
> ⏱️ Tempo estimado: 60–90 min. 💵 Custo: **US$ 0** — Lambda tem **1M invocações/mês sempre
> grátis** (+400k GB-s), HTTP API e S3 ficam nas cotas gratuitas pro volume desta aula.

---

## ⚠️ Antes de começar — leia isto

- Pré-requisitos: **Módulo 01** (conta + CLI configurada) e noções de S3 (**Módulo 06**).
- Tudo aqui cabe no Free Tier, **mas** o teardown continua obrigatório: log groups e buckets
  esquecidos viram bagunça (e bucket com arquivo grande cobra armazenamento).
- Região: **us-east-1** em tudo (lembra da armadilha do "recurso sumido").

---

## Parte A — Primeira Lambda pelo Console

### Passo 1 — Criar a função `m08-hello`
1. Console → **Lambda** → **Create function** → **Author from scratch**.
2. Function name: `m08-hello` · Runtime: **Python 3.13** (ou o 3.x mais novo) · Arquitetura: x86_64.
3. Em **Permissions**, deixe **Create a new role with basic Lambda permissions**.
4. **Create function**.

> **Por quê:** essa "basic role" é a **execution role** da teoria — ela só permite escrever logs
> no CloudWatch (`AWSLambdaBasicExecutionRole`). Least privilege desde o passo 1.

### Passo 2 — Editar o código e testar
1. Na aba **Code**, substitua o conteúdo por:

```python
import json
import os

def lambda_handler(event, context):
    nome = event.get("nome", "mundo")
    saudacao = os.environ.get("SAUDACAO", "Olá")
    print(f"Invocação recebida! event={json.dumps(event)}")  # vai pro CloudWatch
    return {
        "statusCode": 200,
        "body": json.dumps({"mensagem": f"{saudacao}, {nome}!"})
    }
```

2. Clique **Deploy** (sem deploy, a mudança não vale!).
3. Aba **Test** → crie um evento de teste com `{"nome": "SeuNome"}` → **Test**.
4. Veja o resultado: resposta, **duração**, **memória usada** e o trecho de log.

> 🎯 Repare no relatório da execução (`REPORT ... Duration ... Billed Duration ... Max Memory
> Used`): é exatamente o **GB-segundo** da teoria sendo medido.

### Passo 3 — Variáveis de ambiente e configuração
1. Aba **Configuration → Environment variables** → **Edit** → adicione `SAUDACAO` = `E aí`.
2. Teste de novo: a resposta muda **sem tocar no código**.
3. Ainda em Configuration → **General configuration**: veja **Memory (128 MB)** e **Timeout
   (3 s)** — os knobs da teoria. Não precisa mudar.

---

## Parte B — Invocar e observar pela CLI

### Passo 4 — `aws lambda invoke`
```bash
aws lambda invoke \
  --function-name m08-hello \
  --cli-binary-format raw-in-base64-out \
  --payload '{"nome": "CLI"}' \
  /tmp/resposta.json

cat /tmp/resposta.json
```
> O `invoke` é **síncrono** por padrão: você recebeu o retorno do handler. O
> `--cli-binary-format raw-in-base64-out` é necessário na CLI v2 pra mandar JSON puro.

### Passo 5 — Ver os logs (`aws logs tail`)
```bash
aws logs tail /aws/lambda/m08-hello --since 10m
```
> Todo `print` da função vira log no grupo **`/aws/lambda/<nome-da-função>`** — cortesia da
> execution role. Guarde esse comando: é seu melhor amigo pra depurar Lambda. Com `--follow`
> ele fica acompanhando em tempo real.

---

## Parte C — HTTP API na frente da Lambda (API Gateway)

### Passo 6 — Criar a HTTP API
1. Console → **API Gateway** → **Create API** → em **HTTP API**, clique **Build**.
2. **Add integration** → **Lambda** → selecione `m08-hello`. API name: `m08-api` → **Next**.
3. Em **Routes**: método **GET**, path `/ola` (apontando pra integração da Lambda) → **Next**.
4. Stage: deixe **`$default`** com **auto-deploy** → **Next** → **Create**.

> **Por quê HTTP API e não REST API:** é o sabor moderno — mais barato (~US$ 1/milhão) e mais
> rápido. O auto-deploy do stage `$default` publica cada mudança na hora, ideal pra estudo.

### Passo 7 — Testar com curl
1. Copie a **Invoke URL** da API (algo como `https://abc123.execute-api.us-east-1.amazonaws.com`).
2. No terminal:

```bash
curl https://SEU_ID.execute-api.us-east-1.amazonaws.com/ola
```

Você vai receber o JSON da função. 🎉 **Sua primeira API serverless está no ar** — com TLS,
escalando sozinha, custando zero parada.

> 💡 Repare: o `event` que chega do API Gateway é **diferente** do seu teste manual (tem
> `requestContext`, `headers`, `queryStringParameters`...). Rode `aws logs tail /aws/lambda/m08-hello --since 5m`
> e veja o formato no `print` — cada event source tem seu formato de evento.

---

## Parte D — Trigger S3 → Lambda (event-driven de verdade)

### Passo 8 — Criar a função processadora e o bucket
1. Crie uma segunda função no Console: `m08-processa-s3`, Python 3.13, nova role básica, código:

```python
def lambda_handler(event, context):
    for registro in event["Records"]:
        bucket = registro["s3"]["bucket"]["name"]
        chave = registro["s3"]["object"]["key"]
        tamanho = registro["s3"]["object"].get("size", 0)
        print(f"Novo objeto: s3://{bucket}/{chave} ({tamanho} bytes)")
    return {"processados": len(event["Records"])}
```

2. **Deploy**.
3. Crie o bucket (o nome precisa ser único no mundo — troque o sufixo):

```bash
aws s3 mb s3://m08-eventos-SEUNOME-1234
```

### Passo 9 — Conectar o trigger
1. Na função `m08-processa-s3` → **Add trigger** → **S3**.
2. Bucket: `m08-eventos-SEUNOME-1234` · Event types: **All object create events** → confirme o
   aviso (recursivo) → **Add**.

> Por baixo dos panos, o Console fez duas coisas: configurou a **notificação de evento** no
> bucket e deu **permissão ao S3 pra invocar** a função (resource-based policy). É invocação
> **assíncrona**: o S3 dispara e não espera resposta.

### Passo 10 — Disparar e ver o log
```bash
echo "teste de evento" > /tmp/arquivo-teste.txt
aws s3 cp /tmp/arquivo-teste.txt s3://m08-eventos-SEUNOME-1234/

aws logs tail /aws/lambda/m08-processa-s3 --since 5m
```
Você deve ver o log `Novo objeto: s3://.../arquivo-teste.txt`. **Isso é arquitetura event-driven:**
o S3 emitiu, a Lambda reagiu, ninguém orquestrou.

---

## Parte E — 🔥 Teardown (obrigatório)

Nada aqui cobra parado (dentro do Free Tier), mas o ritual é sagrado. Ordem: API → funções →
bucket → log groups.

```bash
# 1. Apagar a API (pegue o ApiId listando)
aws apigatewayv2 get-apis --query "Items[].{Nome:Name,Id:ApiId}" --output table
aws apigatewayv2 delete-api --api-id SEU_API_ID

# 2. Apagar as funções
aws lambda delete-function --function-name m08-hello
aws lambda delete-function --function-name m08-processa-s3

# 3. Esvaziar e apagar o bucket
aws s3 rb s3://m08-eventos-SEUNOME-1234 --force

# 4. Apagar os log groups (eles NÃO somem com a função!)
aws logs delete-log-group --log-group-name /aws/lambda/m08-hello
aws logs delete-log-group --log-group-name /aws/lambda/m08-processa-s3
```

> ⚠️ **Armadilha:** deletar a função **não** deleta o log group nem a IAM role. Os logs você
> apagou acima; as roles (`m08-hello-role-...`) não custam nada, mas se quiser zerar de vez,
> apague no Console em **IAM → Roles** (buscando por `m08-`).

Confira no Console que Lambda, API Gateway e S3 estão limpos.

---

## ✅ Checklist de conclusão do módulo

- [ ] Criou `m08-hello` no Console e testou com evento de teste.
- [ ] Entendeu o REPORT (duração, memória) e mexeu em variável de ambiente.
- [ ] Invocou pela CLI (`aws lambda invoke`) e leu a resposta.
- [ ] Viu os logs com `aws logs tail /aws/lambda/...`.
- [ ] Criou uma **HTTP API** com rota `GET /ola` e testou com `curl`.
- [ ] Montou o trigger **S3 → Lambda** e viu o evento chegar no log.
- [ ] Fez o **teardown** completo (API, funções, bucket, log groups).

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-08/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-08/`) e para o **Módulo 09 — Containers**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 8" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
