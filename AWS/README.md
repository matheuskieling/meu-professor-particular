# Curso de AWS & Cloud — Como fazer o curso

Bem-vindo ao mega intensivo de AWS. Este curso não é só um monte de textos pra ler sozinho:
a ideia é que ele seja um **one-on-one com o seu agente de IA** (Claude Code, Codex, Cursor,
Gemini CLI...) — ele conduz a aula, explica aos poucos, tira suas dúvidas na hora e avança no
seu ritmo. Este README explica **como isso funciona**.

---

## Os dois jeitos de fazer cada módulo

### 🎧 Jeito 1 — Aula guiada pelo agente (recomendado)
Você **não precisa abrir nenhum arquivo**. É só **iniciar o seu harness na pasta do repositório**
(ex.: `claude`, `codex`, `gemini`... no terminal) e entrar na aula de um destes dois jeitos
(equivalentes):

- **Pela skill:** digite **`/retomar-curso`** (no Claude Code) — ela sincroniza, resume e retoma sozinha;
- **Pelas palavras:** peça em linguagem natural (funciona em qualquer agente):
  > "Vamos começar o módulo 1" · "Bora continuar de onde paramos" · "Vamos fazer a prática"

O agente conduz assim:
1. Segue um **roteiro** (a lista ordenada de tudo que o módulo ensina).
2. Explica um ponto de cada vez, com as próprias palavras — nada de despejar textão.
3. Para e pergunta **"posso continuar ou tem alguma dúvida?"**. Você pergunta o que quiser.
4. Quando a teoria acaba, propõe **passar pra prática** e te guia na AWS passo a passo.
5. Depois conduz o **quiz** e a **prova**.
6. **Salva onde paramos** num arquivo de estado — então dá pra parar quando quiser e retomar
   depois exatamente de onde ficou (é só dizer "vamos continuar").

> Nos bastidores o agente usa uns scripts (`apps/aula.py` e `apps/session.py`) que guardam o roteiro
> e o progresso. Você não precisa saber deles — quem os roda é o agente. Estão documentados em `apps/CLAUDE.md`.

### 📖 Jeito 2 — Estudar sozinho (offline)
Se um dia você quiser fazer um módulo **sem agente nenhum**, todo o conteúdo também existe em arquivos:
- `NN-nome/teoria.md` — o texto teórico completo pra ler.
- `NN-nome/pratica.md` — o passo a passo da prática na AWS.
- `apps/modulo-NN/quiz.py` — o quiz pra você responder pelo teclado.
- `provas/modulo-NN/prova.py` — a prova do módulo.

Os dois jeitos cobrem o mesmo conteúdo; escolha por humor do dia. Pode até misturar (ler a teoria
sozinho e fazer a prática guiada pelo agente, por exemplo).

---

## O fluxo de um módulo (a ordem esperada)

```
  1. TEORIA      → entender o "porquê" (conceitos)
        ↓            o agente explica e pergunta "posso continuar?"
  2. PRÁTICA     → fazer de verdade na AWS (Console primeiro, depois CLI)
        ↓            eu te guio passo a passo; cuidamos de custo e teardown
  3. QUIZ        → fixar o conteúdo (o agente conduz as perguntas no chat)
        ↓
  4. PROVA       → avaliação do módulo (feedback por alternativa, aprovação 70%)
        ↓
  5. (opcional) SIMULADO DE CERTIFICAÇÃO → praticar no formato do exame oficial
        ↓
  → próximo módulo
```

Você não precisa decorar isso: o agente te conduz por essa ordem automaticamente e sempre pergunta
antes de mudar de etapa ("terminamos a teoria, podemos ir pra prática?").

---

## Retomar de onde paramos

Como o **estado é salvo**, você pode parar a qualquer momento. Na próxima vez, é só dizer algo como
"vamos continuar o curso" ou "onde a gente parou?" — o agente recupera o ponto exato (inclusive dentro
da teoria ou da prática) e vocês seguem. Ele também guarda **notas** de dúvidas importantes que
aparecerem no caminho.

### A skill `/retomar-curso` (Claude Code)

O jeito mais fácil de entrar no curso é digitar **`/retomar-curso`** (ou `/retomar-curso AWS`).
Ela faz tudo em sequência:
1. Sincroniza seu progresso (`git pull` no seu fork/branch);
2. Detecta o curso e carrega o estado salvo;
3. Te dá um **resumo curto** de onde paramos (módulo, fase, dúvidas anotadas);
4. **Retoma a aula do ponto exato** — e ao encerrar, commita seu progresso.

Use-a **sempre** que for estudar: primeira vez (ela inicia o módulo 1), continuação, ou depois de
um reset. Em agentes sem skills, é só pedir "vamos continuar o curso de onde paramos" — o fluxo
está descrito no `AGENTS.md`/`CLAUDE.md` e funciona em qualquer harness.

## Seu progresso: faça um fork e commite

O repositório principal fica sempre com **progresso zerado** — ele é o "molde" do curso. Pra
estudar, o fluxo é:

1. **Faça um fork** deste repositório no seu GitHub (botão *Fork*).
2. Clone o **seu fork** e estude nele. Seu progresso fica em `AWS/apps/.sessions/` e é
   **commitado normalmente**:
   ```bash
   git add AWS/apps/.sessions && git commit -m "Progresso: módulo 01, beat t3" && git push
   ```
   (peça pro agente fazer isso ao fim de cada sessão de estudo — ele já sabe.)
3. Em **outra máquina**? `git clone` do seu fork (ou `git pull`) e diga "vamos continuar" — a aula
   retoma exatamente de onde parou. ☁️

> **Dono do repositório:** estude numa branch própria (ex.: `progresso/<seu-nome>`) e mantenha a
> `main` limpa, pra que os forks dos amigos sempre nasçam zerados.

## Recomeçar do zero (reset)

Pra zerar seu progresso (recomeçar ou testar de novo) sem tocar no conteúdo do curso:

```bash
python3 AWS/apps/reset.py           # apaga TODO o progresso e volta o curso ao início
python3 AWS/apps/reset.py --list    # só mostra as sessões em andamento (não apaga nada)
python3 AWS/apps/reset.py --id aula-01   # reseta só uma sessão específica
```

Depois commite o reset no seu fork e chame `/retomar-curso` (ou "vamos começar o módulo 1").

---

## Certificações AWS — quando você está pronto

O curso te prepara para as certificações oficiais, com **3 provas simuladas completas por
certificação**, fiéis ao exame real (65 questões, mesmo tempo, mesmo corte, questões de
"Escolha DUAS"). E ele te diz **exatamente quando você está pronto**:

### CLF-C02 — Cloud Practitioner (65 questões · 90 min · corte 70%)
- 🟡 **Pronto pros simulados:** terminou os **Módulos 01–07** com ≥70% em todas as provas de módulo.
- 🟢 **Pronto pra prova real:** tirou **≥80% nas 3 provas simuladas**, cada uma dentro de
  **90 minutos e sem consultar material**. Aí é só agendar o exame com confiança.

### SAA-C03 — Solutions Architect Associate (65 questões · 130 min · corte 72%)
- 🟡 **Pronto pros simulados:** terminou os **Módulos 01–18** com ≥70% nas provas de módulo.
- 🟢 **Pronto pra prova real:** **≥80% nas 3 provas simuladas** dentro de **130 minutos** sem
  consulta, e **Módulo 19 (projeto final)** concluído.

> Por que 80% se o corte é ~70%? Nervosismo, tempo e questões experimentais do exame real comem
> uns pontos — 80% nos simulados é a margem de segurança. Ficou entre 70–79%? Revise os domínios
> com mais erros e refaça a pior prova antes de agendar.

Quem conduz os simulados é o agente, e **ele mesmo te avisa**: "você bateu o portão, pode agendar"
ou "falta X, revise Y". Você não precisa controlar nada disso manualmente.

## Regras de ouro (valem o curso inteiro)

- 💸 **Custos:** priorizamos o **Free Tier**. Toda prática avisa o que cobra e sempre termina com
  **teardown** (destruir os recursos). Na dúvida se algo custa, **pergunte ao agente antes de criar**.
- 🔐 **Segurança:** nunca colocamos credenciais/chaves nos arquivos do curso. Elas ficam só na sua
  máquina (`~/.aws/`). MFA no root desde o primeiro dia.
- 🧭 **Seu ritmo:** não tem pressa. Pergunte quantas vezes precisar; a gente só avança quando fizer sentido.

---

## Estrutura de pastas

Veja `CLAUDE.md` (nesta pasta) para o **plano completo dos 19 módulos**, a anatomia de cada módulo
e os detalhes técnicos. Resumão:

```
AWS/
├── README.md              ← este arquivo (como fazer o curso)
├── CLAUDE.md              ← plano completo + como cada módulo é construído
├── NN-nome/               ← cada módulo: teoria.md, pratica.md, roteiro.json
├── apps/                  ← drivers (aula.py, session.py) + quizzes das aulas
├── provas/                ← provas de fim de módulo
└── certificacoes/         ← simulados das certificações oficiais
```

---

## Pronto pra começar?

Inicie seu harness na pasta do repositório e digite **`/retomar-curso`** — ou simplesmente diga
**"vamos começar o módulo 1"**. 🚀
