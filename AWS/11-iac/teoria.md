# Módulo 11 — Infraestrutura como Código (IaC) (Teoria)

> Objetivo do módulo: parar de criar infraestrutura "no clique" e passar a **descrevê-la como
> código** — versionável, revisável e reproduzível. Você vai entender **por que** IaC existe,
> dominar os fundamentos de **CloudFormation** e **Terraform**, conhecer o **CDK** e sair sabendo
> **escolher a ferramenta certa** para cada situação. Este é o módulo que transforma tudo que você
> aprendeu até aqui (VPC, EC2, S3, RDS...) em artefatos de engenharia de verdade.

---

## 1. Por que Infraestrutura como Código

Até agora você criou recursos pelo Console e pela CLI. Funciona — mas pense nos problemas:

- **Irreproduzível.** Como recriar *exatamente* aquele ambiente em outra conta/região? Ninguém
  lembra de todos os cliques. "Funciona na minha conta" é o novo "funciona na minha máquina".
- **Sem histórico.** Quem mudou o security group semana passada? Por quê? Cliques não têm `git log`.
- **Sem revisão.** Uma mudança de infra feita no Console entra em produção sem ninguém olhar.
  Código de infra num repositório passa por **pull request** como qualquer outro código.
- **Drift.** Ambientes "iguais" (dev, staging, prod) vão divergindo silenciosamente com o tempo,
  até que um deploy quebra só em prod e ninguém sabe por quê.

**IaC resolve isso:** você descreve a infraestrutura desejada em **arquivos de texto**, guarda no
Git, revisa em PR, e uma ferramenta **materializa** aquilo na nuvem — sempre do mesmo jeito.

> 💡 Analogia: o Console é cozinhar de cabeça; IaC é a **receita escrita**. Com a receita, qualquer
> pessoa (ou pipeline de CI) reproduz o prato idêntico, e toda alteração fica registrada.

Benefícios em uma linha cada:

| Benefício | O que significa |
|-----------|-----------------|
| Reprodutibilidade | Mesmo template → mesmo ambiente, quantas vezes quiser (dev/staging/prod, DR em outra região). |
| Versionamento | `git log` da infraestrutura: quem, quando, o quê e por quê. |
| Revisão (PR) | Mudanças de infra passam por code review antes de existir. |
| Automação | CI/CD aplica a infra; humanos não clicam em produção. |
| Documentação viva | O código **é** a documentação — nunca desatualiza. |
| Detecção de drift | Dá pra comparar o que *deveria* existir com o que *existe*. |

---

## 2. Declarativo vs. Imperativo

Duas filosofias de descrever infraestrutura:

- **Imperativo** — você descreve **os passos**: "crie um bucket; depois crie um SG; depois abra a
  porta 443". É como um script bash com comandos `aws ...` em sequência. Você é responsável pela
  ordem, pelos erros no meio do caminho e por saber o que já existe.
- **Declarativo** — você descreve **o estado final desejado**: "deve existir um bucket X e um SG Y
  com a porta 443 aberta". A ferramenta compara o desejado com o atual e **calcula sozinha** o que
  criar, alterar ou destruir (e em que ordem, respeitando dependências).

> 💡 Analogia do GPS: imperativo é ditar "vire à esquerda, siga 200 m..."; declarativo é dizer
> **o destino** e deixar o GPS calcular a rota — inclusive recalcular se você já estiver no meio do caminho.

**CloudFormation e Terraform são declarativos.** O CDK é um híbrido interessante: você *escreve*
código imperativo (TypeScript, Python...), mas ele **gera** um template declarativo (CloudFormation).

A propriedade-chave do modelo declarativo é a **idempotência**: aplicar o mesmo código duas vezes
não duplica nada — na segunda vez, a ferramenta vê que o estado atual já bate com o desejado e não
faz nada. Scripts imperativos ingênuos criariam tudo de novo (ou quebrariam).

---

## 3. CloudFormation — a IaC nativa da AWS

**AWS CloudFormation (CFN)** é o serviço de IaC da própria AWS. Você escreve um **template**
(YAML ou JSON) e o CFN cria/atualiza/destrói os recursos como uma unidade chamada **stack**.

### 3.1 Anatomia de um template YAML

As seções principais (só `Resources` é obrigatória):

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: Bucket de exemplo do curso

Parameters:            # entradas — variam por ambiente (nomes, tamanhos, flags)
  NomeDoProjeto:
    Type: String
    Default: curso-aws

Resources:             # o coração: os recursos a existir
  MeuBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "${NomeDoProjeto}-artefatos-${AWS::AccountId}"

Outputs:               # saídas — valores úteis expostos após o deploy
  BucketArn:
    Value: !GetAtt MeuBucket.Arn
```

- **Parameters** — tornam o template reutilizável (o mesmo template vira dev *e* prod, mudando parâmetros).
- **Resources** — cada recurso tem um **ID lógico** (`MeuBucket`), um `Type` (`AWS::Serviço::Recurso`)
  e `Properties`. O CFN resolve **dependências** automaticamente (e você pode forçar com `DependsOn`).
- **Outputs** — expõem valores (ARNs, endpoints) para humanos ou para outras stacks (via `Export`).
- **Funções intrínsecas** — `!Ref` (referencia parâmetro/recurso), `!GetAtt` (atributo de recurso),
  `!Sub` (interpolação de strings). São a "cola" do template.

### 3.2 O ciclo de vida de uma stack

1. **Create stack** — você envia o template; o CFN cria os recursos na ordem certa. Cada passo vira
   um **evento** (aba Events) — é ali que você depura quando algo falha.
2. **Rollback automático** — se um recurso falha no meio da criação, o CFN **desfaz tudo** e volta
   ao estado anterior. Você não fica com "meia infraestrutura" órfã. (Dá pra desabilitar, mas o
   padrão é seguro.)
3. **Update com Change Set** — antes de aplicar uma mudança, você pode gerar um **changeset**: uma
   *prévia* do que será adicionado, modificado ou **substituído**. Revisa, e só então executa.
4. **Drift detection** — o CFN compara o que o template diz com o que existe de verdade e aponta
   recursos **modificados por fora** (alguém mexeu no Console). Drift = infraestrutura mentindo pro código.
5. **Delete stack** — destrói todos os recursos da stack de uma vez. Teardown de um comando só.

> ⚠️ **Armadilha — Replacement:** algumas mudanças (ex.: renomear um bucket) não podem ser feitas
> *in place*: o CFN **destrói e recria** o recurso ("replacement"). Num banco de dados, isso significa
> **perda de dados** se você não tiver backup. O changeset avisa (`Replacement: True`) — por isso
> **sempre** revise o changeset antes de atualizar uma stack de produção.

> 💡 O CloudFormation em si é **gratuito** — você paga apenas pelos recursos que o template cria.

---

## 4. Terraform — o padrão multi-cloud

**Terraform** (HashiCorp) é a ferramenta de IaC mais usada do mercado. Diferenças-chave em relação
ao CFN: é **open source/independente da AWS**, funciona com **centenas de provedores** (AWS, Azure,
GCP, Cloudflare, GitHub...) e usa uma linguagem própria, o **HCL**.

### 4.1 HCL e providers

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "artefatos" {
  bucket = "curso-aws-artefatos-123456789012"
  tags   = { Projeto = "curso-aws" }
}
```

- **Provider** — o plugin que sabe falar com uma API (o da AWS traduz HCL em chamadas de API).
  Baixado do registry no `terraform init`.
- **Resource** — `resource "<tipo>" "<nome_local>" { ... }`. Referências entre recursos
  (`aws_s3_bucket.artefatos.arn`) criam o **grafo de dependências** implicitamente.
- Também existem **variables** (≈ Parameters), **outputs** (≈ Outputs) e **data sources**
  (consultar coisas que já existem, ex.: a VPC default).

### 4.2 O fluxo de trabalho: init → plan → apply → destroy

| Comando | O que faz |
|---------|-----------|
| `terraform init` | Prepara o diretório: baixa providers, configura o backend do state. |
| `terraform plan` | Mostra a **prévia**: `+` criar, `~` alterar, `-/+` recriar, `-` destruir. É o "changeset" do Terraform. |
| `terraform apply` | Aplica o plano (pede confirmação). |
| `terraform destroy` | Destrói tudo que o código gerencia. Teardown de um comando. |

> 💡 **`plan` é seu melhor amigo.** Cultive o hábito: nunca dê `apply` sem ler o plan. Um `-/+`
> (destroy and recreate) num recurso com dados é o mesmo perigo do "Replacement" do CFN.

### 4.3 State — o conceito mais importante do Terraform

O Terraform guarda um **arquivo de estado** (`terraform.tfstate`) que mapeia "o que está no código"
→ "IDs reais na nuvem". É assim que ele sabe que `aws_s3_bucket.artefatos` é *aquele* bucket
específico, e o que precisa mudar no próximo `plan`.

- **State local** (padrão): um arquivo no seu diretório. Ok pra estudar **sozinho**; péssimo em equipe.
- **State remoto** (o certo em equipe): guardado num **backend** compartilhado — na AWS, o clássico
  é um **bucket S3** com **lock** (trava) para impedir dois `apply` simultâneos corrompendo o estado.
  Nas versões atuais o próprio S3 faz o lock nativamente (`use_lockfile = true`); projetos mais
  antigos usavam uma tabela **DynamoDB** para isso.

> ⚠️ **Armadilhas do state:**
> 1. O state pode conter **dados sensíveis** em texto claro (senhas geradas, endpoints). **Nunca**
>    commite `terraform.tfstate` no Git; em backend S3, criptografe e restrinja o acesso.
> 2. **Perdeu o state, perdeu o controle:** o Terraform "esquece" que os recursos existem — eles
>    ficam órfãos na nuvem e o próximo `apply` tenta criar tudo em duplicidade.
> 3. Mexer nos recursos **por fora** (Console) gera drift: o `plan` seguinte vai propor reverter a mudança.

### 4.4 Módulos

Um **módulo** é um diretório de código Terraform reutilizável — a "função" da IaC. Você define
entradas (variables) e saídas (outputs) e chama o módulo várias vezes (ex.: um módulo `vpc`
instanciado para dev e prod). Há um registry público com módulos prontos e auditados pela comunidade.

---

## 5. CDK — infraestrutura em linguagem de programação (visão geral)

O **AWS CDK** (Cloud Development Kit) deixa você definir infraestrutura em **TypeScript, Python,
Java, Go ou C#** — com loops, condicionais, classes, testes unitários e autocomplete da sua IDE.

Como funciona: seu código usa **constructs** (componentes de infra com bons padrões embutidos);
o comando `cdk synth` **sintetiza** tudo em um template CloudFormation; `cdk deploy` cria a stack.
Ou seja: **o CDK é um gerador de CloudFormation** — por baixo, é sempre uma stack CFN, com os mesmos
eventos, rollback e changesets que você já conhece.

O grande atrativo: constructs de nível alto encapsulam boas práticas — poucas linhas de CDK podem
gerar dezenas de recursos CFN corretamente configurados. O custo: mais uma camada de abstração para
entender quando algo dá errado.

---

## 6. Comparativo: CloudFormation vs. Terraform vs. CDK

| Critério | CloudFormation | Terraform | CDK |
|----------|----------------|-----------|-----|
| Linguagem | YAML/JSON (declarativo) | HCL (declarativo) | TypeScript/Python/... (imperativo → gera CFN) |
| Escopo | Só AWS | **Multi-provider** (AWS, Azure, GCP, SaaS...) | Só AWS (por baixo, CFN) |
| Estado | Gerenciado pela AWS (invisível pra você) | **Você gerencia o state** (local ou S3+lock) | Gerenciado pela AWS (via CFN) |
| Prévia de mudanças | Changesets | `terraform plan` | `cdk diff` (+ changeset) |
| Rollback em falha | Automático | Não automático (para no erro; você corrige e reaplica) | Automático (via CFN) |
| Curva de aprendizado | Média (YAML verboso) | Média (HCL simples, state exige cuidado) | Maior (linguagem + constructs + CFN por baixo) |
| Preço | Grátis (paga só os recursos) | Grátis/open core (paga só os recursos) | Grátis (paga só os recursos) |

**Como escolher (regra prática):**
- Só AWS, quer zero ferramenta extra e integração nativa (ex.: StackSets, suporte AWS)? → **CloudFormation**.
- Multi-cloud, ou quer a ferramenta com maior comunidade/mercado de trabalho? → **Terraform**.
- Time de desenvolvedores que vive em TypeScript/Python e quer abstrações e testes? → **CDK**.

> 💡 Não existe resposta única — existe contexto. O que **não** muda: os conceitos (declaratividade,
> prévia de mudanças, estado, drift, teardown) são os mesmos nas três. Aprendeu um, transfere pros outros.

---

## 7. IaC na prática profissional: o fluxo GitOps

Como isso vive numa equipe de verdade:

1. Infra descrita em código, num **repositório Git**.
2. Mudança de infra = **branch + pull request**, com o `plan`/changeset colado no PR pra revisão.
3. Aprovado → o **pipeline de CI/CD** roda o `apply`/update — humanos não aplicam da máquina local em prod.
4. Console em produção vira **somente leitura** (olhar, nunca mexer) → sem drift.
5. Ambientes (dev/staging/prod) saem do **mesmo código** com parâmetros/variables diferentes.

> ⚠️ **Armadilha cultural:** a pior situação é a híbrida — metade da infra em código, metade no
> clique. O drift vira regra e a confiança no código morre. Adotou IaC num ambiente, **tudo**
> daquele ambiente passa a nascer e morrer pelo código.

---

## 8. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| IaC | Descrever infraestrutura em arquivos de código versionáveis, que uma ferramenta materializa. |
| Declarativo | Você descreve o estado final; a ferramenta calcula os passos. |
| Idempotência | Aplicar o mesmo código N vezes produz o mesmo resultado (não duplica nada). |
| Template | O arquivo YAML/JSON do CloudFormation que descreve os recursos. |
| Stack | A unidade de deploy do CFN: os recursos criados a partir de um template, geridos juntos. |
| Changeset | Prévia do que um update de stack vai adicionar/modificar/substituir. |
| Drift | Diferença entre o que o código diz e o que existe de verdade na nuvem. |
| HCL | A linguagem declarativa do Terraform. |
| Provider | Plugin do Terraform que fala com uma API (AWS, Azure...). |
| State | O mapa do Terraform entre código e recursos reais; local ou remoto (S3 + lock). |
| Módulo | Bloco reutilizável de código Terraform, com entradas e saídas. |
| CDK / synth | Infra escrita em linguagem de programação, sintetizada (`cdk synth`) em template CFN. |
| Replacement | Mudança que força o CFN a destruir e recriar o recurso — risco de perda de dados. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Cite três problemas de criar infraestrutura "no clique" que a IaC resolve — e **como** resolve.
2. Qual a diferença entre declarativo e imperativo? Em qual categoria caem CFN e Terraform — e por
   que o CDK é um caso híbrido?
3. Pra que serve um **changeset** no CloudFormation, e por que revisar um `Replacement: True` antes
   de aplicar pode salvar seus dados?
4. O que é o **state** do Terraform, por que ele não deve ir pro Git, e por que em equipe ele deve
   ser remoto (S3) **com lock**?
5. Sua empresa usa AWS e Azure e quer uma só ferramenta de IaC. Qual você escolhe e por quê?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
