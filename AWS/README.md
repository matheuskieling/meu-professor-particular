# Curso de AWS & Cloud — Como fazer o curso

Bem-vindo ao mega intensivo de AWS. Este curso não é só um monte de textos pra ler sozinho:
a ideia é que ele seja um **one-on-one com o Claude** — eu conduzo a aula, explico aos poucos,
tiro suas dúvidas na hora e a gente avança no seu ritmo. Este README explica **como isso funciona**.

---

## Os dois jeitos de fazer cada módulo

### 🎧 Jeito 1 — Aula guiada com o Claude (recomendado)
Você **não precisa abrir nenhum arquivo**. É só me chamar:

> "Vamos começar o módulo 1" · "Bora continuar de onde paramos" · "Vamos fazer a prática"

Eu conduzo assim:
1. Sigo um **roteiro** (a lista ordenada de tudo que quero te ensinar naquele módulo).
2. Explico um ponto de cada vez, com minhas palavras — nada de despejar textão.
3. Paro e pergunto **"posso continuar ou tem alguma dúvida?"**. Você pergunta o que quiser.
4. Quando a teoria acaba, eu proponho **passar pra prática** e te guio na AWS passo a passo.
5. Depois rodamos o **quiz** e a **prova** (também comigo conduzindo).
6. **Salvo onde paramos** num arquivo de estado — então dá pra parar quando quiser e retomar
   depois exatamente de onde ficou (é só dizer "vamos continuar").

> Nos bastidores eu uso uns scripts (`apps/aula.py` e `apps/session.py`) que guardam o roteiro e o
> progresso. Você não precisa saber deles — quem roda sou eu. Mas estão documentados em `apps/CLAUDE.md`.

### 📖 Jeito 2 — Estudar sozinho (offline)
Se um dia você quiser fazer um módulo **sem mim**, todo o conteúdo também existe em arquivos:
- `NN-nome/teoria.md` — o texto teórico completo pra ler.
- `NN-nome/pratica.md` — o passo a passo da prática na AWS.
- `apps/modulo-NN/quiz.py` — o quiz pra você responder pelo teclado.
- `provas/modulo-NN/prova.py` — a prova do módulo.

Os dois jeitos cobrem o mesmo conteúdo; escolha por humor do dia. Pode até misturar (ler a teoria
sozinho e fazer a prática comigo, por exemplo).

---

## O fluxo de um módulo (a ordem esperada)

```
  1. TEORIA      → entender o "porquê" (conceitos)
        ↓            eu explico e pergunto "posso continuar?"
  2. PRÁTICA     → fazer de verdade na AWS (Console primeiro, depois CLI)
        ↓            eu te guio passo a passo; cuidamos de custo e teardown
  3. QUIZ        → fixar o conteúdo (eu conduzo as perguntas no chat)
        ↓
  4. PROVA       → avaliação do módulo (feedback por alternativa, aprovação 70%)
        ↓
  5. (opcional) SIMULADO DE CERTIFICAÇÃO → praticar no formato do exame oficial
        ↓
  → próximo módulo
```

Você não precisa decorar isso: eu te conduzo por essa ordem automaticamente e sempre te pergunto
antes de mudar de etapa ("terminamos a teoria, podemos ir pra prática?").

---

## Retomar de onde paramos

Como eu **salvo o estado**, você pode parar a qualquer momento. Na próxima vez, é só dizer algo como
"vamos continuar o curso" ou "onde a gente parou?" — eu recupero o ponto exato (inclusive dentro da
teoria ou da prática) e seguimos. Também guardo **notas** de dúvidas importantes que aparecerem no caminho.

Atalho: a skill **`/retomar-curso`** faz exatamente isso — detecta o curso, resume onde paramos e retoma.

## Recomeçar o curso do zero (reset)

Seu progresso é **local e individual** (fica em `apps/.sessions/`, que não vai pro Git). Ou seja:
quem clona este repositório **já começa do zero**, sem herdar o progresso de ninguém.

Se quiser **zerar seu progresso no meio do caminho** (recomeçar ou testar de novo), rode:

```bash
python3 AWS/apps/reset.py           # apaga TODO o progresso e volta o curso ao início
python3 AWS/apps/reset.py --list    # só mostra as sessões em andamento (não apaga nada)
python3 AWS/apps/reset.py --id aula-01   # reseta só uma sessão específica
```

O reset mexe **apenas no seu progresso** — não altera nenhum conteúdo do curso (teoria, prática,
roteiros, questões). Depois de resetar, é só chamar `/retomar-curso` (ou "vamos começar o módulo 1")
pra recomeçar do início.

---

## Regras de ouro (valem o curso inteiro)

- 💸 **Custos:** priorizamos o **Free Tier**. Toda prática avisa o que cobra e sempre termina com
  **teardown** (destruir os recursos). Na dúvida se algo custa, **me pergunte antes de criar**.
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

É só me dizer: **"vamos começar o módulo 1"**. 🚀
