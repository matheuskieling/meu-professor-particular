# Módulo 04 — Compute: EC2 (Teoria)

> Objetivo do módulo: dominar o **EC2 (Elastic Compute Cloud)** — o serviço de máquinas
> virtuais da AWS e o coração do modelo IaaS. Você vai entender o que é uma instância, como
> escolher **AMI** e **tipo**, conectar por **SSH**, automatizar o boot com **user data**,
> gerenciar discos **EBS** e snapshots, usar o **metadata service (IMDSv2)** e — crucial —
> saber **o que cobra em cada estado** do ciclo de vida. No fim da prática, você terá um
> servidor web real no ar... e destruído com verificação.

---

## 1. O que é uma instância EC2

Uma **instância** é uma **máquina virtual** rodando num servidor físico da AWS. Você escolhe:

- a **AMI** (o "molde": SO + software pré-instalado);
- o **tipo** (CPU/RAM — quanto músculo);
- a **rede** (VPC/subnet/security group — o Módulo 03 inteiro!);
- o **disco** (EBS — tamanho e tipo);
- a **key pair** (como você entra via SSH).

E em ~1 minuto tem um servidor no ar, cobrado **por segundo** (mínimo de 60s) enquanto roda.
É o exemplo canônico de IaaS: **da virtualização pra baixo é a AWS; do SO pra cima é você**
(patches, usuários, firewall do SO — lembra da responsabilidade compartilhada?).

> 💡 EC2 é **regional/zonal**: a instância vive numa **subnet**, que vive numa **AZ**. Tudo o
> que você aprendeu no Módulo 03 se aplica diretamente aqui.

---

## 2. AMIs — o molde da máquina

**AMI (Amazon Machine Image)** é a imagem a partir da qual a instância nasce: SO, configurações
e o que mais estiver "assado" nela. Fontes:

| Origem | Exemplos | Cuidado |
|--------|----------|---------|
| **AWS** | Amazon Linux 2023, Ubuntu, Windows Server | O caminho padrão. Amazon Linux 2023 é otimizado pra AWS e grátis. |
| **Marketplace** | Appliances comerciais (firewall, BI...) | Podem ter **custo de licença por hora** além da instância! |
| **Comunidade** | Imagens públicas de terceiros | Confiança zero por padrão — pode ter qualquer coisa dentro. |
| **Suas** | Criadas a partir de instâncias suas | O jeito de "clonar" um servidor configurado (golden image). |

Pontos importantes:

- AMIs são **regionais** — a AMI `ami-0abc...` de `us-east-1` **não existe** em `sa-east-1`
  (dá pra copiar entre regiões; o ID muda).
- Você pode **criar uma AMI da sua instância** configurada e lançar N cópias idênticas — é a
  base de Auto Scaling (Módulo 05).
- A arquitetura importa: `x86_64` vs `arm64` (**Graviton** — chips ARM da AWS, mais baratos
  por desempenho; a AMI precisa ser da arquitetura certa).

---

## 3. Tipos de instância — aprendendo a ler `t3.micro`

O nome do tipo é um código. Destrinchando **`t3.micro`**:

```
 t        3        .micro
 │        │           │
família  geração    tamanho
```

- **Família** — o perfil de hardware (letra):

| Família | Perfil | Uso típico |
|---------|--------|-----------|
| **t** | *Burstable* — CPU básica com "picos" por créditos | Dev, testes, apps leves — **nosso caso** |
| **m** | *General purpose* — equilíbrio CPU:RAM (1:4) | Servidores de app "meio de estrada" |
| **c** | *Compute optimized* — mais CPU por GB | Processamento pesado, encoding, jogos |
| **r** | *Memory optimized* — mais RAM por vCPU (1:8) | Bancos, caches, análise em memória |
| Outras | `g/p` (GPU), `i/d` (disco local), `x` (RAM extrema)... | Casos específicos |

- **Geração** — o número: quanto maior, mais novo (e melhor custo-benefício). Um `m7` supera
  um `m5`. Letras extras após o número indicam variantes: `g` = **Graviton/ARM** (`t4g`, `m7g`),
  `a` = AMD, `n` = rede turbinada.
- **Tamanho** — `nano → micro → small → medium → large → xlarge → 2xlarge...` Cada degrau
  **dobra** (aproximadamente) CPU/RAM e preço.

> 💡 A família **t** é *burstable*: você tem uma linha de base de CPU e acumula **créditos**
> quando está ocioso; picos gastam créditos. Perfeita pra estudo e apps leves; péssima pra
> carga contínua de 100% de CPU (créditos acabam, desempenho cai pra linha de base).

> 💵 **Free Tier:** 750 h/mês de **`t3.micro`** (12 meses, nas regiões onde `t2.micro` não
> existe mais — `us-east-1` incluída; contas novas com o modelo de créditos ganham valor
> equivalente). 750h = um mês inteiro de **uma** instância ligada. Duas instâncias = as horas
> se dividem.

---

## 4. Key pairs — a chave da porta SSH

Autenticação por senha em servidor é passado. O EC2 usa **par de chaves**:

- A AWS guarda a **chave pública** (injetada na instância no boot).
- Você baixa a **chave privada** (`.pem`) — **uma única vez**, na criação.
- SSH: `ssh -i minha-chave.pem ec2-user@<ip-público>`.

Regras de sobrevivência:

1. `chmod 400 minha-chave.pem` — o SSH **recusa** chave com permissão aberta.
2. Perdeu a `.pem`? A AWS **não tem cópia**. (Há contornos, mas o simples é: não perca.)
3. **Nunca** no repositório git — mesmo destino das access keys: `~/.ssh/`, fora do repo.
4. O usuário de login depende da AMI: `ec2-user` (Amazon Linux), `ubuntu` (Ubuntu), etc.

> 💡 Alternativas modernas que você verá por aí: **EC2 Instance Connect** e **SSM Session
> Manager** (acesso via IAM, sem chave nem porta 22 aberta — o padrão corporativo). No curso
> começamos pelo SSH clássico pra entender a base.

---

## 5. User data — o script de nascimento

**User data** é um script que roda **automaticamente no primeiro boot** da instância, como
root. É o "bootstrap": instalar pacotes, subir serviços, configurar tudo sem tocar na máquina.

```bash
#!/bin/bash
dnf update -y
dnf install -y nginx
systemctl enable --now nginx
echo "<h1>Subi via user data! $(hostname)</h1>" > /usr/share/nginx/html/index.html
```

Pontos-chave:

- Roda **uma vez só**, no primeiro boot (não a cada reinício, por padrão).
- Começa com `#!/bin/bash` (shebang) — sem isso, não executa.
- Log de execução: `/var/log/cloud-init-output.log` — **o primeiro lugar pra olhar** quando
  "o user data não funcionou".
- É a semente da automação: com user data + AMI, você descreve servidores em vez de montá-los
  à mão — essencial pra Auto Scaling (M05) e IaC (M11).

> ⚠️ **Armadilha clássica:** colocar segredos (senhas, chaves) no user data. Ele fica legível
> por**qualquer processo** na instância via metadata. Segredos vêm de IAM roles + Secrets
> Manager (M13), nunca do user data.

---

## 6. EBS — os discos da instância

**EBS (Elastic Block Store)** é o disco virtual de rede das instâncias: persiste
**independentemente** da vida da instância (dentro da mesma AZ).

### Tipos que importam (2025/2026)

| Tipo | O que é | Quando usar |
|------|---------|-------------|
| **gp3** | SSD de uso geral — **o padrão atual**. 3000 IOPS/125 MB/s de base, ajustáveis sem mexer no tamanho | Praticamente tudo. Mais barato e previsível que o antigo gp2 |
| **io2** | SSD de alta performance com IOPS provisionadas (até centenas de milhares) | Bancos críticos que exigem IOPS garantidas |
| st1 / sc1 | HDD de throughput / HDD frio | Big data sequencial / arquivos raramente acessados |

> 💡 Se alguém sugerir **gp2**, é material antigo: **gp3 é melhor e mais barato** em
> praticamente todos os casos. Free Tier: 30 GB de EBS (gp3 ou gp2) por 12 meses.

### Snapshots

**Snapshot** = backup pontual do volume, salvo internamente no S3:

- **Incremental**: o primeiro copia tudo; os seguintes só os blocos alterados (barato).
- Pode virar **volume novo em outra AZ** ou **AMI** — é assim que se "move" disco entre AZs.
- Cobra por GB armazenado (~US$ 0,05/GB·mês) — snapshots esquecidos se acumulam.

### Detalhes que caem em prova (e na vida)

- Volume EBS é **zonal**: só anexa em instância **da mesma AZ**.
- **DeleteOnTermination**: o volume raiz, por padrão, **morre com a instância**; volumes
  extras, por padrão, **sobrevivem** (e continuam cobrando!).
- **Instance store** (famílias `i`/`d` e outras): disco físico local, ultrarrápido e **efêmero**
  — os dados **somem** em stop/terminate. Não confundir com EBS.

---

## 7. Instance metadata — a instância se conhecendo (IMDSv2)

Todo EC2 pode consultar um endereço mágico — `http://169.254.169.254` — o **Instance Metadata
Service (IMDS)**: IP, AZ, tipo, tags... e as **credenciais temporárias da IAM role** anexada.
É daí que a CLI/SDK dentro da instância tira as credenciais **sem nenhuma chave gravada**
(fechando o ciclo do Módulo 02!).

Por ser tão poderoso, ele foi endurecido. **IMDSv2** (o padrão atual, obrigatório nas
instâncias novas) exige **sessão com token**:

```bash
# 1. Pegar um token de sessão (PUT!)
TOKEN=$(curl -sX PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# 2. Usar o token nas consultas
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id
```

> **Por que a v2 existe:** o IMDSv1 (GET simples, sem token) era explorável via **SSRF** — um
> app vulnerável podia ser induzido a buscar `169.254.169.254` e vazar as credenciais da role.
> O PUT + token da v2 quebra esse ataque. Por isso as instâncias novas já nascem
> **IMDSv2-only** — e é assim que faremos.

---

## 8. Ciclo de vida — o que cobra em cada estado 💵

O conhecimento que salva sua fatura. Estados e cobranças:

| Estado | Compute (instância) | EBS | IPv4 público |
|--------|--------------------:|----:|-------------:|
| **running** | ✅ cobra | ✅ cobra | ✅ cobra |
| **stopped** | ❌ não cobra | ✅ **cobra!** | EIP ocioso ✅ cobra |
| **terminated** | ❌ | ❌ (volumes com DeleteOnTermination) | ❌ (se liberado) |

- **Stop** = desligar: some o conteúdo da RAM, **o EBS persiste**; ao dar start, a instância
  pode mudar de host físico e **o IP público muda** (a menos que use Elastic IP).
- **Terminate** = destruir: instância deixa de existir; volume raiz deletado (por padrão).
  **Irreversível.**
- **Reboot** = reinício simples: mesmo host, mesmo IP.
- **Stop está disponível só pra instâncias EBS-backed** (as nossas).

> ⚠️ **Armadilhas de custo clássicas:**
> 1. "Parei a instância, não pago nada" — **falso**: o disco EBS continua cobrando.
> 2. **Elastic IP**: um IP fixo que você aloca. Associado a uma instância **ligada**, custa o
>    normal de um IPv4 (~US$ 3,60/mês); **ocioso** (instância parada/terminada ou EIP solto),
>    continua custando — e é puro desperdício. Terminou? **Release.**
> 3. Snapshots esquecidos acumulando GB·mês.
>
> Por isso o teardown deste módulo é **terminate + verificação** de volumes, snapshots e EIPs.

---

## 9. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Instância | Máquina virtual EC2 rodando numa AZ, cobrada por segundo enquanto roda. |
| AMI | Imagem-molde (SO + software) da qual a instância nasce; regional. |
| `t3.micro` | Família t (burstable) + geração 3 + tamanho micro; a do Free Tier. |
| Graviton | Chips ARM da AWS (`t4g`, `m7g`...); melhor preço-desempenho, exige AMI arm64. |
| Key pair | Chave pública (AWS) + privada (`.pem`, você); a porta de entrada SSH. |
| User data | Script executado como root no primeiro boot; bootstrap da instância. |
| EBS | Disco virtual de rede, persistente e zonal; **gp3** é o padrão atual. |
| Snapshot | Backup incremental de um volume EBS; vira volume novo ou AMI. |
| Instance store | Disco local efêmero de algumas famílias; dados somem no stop/terminate. |
| IMDSv2 | Metadata service com sessão por token (PUT); mata o ataque SSRF do v1. |
| Stop vs. Terminate | Desligar (EBS persiste e **cobra**) vs. destruir (irreversível). |
| Elastic IP | IPv4 fixo alocável; **custa sempre**, e ocioso é puro desperdício. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Decodifique `r6g.xlarge`: família? geração? o `g` é o quê? tamanho?
2. Uma instância **parada** (stopped) gera custo? De quê, exatamente?
3. Qual a diferença entre **stop** e **terminate** pro volume EBS raiz? E pro IP público?
4. Por que o IMDSv2 exige um token via PUT antes de qualquer consulta? Que ataque isso evita?
5. Você precisa que 3 instâncias novas subam já com nginx instalado e configurado. Quais
   **duas** ferramentas deste módulo resolvem isso, e como elas se combinam?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
