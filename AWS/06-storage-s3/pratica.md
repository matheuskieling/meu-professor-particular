# Módulo 06 — Storage: S3 & cia (Prática Guiada)

> Objetivo desta prática: operar o S3 de verdade — criar bucket, subir/baixar objetos (Console e
> CLI), ligar **versionamento** e ver versões acumulando, criar uma **lifecycle rule**, gerar uma
> **presigned URL** e hospedar um **site estático** acessível pelo navegador. Teardown no fim.
>
> **Abordagem:** Console web primeiro (pra ver), CLI depois (pra fixar). Cada passo explica o *porquê*.
>
> ⏱️ Tempo estimado: 60–75 min. 💵 Custo: **≈ US$ 0** — o Free Tier dá 5 GB de S3, e vamos usar
> alguns KB. Sem pressa aqui: nada cobra por hora.

---

## ⚠️ Antes de começar

- Região: **`us-east-1`**, como sempre.
- Nome de bucket é **globalmente único**. Vamos usar o padrão `curso-aws-<seunome>-<numero>`
  (ex.: `curso-aws-matheus-4821`). Anote o seu — vou chamá-lo de `SEU-BUCKET` nos comandos.
- Único ponto de atenção de segurança: na parte do **site estático** vamos deixar UM bucket
  público **de propósito**. No teardown ele morre.

---

## Parte A — Criar o bucket e subir objetos (Console)

### Passo 1 — Criar o bucket
1. Console → **S3** → **Create bucket**.
2. Nome: `curso-aws-<seunome>-<numero>` · Região: `us-east-1`.
3. Repare nos padrões seguros: **Object Ownership = ACLs disabled** e **Block Public Access =
   tudo ligado**. Deixe assim.
4. Crie. (Se o nome já existir no mundo, troque o número — é a unicidade global na prática.)

### Passo 2 — Subir e explorar objetos
1. Crie um arquivo local `ola.txt` com qualquer texto.
2. No bucket → **Upload** → selecione o arquivo → Upload.
3. Clique no objeto: veja **key**, tamanho, **classe (Standard)**, e a criptografia **SSE-S3
   já aplicada automaticamente** (padrão desde 2023).
4. Tente abrir a **Object URL** no navegador: **Access Denied**. 🎉 Isso é o correto — bucket
   privado por padrão. (Baixar pelo botão **Download** funciona, porque usa suas credenciais.)
5. Ainda no Console, use **Create folder** (`docs/`) e suba outro arquivo dentro. Lembre: a
   "pasta" é ilusão — o objeto só tem a chave `docs/arquivo.txt`.

---

## Parte B — CLI: cp, sync, ls (o dia a dia de verdade)

```bash
BUCKET=SEU-BUCKET   # troque pelo seu nome de bucket

# Listar buckets e conteúdo
aws s3 ls
aws s3 ls s3://$BUCKET --recursive

# Subir e baixar um arquivo
echo "primeira versao" > relatorio.txt
aws s3 cp relatorio.txt s3://$BUCKET/docs/relatorio.txt
aws s3 cp s3://$BUCKET/docs/relatorio.txt ./relatorio-baixado.txt

# Sincronizar um diretório inteiro (só envia o que mudou!)
mkdir -p projeto && echo "a" > projeto/a.txt && echo "b" > projeto/b.txt
aws s3 sync projeto/ s3://$BUCKET/projeto/
aws s3 sync projeto/ s3://$BUCKET/projeto/   # rode de novo: nada a fazer — só envia diffs
```

> **Por quê:** `aws s3 cp` é o upload/download unitário; `aws s3 sync` é o cavalo de batalha de
> backups e deploys — compara origem e destino e transfere só as diferenças.

---

## Parte C — Versionamento (Console + CLI)

### Passo 3 — Habilitar e ver versões
1. Console → bucket → **Properties** → **Bucket Versioning** → **Enable**.
2. Agora sobrescreva o objeto pela CLI:

```bash
echo "segunda versao" > relatorio.txt
aws s3 cp relatorio.txt s3://$BUCKET/docs/relatorio.txt
echo "terceira versao" > relatorio.txt
aws s3 cp relatorio.txt s3://$BUCKET/docs/relatorio.txt

# Ver as versões acumuladas
aws s3api list-object-versions --bucket $BUCKET --prefix docs/relatorio.txt \
  --query "Versions[].{Id:VersionId,Ultima:IsLatest,Data:LastModified}" --output table
```

3. No Console, ative o toggle **Show versions** na listagem: as 3 versões aparecem.

### Passo 4 — "Deletar" e ressuscitar
```bash
aws s3 rm s3://$BUCKET/docs/relatorio.txt
aws s3 ls s3://$BUCKET/docs/         # sumiu...
aws s3api list-object-versions --bucket $BUCKET --prefix docs/relatorio.txt \
  --query "DeleteMarkers[].{Id:VersionId,Marker:'delete-marker'}" --output table   # ...mas está aqui
```
No Console (com Show versions ligado), **delete o delete marker**: o objeto **volta**. Esse é o
seguro contra deleção acidental.

> Repare com `s3api`: comandos `aws s3 ...` são a interface amigável; `aws s3api ...` expõe a API
> crua (mais controle). Você vai usar os dois.

---

## Parte D — Lifecycle rule (Console)

### Passo 5 — Criar a regra
1. Bucket → **Management** → **Create lifecycle rule**.
2. Nome: `esfriar-e-limpar` · Escopo: prefixo `docs/`.
3. Ações — marque e configure:
   - **Transition current versions**: para **Standard-IA** após **30 dias**.
   - **Permanently delete noncurrent versions**: após **30 dias**.
4. Crie e revise o resumo da regra (a linha do tempo do objeto).

> **Por quê:** essa é a dupla clássica — esfriar o dado atual (economia) e limpar versões velhas
> (versionamento sem lifecycle = fatura crescendo). Não vamos esperar 30 dias pra ver rodar 😄 —
> o que importa é saber montar.

---

## Parte E — Presigned URL (CLI)

### Passo 6 — Compartilhar um objeto privado por 5 minutos
```bash
aws s3 presign s3://$BUCKET/ola.txt --expires-in 300
```
1. Copie a URL gigante gerada e abra **no navegador**: o arquivo abre! Sem login, sem tornar nada
   público.
2. Espere 5 minutos (ou gere com `--expires-in 30` pra testar rápido) e abra de novo:
   **Access Denied — Request has expired**.

> **Por quê:** a URL carrega uma assinatura das *suas* credenciais com validade. É o padrão de
> mercado pra entregar arquivos privados (boletos, fotos, relatórios) sem abrir o bucket.

---

## Parte F — Site estático (Console + CLI)

Usaremos um **segundo bucket**, porque este será público de propósito.

### Passo 7 — Criar bucket do site e o conteúdo
```bash
SITE=curso-aws-site-<seunome>-<numero>
aws s3 mb s3://$SITE

cat > index.html <<'EOF'
<!doctype html><html lang="pt-br"><meta charset="utf-8">
<title>Meu site no S3</title>
<h1>No ar direto de um bucket S3! 🚀</h1>
<p>Módulo 06 do curso de AWS.</p>
EOF
cat > erro.html <<'EOF'
<!doctype html><html lang="pt-br"><meta charset="utf-8"><h1>404 — não achei 😢</h1>
EOF

aws s3 cp index.html s3://$SITE/
aws s3 cp erro.html s3://$SITE/
```

### Passo 8 — Liberar acesso público (conscientemente)
1. Console → bucket do site → **Permissions** → **Block public access** → **Edit** → desmarque
   tudo → Save (confirme digitando `confirm`).
2. Ainda em Permissions → **Bucket policy** → cole (troque `SITE` pelo nome real):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "LeituraPublicaDoSite",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::SITE/*"
  }]
}
```

### Passo 9 — Habilitar o website e testar
1. Bucket → **Properties** → **Static website hosting** → **Enable**.
2. Index document: `index.html` · Error document: `erro.html` → Save.
3. Copie o **endpoint** (`http://SITE.s3-website-us-east-1.amazonaws.com`) e abra no navegador. 🎉
4. Teste também uma URL inexistente (`/nada`) → sua página de erro aparece.

> Note: endpoint de website é **HTTP**. HTTPS + domínio próprio = CloudFront na frente (Módulo 14).

---

## Parte G — 🔥 Teardown

S3 não cobra por hora, mas bucket público não fica pra trás e armazenamento cobra por GB-mês.
Ritual completo:

```bash
# Apaga bucket do site (--force apaga os objetos junto)
aws s3 rb s3://$SITE --force

# O bucket principal tem VERSÕES — o rb --force não apaga versões antigas.
# Caminho garantido: esvaziar pelo Console (bucket → Empty → confirmar) e depois:
aws s3 rb s3://$BUCKET --force

# Conferir que não sobrou nada
aws s3 ls
```

> 💡 Se o `rb` reclamar de bucket não vazio, é o versionamento segurando versões/delete markers:
> use **Empty** no Console (ele apaga tudo, incluindo versões) e rode o `rb` de novo.

- ✅ `aws s3 ls` sem os buckets do módulo.
- ✅ Arquivos locais de teste podem ser apagados (`ola.txt`, `relatorio*.txt`, `projeto/`, `*.html`).

---

## ✅ Checklist de conclusão do módulo

- [ ] Bucket criado com nome único global (e padrões seguros: ACLs off, BPA on).
- [ ] Objetos subidos/baixados pelo Console e por `aws s3 cp` / `sync`.
- [ ] Viu o Access Denied da Object URL (privado por padrão) e a criptografia SSE-S3 automática.
- [ ] Versionamento habilitado; 3 versões listadas; objeto "deletado" e ressuscitado via delete marker.
- [ ] Lifecycle rule criada (transição pra IA + limpeza de versões antigas).
- [ ] Presigned URL gerada, testada e expirada.
- [ ] Site estático no ar pelo endpoint de website (com página de erro funcionando).
- [ ] Teardown: `aws s3 ls` limpo, nenhum bucket do módulo sobrando.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-06/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-06/`) e para o **Módulo 07 — Bancos de dados**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 6" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
