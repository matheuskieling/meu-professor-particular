# Módulo 06 — Storage: S3 & cia (Teoria)

> Objetivo do módulo: dominar o **Amazon S3** — provavelmente o serviço mais icônico da AWS — de
> ponta a ponta: buckets, objetos, classes de armazenamento, versionamento, lifecycle, segurança
> (políticas, Block Public Access, criptografia), presigned URLs e site estático. E fechar com o
> mapa mental **EBS vs. EFS vs. S3**: qual storage usar em cada situação.
>
> Boa notícia: o Free Tier do S3 (5 GB) cobre a prática inteira. **Custo ≈ zero.**

---

## 1. S3 em uma frase (e por que ele é tão importante)

**Amazon S3 (Simple Storage Service)** é armazenamento de **objetos**: você guarda arquivos
(de bytes a 5 TB cada) em **buckets**, acessíveis via HTTP/API, com durabilidade absurda de
**11 noves** (99,999999999% — projetado pra perder 1 objeto a cada 10 milhões... em 10 mil anos).

Ele não é um "disco": não se monta num servidor, não tem pastas de verdade, não edita um byte no
meio do arquivo. É um **balde de objetos imutáveis** com API. E é a espinha dorsal de meio mundo:
data lakes, backups, sites estáticos, uploads de usuários, artefatos de build, logs…

### Conceitos-base

| Conceito | O que é |
|----------|---------|
| **Bucket** | O contêiner. Nome **globalmente único** (entre todas as contas AWS do mundo!), criado **numa região** (os dados ficam lá). |
| **Objeto** | O arquivo em si + metadados. Até 5 TB. |
| **Chave (key)** | O "nome completo" do objeto: `fotos/2026/praia.jpg`. **Não existem pastas de verdade** — as `/` na chave criam a ilusão de pastas que o Console mostra. |
| **Consistência** | Desde 2020, o S3 é **fortemente consistente**: depois de um PUT/DELETE, qualquer leitura já vê o estado novo. (Antes era "eventual" pra alguns casos — pegadinha de material antigo.) |

> 💡 **Armadilha clássica:** nome de bucket é global e disputado. `teste` já foi. Use um padrão
> tipo `empresa-projeto-ambiente` ou adicione um sufixo único. E o nome tem regras: minúsculas,
> números e hífens, 3–63 caracteres, sem `_`.

---

## 2. Classes de armazenamento — pagando o preço certo pela temperatura do dado

Nem todo dado é igual: uns são acessados toda hora ("quentes"), outros uma vez por ano ("frios").
O S3 tem **classes** com preços diferentes de armazenamento × recuperação:

| Classe | Pra quê | Característica |
|--------|---------|----------------|
| **Standard** | Dado quente, acesso frequente | Padrão. Multi-AZ, sem custo de recuperação. |
| **Intelligent-Tiering** | Padrão de acesso desconhecido | Move o objeto de camada sozinho conforme o uso; pequena taxa de monitoramento. |
| **Standard-IA** (Infrequent Access) | Acesso raro, mas precisa estar disponível já | Armazenar mais barato, **recuperar cobra por GB**; mínimo de 30 dias. |
| **One Zone-IA** | Acesso raro E recriável | Como o IA, porém **numa única AZ** (se a AZ for destruída, perdeu). Mais barato ainda. |
| **Glacier Instant Retrieval** | Arquivo acessado ~1x por trimestre | Baratíssimo, recuperação em **milissegundos**; mínimo 90 dias. |
| **Glacier Flexible Retrieval** | Arquivo raro, pode esperar | Recuperação em **minutos a horas**; mínimo 90 dias. |
| **Glacier Deep Archive** | Arquivamento de longuíssimo prazo (compliance) | O mais barato de todos; recuperação em **horas (padrão 12h)**; mínimo 180 dias. |

**Modelo mental:** quanto mais frio, mais barato **guardar** e mais caro/lento **recuperar**.
As classes IA/Glacier têm **períodos mínimos de cobrança** (30/90/180 dias) — apagar antes não
devolve o dinheiro.

> ⚠️ **Armadilha:** jogar tudo em IA/Glacier "porque é mais barato" e depois pagar caro em taxas
> de recuperação (e por objeto pequeno — IA cobra mínimo de 128 KB por objeto). Classe fria é pra
> dado frio de verdade.

---

## 3. Versionamento — o "ctrl+Z" do bucket

Com **versioning** habilitado, cada PUT numa chave existente cria uma **nova versão** — a anterior
fica guardada. E um DELETE não apaga nada: só insere um **delete marker** por cima (o objeto "some",
mas as versões continuam lá; remova o marker e ele "volta").

- Protege contra **sobrescrita e deleção acidental** (inclusive por bug ou ransomware).
- Uma vez habilitado, dá pra **suspender**, mas nunca voltar ao estado "nunca versionado".
- **Custo:** cada versão ocupa (e cobra) espaço. Versionamento sem lifecycle pra limpar versões
  antigas = fatura crescendo em silêncio.

---

## 4. Lifecycle rules — automação da temperatura e da limpeza

**Regras de ciclo de vida** automatizam transições e expirações por idade do objeto:

```
Exemplo clássico de política de logs:
  dia 0   → Standard (dado quente)
  dia 30  → transição pra Standard-IA
  dia 90  → transição pra Glacier Flexible
  dia 365 → expiração (deleta)
  + versões antigas: expirar após 30 dias
  + abortar multipart uploads incompletos após 7 dias
```

É o casamento perfeito com o versionamento (limpar versões velhas) e com as classes (esfriar o
dado automaticamente). Regras podem filtrar por **prefixo** (ex.: só `logs/`) e por **tags**.

---

## 5. Segurança: quem pode acessar o quê

O S3 já foi o campeão de vazamentos por má configuração ("bucket aberto"). Hoje os padrões são
seguros por default — entenda as camadas:

### Bucket policies vs. ACLs

- **Bucket policy** — documento JSON (mesma linguagem do IAM) anexado **ao bucket**, dizendo quem
  pode fazer o quê em quais objetos. **É o mecanismo recomendado** pra dar acesso ao bucket
  (inclusive público ou entre contas).
- **ACLs** — mecanismo **legado**, anterior ao IAM, por objeto/bucket. Desde 2023, buckets novos
  vêm com **ACLs desabilitadas** (`Object Ownership = Bucket owner enforced`) — e é assim que deve
  ficar. Controle acesso com policies (IAM + bucket policy), não ACL.

### Block Public Access (BPA)

Uma **trava de segurança em 4 chaves** (por bucket e por conta) que **bloqueia qualquer
configuração pública**, mesmo que uma policy tente permitir. Vem **ligada por padrão** em buckets
novos. Só desligue conscientemente (ex.: site estático público) e **só no bucket específico**.

> 💡 A ordem de avaliação, simplificada: **negação explícita vence tudo** → BPA bloqueia público →
> depois soma-se IAM policy + bucket policy. Sem nenhum allow, o default é **negar**.

### Criptografia em repouso

| Opção | Chave gerenciada por | Quando usar |
|-------|----------------------|-------------|
| **SSE-S3** (AES-256) | AWS/S3 | **Padrão desde 2023** — todo objeto novo já é criptografado assim, de graça, automático. |
| **SSE-KMS** | AWS KMS (chave sua ou da AWS) | Quando precisa de controle/auditoria da chave (quem usou, quando), rotação própria, políticas por chave. Tem custo por requisição KMS. |
| SSE-C / client-side | Você | Casos especiais: a AWS nunca vê sua chave. |

### Presigned URLs — compartilhar sem abrir o bucket

Uma **presigned URL** é uma URL temporária **assinada com as suas credenciais** que dá acesso a
**um objeto específico por tempo limitado** (ex.: 15 min). Quem tiver a URL faz o GET (ou PUT!)
**com as suas permissões**, sem precisar de conta AWS. É o padrão pra "baixar o boleto", "subir o
anexo" — o bucket continua 100% privado.

---

## 6. Static website hosting

O S3 serve **sites estáticos** (HTML/CSS/JS — sem backend) direto do bucket:

1. Habilitar **Static website hosting** no bucket (definir `index.html` e página de erro).
2. Desligar o Block Public Access **daquele bucket**.
3. Bucket policy permitindo `s3:GetObject` público no conteúdo.
4. Acessar pelo **endpoint de website** (`http://bucket.s3-website-us-east-1.amazonaws.com`).

Limitações: o endpoint de website é **HTTP** (sem HTTPS) e sem domínio bonito. Em produção,
coloca-se **CloudFront** na frente (HTTPS + CDN + domínio próprio) — veremos no Módulo 14.

---

## 7. EBS vs. EFS vs. S3 — qual storage usar?

Os três "storages" da AWS resolvem problemas diferentes. Este comparativo cai em prova de
certificação e — mais importante — em decisão de arquitetura real:

| | **EBS** | **EFS** | **S3** |
|---|---|---|---|
| Tipo | **Bloco** (disco virtual) | **Arquivo** (NFS) | **Objeto** (API HTTP) |
| Analogia | O HD/SSD do servidor | O "drive de rede" compartilhado | O balde infinito com API |
| Quem acessa | **1 instância** EC2 por vez* (na mesma AZ) | **Várias instâncias** ao mesmo tempo (multi-AZ) | Qualquer coisa com HTTP/SDK, de qualquer lugar |
| Escopo | Preso a **uma AZ** | Regional (multi-AZ) | Regional, durabilidade 11 noves |
| Caso de uso | Disco de boot, banco de dados na instância | Diretório compartilhado (uploads, CMS, home dirs) | Backups, mídia, data lake, site estático, logs |
| Edição parcial | Sim (é um disco) | Sim (é um filesystem) | **Não** — objeto é substituído inteiro |

\* Multi-Attach existe em io1/io2, mas é exceção pra casos bem específicos.

**Snapshots de EBS:** backup **incremental** do volume, armazenado internamente no S3 (você não vê
o bucket). Primeiro snapshot é cheio; os seguintes só guardam blocos alterados. É deles que nascem
AMIs e restaurações — inclusive **em outra AZ** (o jeito de "mover" um volume de AZ).

> 💡 **Regra mental rápida:** precisa de **disco pro EC2**? EBS. Precisa que **várias máquinas
> enxerguem os mesmos arquivos**? EFS. É **conteúdo/backup/dado servido por API**? S3 — e na
> dúvida entre eles, comece pensando em S3, que é o mais barato e durável.

---

## 8. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Bucket / objeto / chave | Contêiner global-único / arquivo+metadados / "caminho" do objeto. |
| Consistência forte | Leu depois de escrever, já vê o novo — garantido (desde 2020). |
| Classes de armazenamento | Standard → IA → Glacier: mais frio = guardar barato, recuperar caro/lento. |
| Versionamento | Cada PUT vira versão nova; DELETE só põe um delete marker. |
| Lifecycle rule | Automação por idade: transiciona de classe e expira objetos/versões. |
| Bucket policy | JSON de permissões anexado ao bucket — o jeito certo de dar acesso. |
| ACL | Mecanismo legado de permissão; desabilitado por padrão hoje. |
| Block Public Access | Trava que impede acesso público mesmo com policy permissiva. |
| SSE-S3 / SSE-KMS | Criptografia em repouso: automática (padrão) / com chave KMS auditável. |
| Presigned URL | URL temporária assinada pra acessar um objeto sem abrir o bucket. |
| EBS / EFS / S3 | Bloco (1 EC2, 1 AZ) / arquivo (N EC2, NFS) / objeto (API, 11 noves). |
| Snapshot | Backup incremental de volume EBS, guardado no S3. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Por que o nome de um bucket precisa ser único **no mundo**, e quais as regras básicas de nome?
2. Logs que você consulta muito por 30 dias e quase nunca depois, mas precisa guardar 1 ano — que
   combinação de **classes + lifecycle** você montaria?
3. Com versionamento ligado, o que acontece de verdade quando você "deleta" um objeto?
4. Qual a diferença prática entre **SSE-S3** e **SSE-KMS**, e qual é o padrão hoje?
5. Uma frota de EC2s precisa compartilhar o mesmo diretório de uploads; outro sistema precisa de
   um disco de boot; um terceiro guarda backups acessados 1x/ano. Qual storage pra cada?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
