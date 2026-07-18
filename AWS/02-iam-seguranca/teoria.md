# Módulo 02 — Conta, IAM & Segurança (Teoria)

> Objetivo do módulo: dominar o **IAM (Identity and Access Management)** — o serviço que responde
> à pergunta mais importante da AWS: **"quem pode fazer o quê, em qual recurso?"**. Você vai
> entender users, groups, roles e policies a fundo (incluindo o JSON delas), aplicar **least
> privilege** de verdade e fechar as travas de billing. Errar aqui é a causa nº 1 de vazamentos
> e sustos na nuvem — por isso este módulo vem antes de criar qualquer infraestrutura.

---

## 1. Root vs. usuários IAM — por que o root fica no cofre

Quando você criou a conta (Módulo 01), nasceu junto o **usuário root**: o e-mail + senha do
cadastro. Ele é especial por um motivo simples e assustador:

> **O root pode TUDO e não pode ser restringido.** Nenhuma policy consegue limitar o root.

Algumas ações são **exclusivas do root** (fechar a conta, mudar o plano de suporte, alterar
certas configurações de billing e de conta) — pra isso ele existe. Para todo o resto, ele é
um risco desnecessário: se a senha vaza, o atacante tem a conta inteira e o seu cartão.

Regras práticas:

- **Root:** MFA ativado (já fizemos), **sem access keys** (nunca crie chaves pro root), usado
  só para as poucas tarefas que exigem root.
- **Dia a dia:** usuários IAM (ou, melhor ainda, o IAM Identity Center — seção 8) com apenas
  as permissões necessárias.

> ⚠️ **Armadilha clássica:** criar access keys para o root "pra facilitar". É a pior credencial
> possível pra vazar: poder irrestrito e irrevogável por policy. Se existir, delete.

---

## 2. Os quatro blocos do IAM: users, groups, roles, policies

O IAM é um serviço **global** (não pertence a uma região) e **gratuito**. Ele tem quatro peças:

| Peça | O que é | Analogia |
|------|---------|----------|
| **User** | Uma identidade permanente para uma pessoa ou aplicação, com credenciais próprias (senha e/ou access keys). | O crachá com foto de um funcionário. |
| **Group** | Um agrupador de users. Policies anexadas ao grupo valem para todos os membros. **Não é uma identidade** — não faz login nem tem credencial. | O departamento: "todos do Financeiro entram na sala X". |
| **Role** | Uma identidade **assumível temporariamente**, sem credenciais fixas. Quem assume recebe **credenciais temporárias** que expiram sozinhas. | O colete de visitante: qualquer um autorizado veste, usa e devolve. |
| **Policy** | Documento **JSON** que diz o que é permitido/negado. Sozinha não faz nada — precisa estar **anexada** a um user, group ou role. | O regulamento que diz o que cada crachá/colete abre. |

Modelo mental de gestão que vamos usar no curso:

> **Permissões vão em policies → policies anexam em groups (pessoas) ou roles (serviços/acessos
> temporários) → users entram em groups.** Anexar policy direto num user é exceção, não regra —
> com 30 usuários, gerenciar permissão um a um vira caos.

---

## 3. Anatomia de uma policy (o JSON que manda em tudo)

Toda policy é um JSON com uma lista de **statements**. Exemplo real, que dá acesso somente-leitura
a um bucket S3 específico:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LeituraDoBucketRelatorios",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::relatorios-empresa",
        "arn:aws:s3:::relatorios-empresa/*"
      ]
    }
  ]
}
```

Campo a campo:

| Campo | Significado |
|-------|-------------|
| `Version` | Versão da **linguagem** de policy. Use sempre `"2012-10-17"` (é a atual — não é a data de hoje!). |
| `Sid` | Identificador opcional do statement, só pra documentação. |
| `Effect` | `Allow` ou `Deny`. |
| `Action` | Quais chamadas de API: `servico:Operacao` (ex.: `s3:GetObject`, `ec2:StartInstances`). Aceita curinga: `s3:Get*`, `s3:*`. |
| `Resource` | Em **quais recursos** (via ARN) a ação vale. `"*"` = todos — quase sempre amplo demais. |
| `Condition` | (Opcional) condições extras: IP de origem, MFA presente, tags, horário, etc. |

### ARN — o "endereço completo" de um recurso

**ARN (Amazon Resource Name)** identifica unicamente qualquer recurso na AWS. Formato:

```
arn:partition:service:region:account-id:resource
arn:aws:s3:::relatorios-empresa            ← S3 é global: região e conta ficam vazias
arn:aws:iam::123456789012:user/joao        ← IAM é global: região vazia
arn:aws:ec2:us-east-1:123456789012:instance/i-0abc123def456
```

> 💡 Repare nos `::` "vazios" — serviços globais (IAM, S3 no nome do bucket) omitem região
> e/ou conta, mas os dois-pontos ficam lá marcando a posição. Ler ARNs vira segunda natureza.

> 💡 **`relatorios-empresa` vs `relatorios-empresa/*`:** o primeiro é o **bucket em si**
> (necessário pra `ListBucket`); o segundo são os **objetos dentro dele** (necessário pra
> `GetObject`). Esquecer um dos dois é erro clássico que gera "Access Denied misterioso".

---

## 4. Como a AWS decide: a lógica de avaliação de policies

Quando você faz qualquer chamada de API, a AWS avalia **todas** as policies aplicáveis e decide.
A lógica, na ordem:

1. **Por padrão, tudo é negado** (*implicit deny*). Sem policy dizendo Allow, a resposta é não.
2. Se **alguma** policy aplicável tem um `Allow` para aquela ação naquele recurso → permitido...
3. ...**a menos que** exista um `Deny` explícito em qualquer lugar. **Deny explícito SEMPRE
   vence**, não importa quantos Allows existam.

Em uma frase pra decorar:

> **Deny explícito > Allow > Deny implícito (o padrão).**

Consequências práticas:

- Permissões de user + groups + policies de recurso **se somam** (união dos Allows).
- Um `Deny` explícito serve como **trava de segurança inquebrável** — ex.: "ninguém deleta
  nada em produção, nem quem tem AdministratorAccess de resto".
- Se algo dá `AccessDenied` e você jura que tem Allow, procure um Deny explícito (ou um
  recurso/ação que não bate com o ARN do Allow).

> 💡 Existem outras camadas (permissions boundaries, SCPs de organização, session policies) que
> funcionam como **filtros**: a permissão efetiva é a **interseção** delas com as policies de
> identidade. Só saiba que existem; veremos quando forem necessárias.

---

## 5. Policies gerenciadas vs. inline (e as da AWS vs. as suas)

Três formas de uma policy existir:

| Tipo | O que é | Quando usar |
|------|---------|-------------|
| **AWS managed** | Criada e mantida pela AWS (ex.: `AdministratorAccess`, `ReadOnlyAccess`, `AmazonS3ReadOnlyAccess`). | Começo rápido, casos comuns. Costumam ser mais amplas do que você precisa. |
| **Customer managed** | Criada por **você**, reutilizável, versionada (dá pra voltar versão). | O padrão pra permissões sob medida. É o que vamos criar na prática. |
| **Inline** | Embutida **dentro** de um único user/group/role. Vive e morre com ele; não é reutilizável. | Exceções raras, quando a policy só faz sentido colada naquela identidade. |

> 💡 **Preferência do curso:** customer managed anexada a groups/roles. Inline dificulta
> auditoria ("onde mais essa permissão existe?") e não se reaproveita.

---

## 6. Least privilege e MFA — os dois hábitos que evitam desastres

### Least privilege (privilégio mínimo)

O princípio: **cada identidade deve ter exatamente as permissões de que precisa — nada a mais.**

Na prática:

- Comece **negando tudo** (o padrão já é esse) e conceda o mínimo; vá **adicionando** conforme
  a necessidade real, em vez de dar `*` e "depois eu restrinjo" (nunca restringe).
- Prefira ações específicas (`s3:GetObject`) a curingas (`s3:*`), e ARNs específicos a `"*"`.
- Revise periodicamente: o IAM mostra **quando cada permissão/serviço foi usado pela última
  vez** (last accessed) — permissão nunca usada é candidata a remoção.
- O seu user `admin-*` com `AdministratorAccess` do Módulo 01 é uma concessão temporária de
  quem está **aprendendo sozinho na própria conta**. Em empresa, ninguém opera assim no dia a dia.

### MFA em todo lugar que importa

MFA (autenticação multifator) você já ativou no root. Idealmente, também no seu user IAM com
acesso ao console. Bônus avançado: policies podem **exigir** MFA via
`Condition: {"Bool": {"aws:MultiFactorAuthPresent": "true"}}` — sem o segundo fator, nem com a
senha certa a ação passa.

### Rotação e higiene de credenciais

- **Access keys são senhas de longa duração** — o elo mais fraco. Rotacione periodicamente
  (crie a nova → troque na máquina → desative a antiga → confirme → delete).
- **Nunca** em código, commit, variável hardcoded, print de tela. O padrão de vazamento é
  sempre o mesmo: chave commitada no GitHub → bots acham em minutos → mineração de cripto na
  sua conta.
- Melhor que rotacionar: **não ter chave de longa duração** — usar roles (próxima seção).

---

## 7. Roles — identidade temporária (o jeito certo de dar permissão a serviços)

Pergunta que define o assunto: **como uma instância EC2 acessa um bucket S3?** A resposta errada
(e tristemente comum) é "coloca as access keys num arquivo dentro da instância". A resposta certa:

> **Crie uma role com as permissões necessárias e deixe a instância assumi-la.**

Como funciona:

1. A role tem **duas** policies: a **trust policy** (quem PODE assumir — ex.: o serviço
   `ec2.amazonaws.com`) e as **permission policies** (o que quem assumir PODE fazer).
2. Quem assume chama o **STS** (Security Token Service) — `sts:AssumeRole` — e recebe
   **credenciais temporárias** (access key + secret + **session token**) com prazo de validade.
3. Expirou, acabou. Nada de chave eterna pra vazar.

Casos de uso de roles:

- **Serviço → serviço:** EC2 acessando S3, Lambda escrevendo no DynamoDB (todo serviço que age
  em seu nome usa role).
- **Cross-account:** conta B assume role na conta A para acessar recursos dela — sem criar user.
- **Humanos via federação/Identity Center:** você loga no seu provedor de identidade e recebe
  uma role temporária na AWS.
- **Elevação temporária:** user comum assume uma role de admin só quando precisa (e isso fica
  auditado no CloudTrail).

> 💡 **Regra de bolso:** *pessoa permanente = user (num group); serviço ou acesso temporário =
> role.* Se você está digitando access keys dentro de um servidor, pare: existe uma role pra isso.

---

## 8. IAM Identity Center (visão geral)

O **IAM Identity Center** (ex-AWS SSO) é a recomendação atual da AWS para **acesso humano**:

- Login único (SSO) num portal, com um diretório central de pessoas (ou integrado a
  Entra ID/Google Workspace/Okta).
- Por baixo, todo acesso vira **role com credenciais temporárias** — ninguém tem access key
  de longa duração.
- Feito para **múltiplas contas** (AWS Organizations): você define "grupo X tem permission set
  Y nas contas Z" num lugar só.
- A própria CLI suporta: `aws configure sso` / `aws sso login` — sem secret salva em `~/.aws`.

Para a nossa conta de estudos, o user IAM clássico basta e simplifica. Mas em qualquer ambiente
com mais de uma pessoa ou conta, **Identity Center é o caminho** — e é o que você vai encontrar
nas empresas. Por ora, guarde o conceito.

---

## 9. Billing: alertas e onde olhar (fechando as travas do Módulo 01)

Segurança inclui **segurança financeira**. Recapitulando e completando o que começamos:

- **AWS Budgets** — orçamento com alerta por e-mail (você criou o zero-spend no M01). Dá pra
  alertar no gasto **real** e no **previsto** (forecast).
- **Billing alerts via CloudWatch** — alarme sobre a métrica de cobrança estimada (exige
  habilitar *Receive Billing Alerts* nas preferências de billing; a métrica vive em `us-east-1`).
- **Cost Explorer** — o "extrato" navegável: gasto por serviço, por dia, por tag.
- **Acesso ao billing por users IAM:** por padrão, só o root vê billing. Ative
  *IAM user and role access to Billing information* (ação de root, nas configurações da conta)
  para o seu user admin enxergar custos sem precisar do root.
- **Free Tier alerts** — a AWS avisa por e-mail quando você se aproxima dos limites do Free Tier
  (ative nas preferências de billing, se ainda não está).

---

## 10. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Root | Identidade suprema da conta; irrestringível; MFA + cofre. |
| IAM User | Identidade permanente com credenciais próprias (pessoa ou app legada). |
| Group | Agrupador de users para anexar policies em lote; não faz login. |
| Role | Identidade assumível com credenciais **temporárias**; ideal para serviços. |
| Policy | JSON com statements Allow/Deny que define permissões. |
| ARN | Nome único e completo de um recurso (`arn:aws:serviço:região:conta:recurso`). |
| Trust policy | A policy da role que define **quem pode assumi-la**. |
| STS | Serviço que emite credenciais temporárias (`sts:AssumeRole`, `get-caller-identity`). |
| Least privilege | Conceder o mínimo necessário, e nada além. |
| Managed vs. inline | Policy reutilizável (da AWS ou sua) vs. embutida numa única identidade. |
| Identity Center | SSO da AWS: acesso humano via roles temporárias, multi-conta. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Por que o root não deve ter access keys, e para que ele ainda serve?
2. Um user pertence a dois groups: um dá `Allow s3:*` e o outro tem `Deny s3:DeleteObject`.
   Ele consegue deletar um objeto? Por quê?
3. Qual a diferença entre a **trust policy** e as **permission policies** de uma role?
4. Por que dar acesso ao S3 para uma instância EC2 via **role** é melhor do que colocar
   access keys dentro da instância?
5. No JSON de policy, o que muda entre `Resource: "arn:aws:s3:::meu-bucket"` e
   `Resource: "arn:aws:s3:::meu-bucket/*"` — e por que muitas vezes você precisa dos dois?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
