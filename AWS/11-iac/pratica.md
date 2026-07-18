# Módulo 11 — Infraestrutura como Código (Prática Guiada)

> Objetivo desta prática: criar **a mesma infraestrutura** (um bucket S3 + um security group) de
> duas formas — primeiro com **CloudFormation** (template → stack → changeset → delete), depois com
> **Terraform** (init → plan → apply → destroy). Ao final você terá vivido o ciclo completo de IaC
> nas duas ferramentas e visto o **state** do Terraform de perto.
>
> **Abordagem:** Console primeiro (pra ver a stack acontecendo), CLI/terminal depois (pra fixar).
>
> ⏱️ Tempo estimado: 60–90 min. 💵 Custo: **US$ 0** — CloudFormation e Terraform são gratuitos;
> bucket S3 vazio e security group não custam nada. Mesmo assim, faremos o **teardown completo**.

---

## ⚠️ Antes de começar — leia isto

- Tudo nesta prática usa recursos **gratuitos** (bucket vazio, SG, stacks). O ritual de teardown
  continua **obrigatório** — é o hábito que vale.
- Trabalhe na região **us-east-1** (como no resto do curso).
- Crie uma pasta de trabalho **fora** deste repositório (ex.: `~/lab-iac/`) — o state do Terraform
  e artefatos locais não devem ser commitados aqui.
- Nomes de bucket S3 são **globais e únicos**: nos exemplos, troque `SEUNOME` por algo seu
  (minúsculas, sem espaços).

```bash
mkdir -p ~/lab-iac/cfn ~/lab-iac/tf && cd ~/lab-iac
```

---

## Parte A — CloudFormation: escrever o template

### Passo 1 — Criar o template YAML

Crie o arquivo `~/lab-iac/cfn/lab.yaml` com este conteúdo:

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: Lab do Modulo 11 - bucket S3 + security group via CloudFormation

Parameters:
  NomeDoProjeto:
    Type: String
    Default: lab-iac
    Description: Prefixo usado nos nomes e tags dos recursos

Resources:
  BucketDoLab:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "${NomeDoProjeto}-SEUNOME-${AWS::AccountId}"
      Tags:
        - Key: Projeto
          Value: !Ref NomeDoProjeto

  SgDoLab:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: SG do lab de IaC - permite HTTPS de entrada
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0
      Tags:
        - Key: Projeto
          Value: !Ref NomeDoProjeto

Outputs:
  NomeDoBucket:
    Description: Nome do bucket criado
    Value: !Ref BucketDoLab
  ArnDoBucket:
    Description: ARN do bucket
    Value: !GetAtt BucketDoLab.Arn
  IdDoSg:
    Description: ID do security group
    Value: !GetAtt SgDoLab.GroupId
```

> **Leia o template antes de seguir.** Identifique: o parâmetro, os dois recursos (com seus IDs
> lógicos `BucketDoLab` e `SgDoLab`), as funções `!Sub`, `!Ref` e `!GetAtt`, e os outputs.
> ⚠️ Não esqueça de trocar `SEUNOME` no `BucketName`.

---

## Parte B — CloudFormation: criar a stack (Console)

### Passo 2 — Create stack
1. Console → serviço **CloudFormation** → **Create stack** → *With new resources (standard)*.
2. **Upload a template file** → escolha o seu `lab.yaml` → **Next**.
3. Stack name: `lab-iac`. Veja que o parâmetro `NomeDoProjeto` aparece preenchido com o default → **Next**.
4. Mantenha os padrões → **Next** → **Submit**.

### Passo 3 — Assistir aos eventos
1. Na stack, abra a aba **Events** e atualize: veja cada recurso passando por
   `CREATE_IN_PROGRESS` → `CREATE_COMPLETE`, até a stack ficar `CREATE_COMPLETE`.
2. Abra a aba **Resources**: os IDs lógicos (`BucketDoLab`, `SgDoLab`) mapeados pros **IDs físicos**
   reais (nome do bucket, `sg-...`).
3. Abra a aba **Outputs**: o nome, o ARN do bucket e o ID do SG que declaramos.

> 🎯 Este é o coração do CFN: um arquivo virou infraestrutura real, com log de cada passo.
> Se algo falhar (ex.: nome de bucket já existente no mundo), veja o motivo em Events — o CFN faz
> **rollback automático** e nada fica pela metade.

### Passo 4 — Update com changeset
1. Edite o `lab.yaml`: no `SgDoLab`, adicione uma segunda regra de ingress (porta 80):
   ```yaml
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
   ```
2. Na stack → **Stack actions** → **Create change set for current stack** → *Replace current
   template* → upload do YAML editado → Next... → **Create change set**.
3. **Revise a prévia:** deve mostrar `Modify` no `SgDoLab` com **Replacement: False** (mudança
   in-place, sem destruir). O bucket nem aparece — não mudou.
4. **Execute change set** e acompanhe em Events (`UPDATE_IN_PROGRESS` → `UPDATE_COMPLETE`).

> 💡 Ritual profissional: **nunca** atualize stack importante sem ler o changeset. É ali que um
> `Replacement: True` inesperado (destruir e recriar) é pego **antes** de causar estrago.

### Passo 5 — (Opcional) Provocar um drift
1. No Console **EC2 → Security Groups**, ache o SG da stack e **remova manualmente** a regra da porta 80.
2. Na stack → **Stack actions** → **Detect drift** → depois **View drift results**: o `SgDoLab`
   aparece como `MODIFIED` — a nuvem divergiu do template.
3. É exatamente por isso que "mexer por fora" é proibido em ambientes com IaC. (O update seguinte
   pelo template reconciliaria a regra.)

---

## Parte C — CloudFormation pela CLI (fixar)

Os mesmos passos, agora reproduzíveis por script. Primeiro, delete a stack do Console para recriar
pela CLI (ou use outro nome de stack **e** outro `NomeDoProjeto`, por causa do nome único do bucket):

```bash
aws cloudformation delete-stack --stack-name lab-iac
aws cloudformation wait stack-delete-complete --stack-name lab-iac
```

Criar de novo, agora pela CLI:

```bash
cd ~/lab-iac/cfn
aws cloudformation create-stack \
  --stack-name lab-iac-cli \
  --template-body file://lab.yaml \
  --parameters ParameterKey=NomeDoProjeto,ParameterValue=lab-iac-cli

aws cloudformation wait stack-create-complete --stack-name lab-iac-cli
```

Ver eventos e outputs:

```bash
aws cloudformation describe-stack-events --stack-name lab-iac-cli \
  --query "StackEvents[].{Recurso:LogicalResourceId,Status:ResourceStatus}" --output table

aws cloudformation describe-stacks --stack-name lab-iac-cli \
  --query "Stacks[0].Outputs" --output table
```

> 💡 Repare como a CLI torna tudo **scriptável**: esses comandos poderiam estar num pipeline de CI.

---

## Parte D — Terraform: instalar e escrever o main.tf

### Passo 6 — Instalar o Terraform

Verifique se já tem:
```bash
terraform -version
```
Se não tiver (Arch Linux): `sudo pacman -S terraform` (ou `opentofu`, o fork aberto — comandos
idênticos). Outros SOs: <https://developer.hashicorp.com/terraform/install>. Confirme com
`terraform -version` antes de seguir.

### Passo 7 — Escrever o main.tf

Crie `~/lab-iac/tf/main.tf` — o **equivalente** ao template CFN:

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

variable "nome_do_projeto" {
  type    = string
  default = "lab-iac-tf"
}

data "aws_caller_identity" "atual" {}

resource "aws_s3_bucket" "lab" {
  bucket = "${var.nome_do_projeto}-SEUNOME-${data.aws_caller_identity.atual.account_id}"
  tags   = { Projeto = var.nome_do_projeto }
}

resource "aws_security_group" "lab" {
  description = "SG do lab de IaC via Terraform - HTTPS de entrada"

  ingress {
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Projeto = var.nome_do_projeto }
}

output "nome_do_bucket" {
  value = aws_s3_bucket.lab.bucket
}

output "arn_do_bucket" {
  value = aws_s3_bucket.lab.arn
}

output "id_do_sg" {
  value = aws_security_group.lab.id
}
```

> Compare mentalmente com o YAML: `variable` ≈ Parameters, `resource` ≈ Resources, `output` ≈
> Outputs. O `data` é novidade: **consulta** algo existente (aqui, o ID da sua conta) sem criar nada.
> ⚠️ Troque `SEUNOME` de novo.

---

## Parte E — Terraform: init → plan → apply → destroy

### Passo 8 — init e plan
```bash
cd ~/lab-iac/tf
terraform init
```
> O `init` baixou o **provider AWS** (veja a pasta `.terraform/` criada) e preparou o backend de
> state (local, por padrão).

```bash
terraform plan
```
> Leia o plan com calma: `+ aws_s3_bucket.lab` e `+ aws_security_group.lab` — **2 to add, 0 to
> change, 0 to destroy**. Nada aconteceu na AWS ainda; é só a prévia (o "changeset" do Terraform).

### Passo 9 — apply e inspecionar o state
```bash
terraform apply     # revise e digite: yes
```
Confirme que existe de verdade:
```bash
aws s3 ls | grep lab-iac-tf
```
Agora o **state**:
```bash
ls -la               # repare no terraform.tfstate
terraform state list # os recursos que o TF gerencia
terraform state show aws_s3_bucket.lab
```
> Abra o `terraform.tfstate` num editor e espie: é um JSON mapeando seu código → IDs reais.
> **Por isso ele nunca vai pro Git** (pode conter segredos) e, em equipe, vive em S3 com lock.

### Passo 10 — alterar e ver o diff
Edite o `main.tf`: adicione um segundo bloco `ingress` no SG (porta 80, igual fizemos no CFN):
```hcl
  ingress {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }
```
```bash
terraform plan
```
> O diff mostra `~ aws_security_group.lab` (til = **update in-place**): só a regra nova entra.
> Se fosse `-/+`, seria destruir-e-recriar — o alerta vermelho pra ler duas vezes.
```bash
terraform apply     # yes
```

### Passo 11 — destroy
```bash
terraform destroy   # revise: 2 to destroy — e digite: yes
aws s3 ls | grep lab-iac-tf   # não deve retornar nada
```
> Um comando desfez tudo que o código criou. Esse é o teardown no mundo IaC: **confiável e completo**.

---

## Parte F — 🔥 Teardown (obrigatório)

Mesmo com custo zero, zere tudo:

```bash
# 1. Stack do CloudFormation (CLI)
aws cloudformation delete-stack --stack-name lab-iac-cli
aws cloudformation wait stack-delete-complete --stack-name lab-iac-cli

# 2. Se a stack 'lab-iac' do Console ainda existir, delete também
aws cloudformation delete-stack --stack-name lab-iac

# 3. Terraform — se ainda não destruiu no Passo 11
cd ~/lab-iac/tf && terraform destroy

# 4. Conferir que não sobrou nada
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --output table
aws s3 ls | grep lab-iac
```

O último comando de cada verificação deve vir **vazio** (ou sem as stacks do lab).

---

## ✅ Checklist de conclusão do módulo

- [ ] Escreveu um template CFN com Parameters, Resources (bucket + SG) e Outputs.
- [ ] Criou a stack pelo Console e acompanhou os **Events** até `CREATE_COMPLETE`.
- [ ] Viu os Outputs e o mapeamento ID lógico → ID físico em Resources.
- [ ] Fez um update via **changeset**, revisando a prévia antes de executar.
- [ ] (Opcional) Provocou e detectou um **drift**.
- [ ] Recriou e consultou a stack pela **CLI**.
- [ ] `terraform -version` funcionando; escreveu o `main.tf` equivalente.
- [ ] Rodou `init` → `plan` → `apply` e **inspecionou o state**.
- [ ] Alterou o código, leu o **diff** do plan e aplicou.
- [ ] `terraform destroy` + delete das stacks — **teardown completo confirmado**.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-11/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-11/`) e para o **Módulo 12 — Observabilidade**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 11" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
