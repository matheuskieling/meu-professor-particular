# Módulo 01 — Fundamentos de Cloud & AWS (Prática Guiada)

> Objetivo desta prática: sair do zero e ter um **ambiente de trabalho AWS funcional e seguro** —
> conta criada, protegida com MFA, com travas de custo, e a **AWS CLI** configurada e testada.
> Ao final você vai rodar seus primeiros comandos reais e **explorar regiões/AZs** na prática.
>
> **Abordagem:** Console web primeiro (pra ver), CLI depois (pra fixar). Cada passo explica o *porquê*.
>
> ⏱️ Tempo estimado: 45–60 min. 💵 Custo: **US$ 0** se seguir o Free Tier e o teardown.

---

## ⚠️ Antes de começar — leia isto

- Criar conta exige **cartão de crédito** (a AWS faz uma pequena cobrança de verificação, ~US$ 1,
  estornada). Isso é normal.
- Vamos configurar **alertas de orçamento logo no início** pra você nunca ser surpreendido.
- **Nada de credencial neste repositório.** As chaves ficam só na sua máquina (`~/.aws/`), que já
  está no `.gitignore`.

---

## Parte A — Criar e proteger a conta (Console)

### Passo 1 — Criar a conta AWS
1. Acesse <https://aws.amazon.com/> → **Create an AWS Account**.
2. Informe e-mail, nome da conta e siga o cadastro (cartão + verificação por telefone).
3. Escolha o plano de suporte **Basic (Free)**.

> A conta que você acabou de criar tem um usuário especial: o **root** (o e-mail que você cadastrou).
> Ele pode **tudo** e não dá pra restringir. Por isso: use o root o mínimo possível.

### Passo 2 — Ativar MFA no usuário root (crítico)
1. No Console, canto superior direito → nome da conta → **Security credentials**.
2. Em **Multi-factor authentication (MFA)** → **Assign MFA device**.
3. Use um app autenticador (Google Authenticator, Authy, etc.) → escaneie o QR → confirme dois códigos.

> **Por quê:** o root é a chave-mestra da sua conta e do seu cartão. Sem MFA, uma senha vazada =
> desastre financeiro. Isso é *você* cumprindo sua parte no **modelo de responsabilidade compartilhada**.

### Passo 3 — Criar um orçamento (AWS Budgets)
1. Busque **Billing and Cost Management** → **Budgets** → **Create budget**.
2. Template **Zero spend budget** (avisa a qualquer gasto) *ou* um budget de custo de **US$ 1**.
3. Coloque seu e-mail pra receber alertas.

> **Por quê:** essa é sua rede de segurança. Se algo começar a custar, você fica sabendo no mesmo dia.

### Passo 4 — Explorar Regiões e AZs (fixar a teoria)
1. No canto superior direito, abra o **seletor de região**. Veja a lista (ex.: `us-east-1`, `sa-east-1`).
2. Troque para **South America (São Paulo) sa-east-1** e repare que a URL/contexto muda.
3. Volte para **US East (N. Virginia) us-east-1** — é onde faremos a maioria das práticas (mais
   serviços, mais barato, e onde recursos globais "moram").

> 🎯 Lembre da armadilha: recurso "sumido" quase sempre é **região errada** no seletor.

---

## Parte B — Criar um usuário IAM pra você (Console)

Vamos parar de usar o root. Você vai criar um usuário administrativo pro dia a dia.

> Prévia do Módulo 02. Aqui fazemos o mínimo pra você operar com segurança; a fundo vem depois.

### Passo 5 — Criar usuário IAM
1. Console → serviço **IAM** → **Users** → **Create user**.
2. Nome: `admin-<seuNome>`. Marque **Provide user access to the Management Console** se quiser login web.
3. Permissões → **Attach policies directly** → marque **AdministratorAccess** (por enquanto).
4. Crie o usuário.

### Passo 6 — Gerar chaves de acesso (Access Keys) pra CLI
1. IAM → seu usuário → aba **Security credentials** → **Create access key**.
2. Caso de uso: **Command Line Interface (CLI)** → confirme.
3. **Copie `Access key ID` e `Secret access key`.** A secret só aparece **uma vez**.

> ⚠️ **NUNCA** cole essas chaves em código, em commit, ou neste repositório. Elas vão só pro
> `~/.aws/credentials` no próximo passo. Se vazar, **revogue imediatamente** no IAM.

---

## Parte C — Instalar e configurar a AWS CLI

### Passo 7 — Instalar a CLI

Verifique se já tem:
```bash
aws --version
```
Se não tiver, instale (Linux x86_64):
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```
(Para outros SOs: <https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>)

### Passo 8 — Configurar credenciais
```bash
aws configure
```
Responda:
- **AWS Access Key ID:** (cole a sua)
- **AWS Secret Access Key:** (cole a sua)
- **Default region name:** `us-east-1`
- **Default output format:** `json`

Isso grava dois arquivos em `~/.aws/`: `credentials` (chaves) e `config` (região/formato).

### Passo 9 — Testar: quem sou eu?
```bash
aws sts get-caller-identity
```
Deve retornar seu `UserId`, `Account` (ID da conta, 12 dígitos) e `Arn` (algo como
`arn:aws:iam::123456789012:user/admin-...`). **Se retornou isso, sua CLI está funcionando!** 🎉

---

## Parte D — Primeiros comandos reais (CLI)

Agora vamos *ver* na CLI os conceitos da teoria. Nenhum destes comandos cria recurso pago.

### Listar todas as Regiões disponíveis
```bash
aws ec2 describe-regions --query "Regions[].RegionName" --output table
```
> Você está vendo o "mapa" da AWS. O `--query` filtra a resposta (é **JMESPath**); o `--output table`
> formata bonito. Vamos usar muito `--query` no curso.

### Listar as AZs da sua região atual
```bash
aws ec2 describe-availability-zones --query "AvailabilityZones[].ZoneName" --output table
```
> Essas são as "gavetas" isoladas dentro da região onde, mais pra frente, você vai espalhar
> recursos pra ter alta disponibilidade.

### Ver a mesma coisa em outra região (sem trocar de config)
```bash
aws ec2 describe-availability-zones --region sa-east-1 --query "AvailabilityZones[].ZoneName" --output table
```
> Repare: `--region` sobrescreve a região padrão só pra este comando. Prova de que **regiões são isoladas**.

---

## Parte E — Teardown (higiene de custos)

Neste módulo **não criamos nenhum recurso pago** (conta, IAM user, budget e chaves não custam).
Então não há o que destruir. Mas fixe o ritual:

- ✅ Confirme que **não** deixou nenhum recurso ligado: no Console, **Billing → Bills** deve estar zerado.
- ✅ Guarde suas Access Keys num gerenciador de senhas (não no repo!).
- ✅ Da próxima vez que criarmos algo pago (Módulo 04+), o teardown vira obrigatório no fim.

---

## ✅ Checklist de conclusão do módulo

- [ ] Conta AWS criada.
- [ ] MFA ativado no root.
- [ ] Budget/alerta de custo configurado.
- [ ] Usuário IAM administrativo criado (parando de usar o root no dia a dia).
- [ ] Access keys geradas e guardadas com segurança (fora do repo).
- [ ] AWS CLI instalada e `aws configure` feito.
- [ ] `aws sts get-caller-identity` retornou sua identidade.
- [ ] Listou regiões e AZs pela CLI.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-01/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-01/`) e para o **Módulo 02 — Conta, IAM & Segurança**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 1" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
