# Módulo 03 — Rede: VPC (Teoria)

> Objetivo do módulo: entender como funciona a **rede na AWS** — a VPC e todas as peças que a
> compõem: CIDR, subnets públicas/privadas, route tables, Internet Gateway, NAT Gateway,
> security groups e NACLs. Rede é o alicerce invisível: **todo EC2, RDS ou load balancer que
> você criar vai morar dentro de uma VPC**. Entender isso agora evita horas de "por que não
> conecta?" depois.

---

## 1. O que é uma VPC

**VPC (Virtual Private Cloud)** é a sua **rede privada e isolada** dentro da AWS. Pense num
condomínio fechado: a AWS é a cidade, e a VPC é o seu terreno murado — você decide as ruas
(subnets), os portões (gateways) e as regras de entrada (security groups).

Pontos-chave:

- Uma VPC é **regional**: vive numa região e **atravessa todas as AZs** dela.
- Ela é **isolada por padrão**: nada entra nem sai sem você criar os componentes pra isso.
- Toda conta já vem com uma **default VPC** por região (pra facilitar o começo — seção 4).
- Dentro da VPC, você fatia o espaço de IPs em **subnets**, cada uma presa a **uma** AZ.

---

## 2. CIDR: entendendo /16, /24 e os IPs privados

Antes das subnets, precisamos falar de endereçamento. Um bloco **CIDR** (Classless Inter-Domain
Routing) descreve uma faixa de IPs assim: `10.0.0.0/16`.

### Como ler o `/N`

Um IPv4 tem **32 bits** (4 números de 0–255). O `/N` diz: **os primeiros N bits são fixos**
(identificam a rede); os `32 − N` restantes variam (identificam os hosts).

| CIDR | Bits fixos | Bits livres | Nº de IPs | Faixa |
|------|-----------|-------------|-----------|-------|
| `10.0.0.0/16` | 16 | 16 | 65.536 | 10.0.**0.0** → 10.0.**255.255** |
| `10.0.1.0/24` | 24 | 8 | 256 | 10.0.1.**0** → 10.0.1.**255** |
| `10.0.0.0/28` | 28 | 4 | 16 | 10.0.0.0 → 10.0.0.15 |

Regra mental: **quanto MAIOR o número depois da barra, MENOR a rede** (mais bits presos).
Cada bit a menos no `/` **dobra** a quantidade de IPs.

> 💡 A AWS **reserva 5 IPs** em cada subnet (o primeiro, os 3 seguintes e o último — pra rede,
> roteador, DNS e broadcast). Uma subnet `/24` tem, na prática, **251** IPs usáveis, não 256.

### IPs privados

Dentro da VPC você usa faixas **privadas** (RFC 1918), que não existem na internet:
`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.

Padrão comum (e o que usaremos): VPC `10.0.0.0/16` com subnets `/24` dentro
(`10.0.1.0/24`, `10.0.2.0/24`, ...). Sobra espaço de sobra pra crescer.

> ⚠️ **Armadilha clássica:** escolher o mesmo CIDR em duas VPCs (ou igual ao da rede do
> escritório) e depois precisar conectá-las — IPs sobrepostos **não roteiam**. Planeje CIDRs
> únicos desde o início se um dia as redes puderem se falar.

---

## 3. Subnets: públicas vs. privadas

Uma **subnet** é uma fatia do CIDR da VPC, amarrada a **uma única AZ**. É nela que os recursos
(instâncias EC2, bancos) de fato ficam.

A distinção mais importante do módulo:

| | Subnet **pública** | Subnet **privada** |
|---|---|---|
| Definição | A route table dela tem rota pra um **Internet Gateway** | **Não** tem rota pra IGW |
| Quem mora aqui | Load balancers, bastion hosts, NAT Gateway | Aplicações, bancos de dados — o grosso |
| Recebe acesso da internet? | Sim (se tiver IP público + SG permitindo) | Nunca diretamente |
| Sai pra internet? | Sim, via IGW | Só via **NAT** (se você criar) |

> 💡 **O nome não faz a subnet ser pública.** O que define é **a rota**: existe caminho
> (`0.0.0.0/0 → igw-...`) na route table associada? É pública. Não existe? É privada.
> "Pública/privada" é consequência do roteamento, não um checkbox.

Arquitetura clássica (que montaremos na prática): o que **precisa** ser alcançado da internet
fica na pública; todo o resto (app, banco) fica na privada, protegido. Menos superfície de
ataque, princípio do least privilege aplicado à rede.

---

## 4. Default VPC vs. VPC customizada

Toda região da sua conta tem uma **default VPC** (`172.31.0.0/16`), com uma subnet pública por
AZ, IGW pronto e IP público automático nas instâncias. Ela existe pra você conseguir subir um
EC2 no primeiro dia sem estudar rede.

| | Default VPC | VPC customizada |
|---|---|---|
| Pronta pra usar | Sim | Você monta tudo |
| Subnets | Todas **públicas** | Você decide (públicas + privadas) |
| Segurança | Tudo exposto por padrão | Isolamento sob medida |
| Uso adequado | Testes rápidos, aprendizado | **Qualquer coisa séria** |

> ⚠️ Rodar banco de dados na default VPC (subnet pública, IP público) é o erro de rede mais
> comum de iniciante. Em produção: **VPC customizada, sempre.** É o que vamos construir.

---

## 5. Route tables e o Internet Gateway

### Route table (tabela de rotas)

Cada subnet está associada a **exatamente uma route table** (a *main* da VPC, se você não
associar outra). Ela decide **pra onde vai o tráfego que sai** dos recursos da subnet. Exemplo
de route table de subnet pública:

| Destination | Target | Significado |
|-------------|--------|-------------|
| `10.0.0.0/16` | `local` | Tráfego pra dentro da VPC fica na VPC (rota implícita, não removível) |
| `0.0.0.0/0` | `igw-0abc...` | Todo o resto ("qualquer IP") vai pro Internet Gateway |

A regra de escolha é **longest prefix match**: vale a rota mais específica que casar com o
destino. `0.0.0.0/0` é o "resto" (rota default), usada só quando nada mais específico casa.

### Internet Gateway (IGW)

O **IGW** é o portão da VPC pra internet: um componente redundante e escalável (você não
gerencia capacidade) que **se anexa à VPC** (1 por VPC). Ele faz a tradução entre o IP privado
da instância e o **IP público** dela.

Pra uma instância ser alcançável da internet, precisa de **4 coisas ao mesmo tempo**:
1. IGW anexado à VPC;
2. rota `0.0.0.0/0 → IGW` na route table da subnet;
3. **IP público** (ou Elastic IP) na instância;
4. security group (e NACL) permitindo o tráfego.

> 💡 Faltou qualquer um dos 4 → "timeout". Esse checklist resolve 90% dos "não consigo acessar
> minha instância".
>
> 💰 **Nota de custo (regra atual da AWS):** todo **IPv4 público custa** (~US$ 0,005/hora
> ≈ US$ 3,60/mês por IP). O Free Tier de 12 meses inclui 750 h/mês de IP público **junto com
> uma instância EC2**. Mais um motivo pra não espalhar IP público à toa.

---

## 6. NAT Gateway — saída sem entrada (⚠️ custa dinheiro)

E a subnet **privada**? Ela não tem rota pro IGW — mas o servidor de app dela precisa baixar
pacotes, chamar APIs externas... Como sair sem ficar exposto?

**NAT Gateway**: um serviço gerenciado que mora numa **subnet pública** (com um Elastic IP) e
faz *Network Address Translation* — deixa quem está na subnet privada **iniciar** conexões de
saída, mas **bloqueia qualquer conexão iniciada de fora**. Mão única.

Fluxo: instância privada → route table da privada tem `0.0.0.0/0 → nat-...` → NAT (na subnet
pública) → IGW → internet. A volta da resposta é permitida; uma conexão **nova** vinda de fora,
não.

> ⚠️ **CUSTO — atenção máxima:** NAT Gateway **NÃO tem Free Tier**. Cobra
> **~US$ 0,045/hora (≈ US$ 32/mês) + ~US$ 0,045 por GB processado**, por AZ. É o campeão de
> "sangria silenciosa" em conta de estudante. Na prática deste módulo vamos **apenas mostrar
> onde ele seria criado** — ou, se você quiser criar pra ver funcionando, **destruir
> imediatamente** (e o Elastic IP junto).

> 💡 Alternativas que você verá no mundo real: NAT instance (EC2 fazendo NAT — barato e
> trabalhoso), e **VPC endpoints** pra falar com serviços AWS (S3, DynamoDB) sem sair pra
> internet — de graça no caso dos *gateway endpoints*.

---

## 7. Security Groups vs. NACLs — o firewall em duas camadas

As duas camadas de firewall da VPC, e a diferença **stateful vs. stateless** que cai em toda
prova e em toda entrevista:

| | **Security Group (SG)** | **Network ACL (NACL)** |
|---|---|---|
| Atua em | **Instância** (na verdade, na interface de rede/ENI) | **Subnet** (na borda) |
| Estado | **Stateful**: resposta de conexão permitida passa automaticamente | **Stateless**: ida e volta avaliadas separadamente |
| Regras | **Só Allow** (o que não é permitido, é negado) | Allow **e** Deny, avaliadas **em ordem numérica** |
| Padrão | Entrada: nega tudo · Saída: permite tudo | Default NACL: permite tudo nos dois sentidos |
| Alcance de regra | Pode referenciar **outro SG** como origem | Só CIDRs |

**Stateful na prática:** você libera a porta 443 de entrada no SG; a **resposta** sai sem
precisar de regra de saída — o SG "lembra" da conexão. Na NACL (stateless), você precisaria
liberar a entrada na 443 **e** a saída nas *ephemeral ports* (1024–65535), senão a resposta
morre no caminho.

**Referenciar SG como origem** é o superpoder: em vez de "libere o IP do app", você diz
"o SG do banco aceita 5432 **vindo do SG do app**". As instâncias podem mudar de IP à vontade
— a regra continua valendo. É assim que se desenha rede na AWS.

> 💡 **Na prática do dia a dia:** você vai trabalhar 95% do tempo com SGs. As NACLs ficam no
> default (permite tudo) na maioria das arquiteturas, reservadas pra bloqueios grosseiros na
> borda da subnet (ex.: banir uma faixa de IPs atacante).

> ⚠️ **Armadilha clássica:** "liberei a porta no SG e não conecta". Cheque o resto do caminho:
> route table, IP público, NACL, e o firewall do próprio SO da instância.

---

## 8. DNS na VPC e VPC Peering (visão geral)

### DNS na VPC

Toda VPC tem um **resolvedor DNS embutido** (o "Route 53 Resolver", no IP base da VPC + 2 —
ex.: `10.0.0.2`). Dois atributos da VPC controlam o comportamento:

- **enableDnsSupport** — habilita a resolução DNS dentro da VPC (default: on).
- **enableDnsHostnames** — dá nomes DNS (`ec2-x-x-x-x.compute-1.amazonaws.com`) a instâncias
  com IP público (default: **off** em VPC customizada, on na default VPC).

> 💡 Detalhe elegante: o DNS público de uma instância, resolvido **de dentro** da VPC, retorna
> o **IP privado** dela (tráfego fica interno, sem custo de saída); de fora, retorna o público.

### VPC Peering (visão geral)

**Peering** conecta duas VPCs (mesma conta ou não, mesma região ou não) pra que conversem por
IP privado, sem passar pela internet. Essencial saber:

- Exige **CIDRs que não se sobreponham** (lembra da armadilha da seção 2?).
- Você precisa **adicionar rotas** nas route tables dos dois lados (o peering sozinho não roteia).
- **Não é transitivo**: A↔B e B↔C **não** dá A↔C. Cada par precisa do seu peering — com muitas
  VPCs isso vira malha; a solução moderna é o **Transit Gateway** (hub central; só o conceito
  por ora).

---

## 9. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| VPC | Sua rede privada e isolada dentro de uma região da AWS. |
| CIDR | Notação de faixa de IPs (`10.0.0.0/16`); maior `/N` = rede menor. |
| Subnet | Fatia da VPC presa a uma AZ; onde os recursos moram. |
| Subnet pública/privada | Tem/não tem rota pra IGW na route table. |
| Route table | Decide pra onde vai o tráfego de saída de uma subnet. |
| IGW | Portão da VPC pra internet (1 por VPC, mão dupla). |
| NAT Gateway | Saída-sem-entrada pra subnets privadas; **pago por hora + GB**. |
| Security Group | Firewall **stateful** da instância; só regras Allow. |
| NACL | Firewall **stateless** da subnet; Allow/Deny em ordem numérica. |
| VPC Peering | Liga duas VPCs por IP privado; não transitivo; CIDRs não podem colidir. |
| Ephemeral ports | Portas altas (1024–65535) usadas pelas respostas; importam nas NACLs. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Quantos IPs tem um `/24`? E por que na AWS "sobram" só 251 usáveis?
2. O que **de fato** torna uma subnet pública? (Dica: não é o nome nem um checkbox.)
3. Cite as **4 condições** pra uma instância ser alcançável da internet.
4. Seu app na subnet privada precisa baixar atualizações. Qual componente resolve, onde ele
   mora, e por que é preciso cuidado com o custo dele?
5. Explique **stateful vs. stateless** usando o exemplo de liberar a porta 443 num SG vs.
   numa NACL.

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
