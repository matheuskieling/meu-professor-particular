# Módulo 01 — Fundamentos de Cloud & AWS (Teoria)

> Objetivo do módulo: entender **o que é computação em nuvem**, por que ela existe, como a AWS
> se organiza (regiões, zonas, serviços) e quais são os conceitos-base que você vai carregar pro
> curso inteiro — incluindo o **modelo de responsabilidade compartilhada** e como a **cobrança**
> funciona. Sem isso, o resto vira decoreba. Com isso, tudo faz sentido.

---

## 1. O que é "a nuvem", de verdade

"Cloud" não é mágica nem "o computador de outra pessoa" como diz a piada. É mais preciso dizer:

> **Computação em nuvem é o fornecimento de recursos de computação (servidores, armazenamento,
> banco de dados, rede, software) sob demanda, pela internet, com pagamento pelo uso.**

Antes da nuvem, se você queria colocar uma aplicação no ar, precisava:

1. Estimar quanta capacidade ia precisar (e quase sempre errar).
2. Comprar servidores físicos (gasto grande, antecipado — **CapEx**).
3. Esperar semanas pela entrega.
4. Alugar espaço num datacenter, energia, refrigeração, rede.
5. Contratar gente pra manter tudo isso funcionando.
6. Pagar por essa capacidade **mesmo quando ociosa**.

Com a nuvem, isso vira:

1. Abrir um site, pedir um servidor.
2. Ter o servidor em **segundos**.
3. Pagar só pelo tempo que usar (**OpEx** — despesa operacional).
4. Desligar quando não precisar mais.

### As vantagens que importam

- **Elasticidade** — você escala pra cima na Black Friday e pra baixo de madrugada, automaticamente.
- **Pague pelo uso** — sem desperdício com capacidade parada.
- **Velocidade / agilidade** — experimentar custa quase nada; errou, destrói e recomeça.
- **Alcance global** — subir infraestrutura em outro continente é questão de minutos.
- **Menos "trabalho pesado indiferenciado"** — você não cuida de ar-condicionado de datacenter;
  cuida da sua aplicação, que é o que gera valor.

---

## 2. Modelos de serviço: IaaS, PaaS, SaaS

Uma forma clássica de entender **quanto a nuvem gerencia por você** é a analogia da pizza 🍕
("Pizza as a Service"). Quanto mais "as a service", menos você administra:

| Modelo | O que é | Você gerencia | O provedor gerencia | Exemplo AWS |
|--------|---------|---------------|---------------------|-------------|
| **On-premises** | Tudo seu, no seu datacenter | Tudo | Nada | (seu próprio servidor) |
| **IaaS** (Infra as a Service) | Infra crua: máquinas, rede, disco | SO, runtime, app, dados | Hardware, virtualização, rede física | **EC2**, VPC, EBS |
| **PaaS** (Platform as a Service) | Plataforma pronta pra rodar código | Só o app e os dados | SO, runtime, escalonamento | Elastic Beanstalk, RDS, Lambda* |
| **SaaS** (Software as a Service) | Software pronto pra usar | Só o uso/config | Tudo | Gmail, Amazon WorkMail |

\* Lambda é frequentemente chamado de **FaaS / serverless** — você entrega só a função e a AWS
cuida de todo o resto (inclusive de escalar de 0 a milhares de execuções).

**Regra mental:** quanto mais você sobe na escala (IaaS → SaaS), **menos controle e menos
responsabilidade** você tem. Não existe "melhor" — existe o adequado pro caso. Neste curso você
vai transitar por todos, começando por IaaS (EC2, VPC) porque é onde os fundamentos aparecem mais claros.

---

## 3. Como a AWS se organiza no mundo: Regiões e Zonas de Disponibilidade

Este é um dos conceitos mais importantes e mais mal-entendidos. Preste atenção.

### Região (Region)

Uma **Região** é uma área geográfica do mundo onde a AWS tem infraestrutura. Exemplos:
`us-east-1` (Norte da Virgínia), `sa-east-1` (São Paulo), `eu-west-1` (Irlanda).

Pontos-chave:
- Cada região é **isolada** das outras (falha em uma não derruba a outra).
- Você **escolhe** em qual região trabalha — e isso afeta **latência**, **preço** e **conformidade legal** (ex.: LGPD/GDPR, onde os dados podem residir).
- **Nem todo serviço existe em toda região**, e os **preços variam** por região.
- Alguns recursos são **regionais** (ex.: uma VPC), outros são **globais** (ex.: IAM, Route 53, CloudFront).

> 💡 **Armadilha clássica:** você cria um recurso e depois "some". Quase sempre é porque você
> estava numa região diferente no console. O seletor de região fica no canto superior direito.

### Zona de Disponibilidade (Availability Zone — AZ)

Dentro de cada região existem várias **AZs** (normalmente 3+). Cada AZ é **um ou mais datacenters
fisicamente separados** (energia, rede e refrigeração independentes), mas conectados entre si por
links de altíssima velocidade e baixa latência.

Nomes: `us-east-1a`, `us-east-1b`, `us-east-1c`...

**Por que isso importa:** se você quer **alta disponibilidade**, distribui sua aplicação em
**múltiplas AZs**. Se um datacenter inteiro pega fogo (AZ cai), a outra AZ continua servindo.
Essa é a base de quase toda arquitetura resiliente na AWS.

### Edge Locations (bônus)

Além de regiões e AZs, a AWS tem centenas de **Edge Locations** — pontos espalhados pelo mundo
usados por serviços como **CloudFront** (CDN) para entregar conteúdo pertinho do usuário final,
reduzindo latência. Você não gerencia isso diretamente, mas é bom saber que existe.

---

## 4. Visão geral das categorias de serviço

A AWS tem 200+ serviços. Você **não** precisa conhecer todos — precisa conhecer os pilares e
saber onde procurar o resto. Mapa mental por categoria:

- **Compute** (processamento): EC2 (VMs), Lambda (funções), ECS/EKS (containers), Elastic Beanstalk.
- **Storage** (armazenamento): S3 (objetos), EBS (discos de VM), EFS (arquivos), Glacier (arquivamento).
- **Rede (Networking)**: VPC (rede privada), Route 53 (DNS), CloudFront (CDN), API Gateway, ELB (balanceadores).
- **Banco de dados**: RDS (relacional gerenciado), DynamoDB (NoSQL), Aurora, ElastiCache.
- **Segurança & Identidade**: IAM (quem pode o quê), KMS (chaves), Secrets Manager, WAF, Shield.
- **Observabilidade / Gestão**: CloudWatch (métricas/logs/alarmes), CloudTrail (auditoria), Config.
- **IaC / Deploy**: CloudFormation, CDK, CodePipeline/CodeBuild/CodeDeploy.
- **Custos**: Billing, Cost Explorer, Budgets.

Neste curso vamos percorrer os principais em profundidade. Por ora, só **reconheça as caixas** e
saiba em qual categoria cada coisa mora.

---

## 5. O Modelo de Responsabilidade Compartilhada

Talvez o conceito de **segurança** mais importante da AWS. A pergunta que ele responde é:
**"Quando algo dá errado, a culpa/responsabilidade é da AWS ou minha?"**

A divisão oficial:

- **AWS é responsável pela segurança _DA_ nuvem** (*security **of** the cloud*):
  o hardware, os datacenters, a rede física, a virtualização, a infraestrutura global.
  Você **não** precisa se preocupar se o servidor físico está trancado ou se o disco foi destruído
  corretamente ao ser descartado — isso é com a AWS.

- **Você é responsável pela segurança _NA_ nuvem** (*security **in** the cloud*):
  como você **configura e usa** os serviços. Isso inclui:
  - Gerenciamento de identidades e acessos (IAM, senhas, MFA).
  - Configuração de rede e firewall (security groups, quem pode acessar o quê).
  - Criptografia dos seus dados.
  - Patches do sistema operacional **em serviços IaaS** (ex.: no EC2, o SO é seu problema).
  - Não deixar um bucket S3 público sem querer. 😅

> ⚠️ **A grande maioria dos vazamentos de dados em nuvem não é "a AWS foi hackeada" — é cliente
> configurando errado** (bucket público, credencial vazada no GitHub, permissão ampla demais).
> Por isso o Módulo 02 (IAM & Segurança) é tão crítico.

Repare que a fronteira **muda conforme o modelo de serviço**: num serviço gerenciado como Lambda,
a AWS assume mais (inclusive o SO); num EC2 (IaaS), você assume mais. Quanto mais gerenciado, menos sobra pra você.

---

## 6. Como a AWS cobra (e como você evita sustos)

Modelo mental de precificação — três ideias que explicam quase tudo:

1. **Pague pelo que usar** — cobra por hora/segundo de compute, por GB armazenado, por GB trafegado, etc.
2. **Pague menos quando reserva** — se você se compromete com uso (Reserved Instances, Savings Plans), paga bem mais barato que o preço sob demanda (*on-demand*).
3. **Pague menos quando usa mais** — vários serviços têm preço decrescente por volume (ex.: S3).

Dimensões de custo que mais pegam iniciantes de surpresa:
- **Transferência de dados de _saída_** (data transfer *out* pra internet) é cobrada. Entrada geralmente é grátis.
- **Recursos "esquecidos ligados"** — um EC2 esquecido ligado, um NAT Gateway, um IP elástico não associado: sangram dinheiro em silêncio.
- **Serviços que cobram só por existir**, não só por uso ativo.

### Free Tier (nível gratuito)

A AWS oferece um **Free Tier** pra você aprender sem gastar. Ele tem 3 sabores:
- **Sempre grátis** (ex.: 1 milhão de requisições Lambda/mês).
- **12 meses grátis** a partir da criação da conta (ex.: 750h/mês de EC2 `t2.micro`/`t3.micro`, 5 GB de S3).
- **Trials** (testes por tempo/uso limitado).

Neste curso vamos **priorizar o Free Tier** e **sempre destruir os recursos ao final de cada prática**.

### Suas travas de segurança contra sustos (faremos na prática)

- **AWS Budgets** — cria um orçamento (ex.: US$ 1) e te avisa por e-mail quando o gasto se aproxima.
- **Billing Alerts / CloudWatch** — alarme quando a fatura estimada passa de um valor.
- **Cost Explorer** — visualiza pra onde o dinheiro está indo.

> 🎯 **Regra de ouro do curso:** *nunca* deixe um recurso pago rodando "só por garantia".
> Se a prática acabou, **teardown**. Se não sabe se algo custa, **pergunte antes de criar**.

---

## 7. Ferramentas de acesso à AWS (o que você vai usar na prática)

Existem várias portas de entrada pros mesmos serviços:

- **Management Console** — a interface web. Ótima pra explorar, entender visualmente e aprender.
- **AWS CLI** — a linha de comando. Reproduzível, automatizável, scriptável. É onde você vira produtivo.
- **SDKs** — bibliotecas pra chamar a AWS a partir de código (Python `boto3`, JS, Go, etc.).
- **IaC** (CloudFormation/Terraform/CDK) — descrever a infra como código, versionável.

**Nossa abordagem no curso:** **Console primeiro** (pra você *ver* o que acontece) e depois
**CLI** (pra você *fixar, reproduzir e automatizar*). É por aí que a prática deste módulo vai.

---

## 8. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Região | Área geográfica isolada com infraestrutura AWS. |
| AZ | Datacenter(s) isolado(s) dentro de uma região; base da alta disponibilidade. |
| IaaS/PaaS/SaaS | Níveis de "quanto a nuvem gerencia por você". |
| Responsabilidade compartilhada | AWS cuida da segurança *da* nuvem; você, *na* nuvem. |
| Free Tier | Cota gratuita pra aprender sem gastar. |
| CapEx vs OpEx | Comprar antecipado (capital) vs. pagar pelo uso (operacional). |
| Elasticidade | Escalar pra cima/baixo automaticamente conforme a demanda. |
| Console / CLI / SDK / IaC | As diferentes formas de operar a AWS. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Qual a diferença entre **Região** e **AZ**, e por que você usaria várias AZs?
2. No modelo de responsabilidade compartilhada, de quem é a culpa se um bucket S3 seu ficou público?
3. Por que EC2 é IaaS e Lambda é mais parecido com PaaS/FaaS? O que muda na sua responsabilidade?
4. Cite dois custos que costumam "pegar" iniciantes de surpresa.
5. Qual a nossa "regra de ouro" sobre recursos ligados?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
