# Módulo 03 — Rede: VPC (Prática Guiada)

> Objetivo desta prática: construir do zero uma **VPC customizada** com subnet **pública** e
> **privada**, Internet Gateway, route tables e security group — primeiro no Console (pra
> enxergar cada peça), depois **recriar tudo via CLI** (pra fixar). No fim, **teardown completo
> obrigatório**.
>
> ⏱️ Tempo estimado: 60–90 min. 💵 Custo: **US$ 0** se seguir exatamente o roteiro.
> VPC, subnets, IGW, route tables, SGs e NACLs **não custam nada**. O que custaria: **NAT
> Gateway** (não vamos criar) e **Elastic IP/IPv4 público ocioso** (não vamos alocar).

---

## ⚠️ Antes de começar

- Pré-requisitos: Módulos 01 e 02 completos (CLI configurada, você sabe ler um ARN e um JSON).
- Região: **us-east-1** em tudo (Console e CLI). Lembre da armadilha do "recurso sumido".
- **Não criaremos nenhuma instância** neste módulo — só a rede. A VPC vazia é o palco; os
  atores (EC2) entram no Módulo 04, usando exatamente o que você montar aqui.
- ⚠️ **NAT Gateway custa ~US$ 32/mês + GB trafegado.** No Passo 7 vamos apenas **ver onde**
  ele seria criado. Se decidir criar pra ver funcionando, siga o passo opcional e **destrua
  imediatamente** (NAT + Elastic IP).

---

## Parte A — Construir a VPC no Console

Vamos montar esta arquitetura:

```
VPC curso-vpc (10.0.0.0/16)          [us-east-1]
├── Subnet pública  10.0.1.0/24      [us-east-1a] ── rota 0.0.0.0/0 → IGW
├── Subnet privada  10.0.2.0/24      [us-east-1a] ── sem rota pra fora
├── Internet Gateway curso-igw
├── Route tables: curso-rt-publica / curso-rt-privada
└── Security group: curso-sg-web (443/80 do mundo, 22 só do seu IP)
```

### Passo 1 — Criar a VPC
1. Console → **VPC** → **Your VPCs** → **Create VPC**.
2. Escolha **VPC only** (queremos montar peça por peça — o assistente "VPC and more" faz tudo
   sozinho e você não aprende; e ele adora criar NAT Gateway pago sem você reparar).
3. Name: `curso-vpc` · IPv4 CIDR: `10.0.0.0/16` → **Create VPC**.

> **Por quê `10.0.0.0/16`:** faixa privada, 65.536 IPs — espaço de sobra pra fatiar em subnets
> `/24` sem colidir com nada.

### Passo 2 — Criar as duas subnets
1. **Subnets** → **Create subnet** → VPC: `curso-vpc`.
2. Subnet 1: name `curso-subnet-publica`, AZ `us-east-1a`, CIDR `10.0.1.0/24`.
3. **Add new subnet** → Subnet 2: name `curso-subnet-privada`, AZ `us-east-1a`, CIDR
   `10.0.2.0/24` → **Create subnet**.

> Repare: por enquanto as duas são **idênticas** — nenhuma é "pública" ainda. Quem vai
> diferenciá-las é a **rota**, nos próximos passos. (Numa arquitetura real de produção, você
> repetiria o par em outra AZ — multi-AZ; aqui uma AZ basta pro aprendizado.)

### Passo 3 — Criar e anexar o Internet Gateway
1. **Internet gateways** → **Create internet gateway** → name `curso-igw` → criar.
2. Ele nasce **detached**. Selecione → **Actions → Attach to VPC** → `curso-vpc`.

### Passo 4 — Route table pública
1. **Route tables** → **Create route table** → name `curso-rt-publica`, VPC `curso-vpc`.
2. Selecione-a → aba **Routes** → **Edit routes** → **Add route**:
   - Destination: `0.0.0.0/0` · Target: **Internet Gateway** → `curso-igw` → **Save**.
3. Aba **Subnet associations** → **Edit subnet associations** → marque
   `curso-subnet-publica` → salvar.

> 🎉 **Neste momento** a `curso-subnet-publica` virou de fato pública: a route table associada
> a ela tem caminho pro IGW. Repare que a rota `10.0.0.0/16 → local` já estava lá — é a rota
> implícita da VPC, não removível.

### Passo 5 — Route table privada
1. **Create route table** → name `curso-rt-privada`, VPC `curso-vpc`.
2. **Não adicione** rota nenhuma (só a `local` implícita).
3. Associe à `curso-subnet-privada`.

> **Por que criar uma route table "vazia"?** Explicitude. A subnet privada poderia ficar na
> *main* route table da VPC, mas aí qualquer rota adicionada à main no futuro vazaria pra ela.
> Route table própria = intenção documentada. É aqui que a rota pro **NAT Gateway** entraria
> um dia (`0.0.0.0/0 → nat-...`).

### Passo 6 — Security group
1. **Security groups** → **Create security group** → name `curso-sg-web`,
   description `Web publica do curso`, VPC `curso-vpc`.
2. **Inbound rules**:
   - HTTP (80) · Source: `0.0.0.0/0`
   - HTTPS (443) · Source: `0.0.0.0/0`
   - SSH (22) · Source: **My IP** (o console preenche seu IP com /32)
3. **Outbound**: deixe o default (All traffic). **Create security group**.

> ⚠️ **Nunca** SSH aberto pra `0.0.0.0/0`. Bots varrem a porta 22 da internet inteira o dia
> todo. `/32` = exatamente 1 IP: o seu. (Se seu IP mudar — internet residencial —, é só editar
> a regra.)
>
> 💡 Lembre: SG é **stateful** — não precisamos de regra de entrada pras *respostas* das
> conexões que saírem, nem de regra de saída pras respostas do que entrar.

### Passo 7 — NAT Gateway: só olhar, não criar 👀
1. **NAT gateways** → **Create NAT gateway** (só abra a tela, **não confirme**).
2. Observe o que ele pede: uma **subnet** (seria a `curso-subnet-publica` — o NAT mora na
   pública pra servir a privada!) e um **Elastic IP**.
3. **Cancele.** ⚠️ Se confirmasse: ~US$ 0,045/h (≈ US$ 32/mês) + US$ 0,045/GB, começando a
   contar **no minuto da criação**.

> **Opcional (consciente):** se quiser MUITO vê-lo funcionando: crie, veja o estado `Available`,
> adicione a rota `0.0.0.0/0 → nat-...` na `curso-rt-privada`, observe, e **destrua em
> seguida**: delete a rota → delete o NAT gateway (leva uns minutos) → **Release** no Elastic
> IP (senão o IP ocioso cobra ~US$ 3,60/mês!). Custo total de uns minutos: centavos.

### Passo 8 — Conferir o DNS da VPC
1. **Your VPCs** → selecione `curso-vpc` → veja **DNS resolution** (on) e **DNS hostnames**
   (**off** — padrão de VPC customizada).
2. **Actions → Edit VPC settings** → marque **Enable DNS hostnames** → salvar.

> Sem isso, instâncias com IP público na sua VPC não ganham nome DNS. Na default VPC já vem
> ligado; na customizada é você quem liga. Detalhe pequeno que causa confusão grande no M04.

---

## Parte B — Recriar tudo via CLI

Agora **delete mentalmente** o que fez e vamos reconstruir por comandos — é assim que se
automatiza e é assim que fixa. (Não precisa deletar a VPC do Console ainda; os CIDRs não
colidem porque VPCs são isoladas entre si. Teremos duas VPCs até o teardown.)

> 💡 Vamos guardar os IDs em variáveis de shell (`VPC_ID=...`) — os comandos seguintes
> dependem deles. Se fechar o terminal, recupere os IDs com os `describe-*`.

### Passo 9 — VPC
```bash
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=curso-vpc-cli}]' \
  --query Vpc.VpcId --output text)
echo $VPC_ID

aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames
```

### Passo 10 — Subnets
```bash
SUB_PUB=$(aws ec2 create-subnet --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=curso-subnet-publica-cli}]' \
  --query Subnet.SubnetId --output text)

SUB_PRIV=$(aws ec2 create-subnet --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=curso-subnet-privada-cli}]' \
  --query Subnet.SubnetId --output text)

echo "publica: $SUB_PUB / privada: $SUB_PRIV"
```

### Passo 11 — IGW: criar e anexar
```bash
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=curso-igw-cli}]' \
  --query InternetGateway.InternetGatewayId --output text)

aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
```

### Passo 12 — Route table pública: criar, rotear, associar
```bash
RT_PUB=$(aws ec2 create-route-table --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=curso-rt-publica-cli}]' \
  --query RouteTable.RouteTableId --output text)

aws ec2 create-route --route-table-id $RT_PUB \
  --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID

aws ec2 associate-route-table --route-table-id $RT_PUB --subnet-id $SUB_PUB
```
> São exatamente os 3 cliques do Console: criar tabela → adicionar rota → associar subnet.
> A subnet privada ficamos devendo de propósito: sem associação explícita, ela cai na *main*
> route table (que só tem a rota `local`) — privada do mesmo jeito.

### Passo 13 — Security group
```bash
SG_ID=$(aws ec2 create-security-group --vpc-id $VPC_ID \
  --group-name curso-sg-web-cli --description "Web publica do curso (CLI)" \
  --query GroupId --output text)

MEU_IP=$(curl -s https://checkip.amazonaws.com)

aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 80  --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 22  --cidr ${MEU_IP}/32
```

### Passo 14 — Inspecionar o que você construiu
```bash
aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC_ID \
  --query "Subnets[].{Nome:Tags[?Key=='Name']|[0].Value,CIDR:CidrBlock,AZ:AvailabilityZone}" \
  --output table

aws ec2 describe-route-tables --filters Name=vpc-id,Values=$VPC_ID \
  --query "RouteTables[].Routes[].{Destino:DestinationCidrBlock,Alvo:GatewayId}" --output table

aws ec2 describe-security-groups --group-ids $SG_ID \
  --query "SecurityGroups[0].IpPermissions[].{Porta:FromPort,Origem:IpRanges[0].CidrIp}" \
  --output table
```
> Compare com o diagrama do início da Parte A. Bate? Então você acabou de descrever uma rede
> inteira em ~10 comandos reproduzíveis — o embrião de IaC (Módulo 11).

---

## Parte C — Teardown COMPLETO (obrigatório)

Nada aqui está cobrando, mas o ritual é inegociável — e a **ordem importa** (dependências:
não dá pra deletar a VPC com coisas dentro).

### As duas VPCs (Console e CLI)

**Via CLI** (a VPC da CLI; para a do Console, repita trocando os IDs — descubra-os com os
`describe-*` filtrando pelo Name, ou use o Console):

```bash
# 1. Security group (os default de cada VPC não podem/precisam ser deletados)
aws ec2 delete-security-group --group-id $SG_ID

# 2. Desassociar e deletar a route table pública
ASSOC=$(aws ec2 describe-route-tables --route-table-ids $RT_PUB \
  --query "RouteTables[0].Associations[0].RouteTableAssociationId" --output text)
aws ec2 disassociate-route-table --association-id $ASSOC
aws ec2 delete-route-table --route-table-id $RT_PUB

# 3. Desanexar e deletar o IGW
aws ec2 detach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID

# 4. Subnets
aws ec2 delete-subnet --subnet-id $SUB_PUB
aws ec2 delete-subnet --subnet-id $SUB_PRIV

# 5. A VPC em si
aws ec2 delete-vpc --vpc-id $VPC_ID
```

**Via Console** (pra VPC da Parte A, o caminho rápido): **Your VPCs** → selecione `curso-vpc`
→ **Actions → Delete VPC**. O Console lista as dependências e deleta em cascata (IGW, subnets,
route tables, SGs) — digite `delete` pra confirmar.

### Verificação final (não pule!)

```bash
aws ec2 describe-vpcs --query "Vpcs[].{Id:VpcId,CIDR:CidrBlock,Default:IsDefault}" --output table
aws ec2 describe-nat-gateways --filter Name=state,Values=available,pending
aws ec2 describe-addresses
```
- ✅ Só a **default VPC** (`172.31.0.0/16`, Default=True) deve restar. **Não delete a default.**
- ✅ NAT gateways: lista **vazia**.
- ✅ Addresses (Elastic IPs): lista **vazia** — EIP alocado e solto cobra!
- ✅ Se fez o NAT opcional: confirme também no Console que o estado dele é `Deleted` e o EIP
  foi liberado (Release).

---

## ✅ Checklist de conclusão do módulo

- [ ] VPC `10.0.0.0/16` criada no Console com subnets pública (`10.0.1.0/24`) e privada
      (`10.0.2.0/24`).
- [ ] IGW criado e **anexado**; rota `0.0.0.0/0 → IGW` na route table **pública** apenas.
- [ ] Entendeu por que a rota (e não o nome) define a subnet pública.
- [ ] Security group com 80/443 abertos e **22 só pro seu IP** (/32).
- [ ] Viu a tela do NAT Gateway, sabe onde ele mora (subnet pública) e **quanto custa**.
- [ ] DNS hostnames habilitado na VPC customizada.
- [ ] Recriou **tudo** via CLI (create-vpc, create-subnet, create-internet-gateway,
      create-route, authorize-security-group-ingress...).
- [ ] Inspecionou com `describe-*` e conferiu contra o diagrama.
- [ ] **Teardown completo**: as duas VPCs deletadas, zero NAT, zero Elastic IP, só a default
      VPC restante.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-03/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-03/`) e para o **Módulo 04 — Compute (EC2)** — onde finalmente vamos
colocar uma instância de verdade dentro de uma rede como a que você acabou de construir.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 3" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
