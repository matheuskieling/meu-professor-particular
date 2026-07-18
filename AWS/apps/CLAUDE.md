# AWS/apps — Drivers e aplicações de teste

Aqui vivem os **drivers que o Claude opera** para conduzir o curso, e as **apps de teste** (quizzes)
de cada módulo. Dois drivers, propósitos diferentes:

- **`aula.py`** — conduz a **aula ao vivo** (teoria + prática) seguindo um `roteiro.json`, salvando
  onde paramos. É o coração do formato one-on-one.
- **`session.py`** — conduz **quiz/prova/simulado** a partir de um `questions.json`.

Ambos são **máquinas de estado** (sem stdin travado), persistem em `.sessions/` (gitignored) e são
pensados para o Claude rodar via Bash, narrando/explicando no chat.

---

## `aula.py` — driver de aula ao vivo (conduzido pelo Claude)

Guarda o **roteiro** (a lista ordenada de "beats" — os pontos a ensinar) e o **progresso**. Quem
ensina é o Claude; o driver só entrega o próximo beat e registra o avanço. Fluxo típico:

```bash
python3 AWS/apps/aula.py start AWS/01-fundamentos/roteiro.json   # mostra o beat atual
python3 AWS/apps/aula.py next                                    # avança quando o aluno topar
python3 AWS/apps/aula.py current                                 # retomar de onde paramos
python3 AWS/apps/aula.py status                                  # mapa de progresso
python3 AWS/apps/aula.py goto p1                                 # pular para um beat (ex.: prática)
python3 AWS/apps/aula.py note "aluno teve dúvida em AZ x Região" # registrar nota/dúvida
```
- Cada beat traz `pontos` (o que desenvolver), `checkpoint` (a deixa do "posso continuar?"), e às
  vezes `acao` (ex.: rodar o quiz) e `ref` (seção de apoio em teoria.md/pratica.md).
- O `--id` padrão é `aula-<modulo>`; o beat atual sobrevive entre sessões, então dá pra **retomar**.
- **Como o Claude usa:** rode `current`/`next`, leia os pontos, **narre com suas palavras** (não cole
  os bullets crus), convide dúvidas, e só chame `next` após o aluno confirmar. Ao chegar num beat de
  fase `quiz`/`prova`, dispare o `session.py` correspondente.

Formato do `roteiro.json`: ver cabeçalho de `aula.py` (campos `modulo`, `titulo`, `beats[]`).

---

## `session.py` — aplicações de teste (quiz/prova/certificação)

As apps de teste reforçam o conteúdo. Compartilham o formato `questions.json` e rodam em **dois modos**.

## Dois modos de uso

### 1. Modo conduzido pelo Claude (preferido) — `session.py`
Uma **máquina de estado** que persiste a sessão em arquivo. É o Claude quem opera: apresenta cada
pergunta no chat, recebe a resposta do aluno em linguagem natural, chama `answer` e explica o
retorno — **tirando dúvidas ao longo do caminho**. Sem interação de stdin, então é robusto.

```bash
python3 AWS/apps/session.py start AWS/apps/modulo-01/questions.json   # mostra a Q1
python3 AWS/apps/session.py answer B                                  # corrige e avança
python3 AWS/apps/session.py status                                    # progresso/nota
python3 AWS/apps/session.py current                                   # remostra a questão
python3 AWS/apps/session.py reset                                     # zera a sessão
```
Use `--id <nome>` para múltiplas sessões simultâneas (ex.: `--id prova`, `--id cert`).
O mesmo `session.py` roda **qualquer** banco: quiz de aula, prova de módulo ou simulado de certificação.

### 2. Modo solo — `quiz_engine.py` + `quiz.py`
O aluno roda sozinho e responde pelo teclado. Cada módulo tem um `quiz.py` fininho:
```bash
python3 AWS/apps/modulo-01/quiz.py
```

## Estrutura

```
apps/
├── CLAUDE.md
├── aula.py             ← driver de AULA ao vivo (roteiro + progresso)
├── session.py          ← driver de QUIZ/PROVA conduzido pelo Claude
├── quiz_engine.py      ← motor do quiz no modo solo (lê do teclado)
├── reset.py            ← zera o progresso local (apaga .sessions/)
├── .sessions/          ← estado de aulas e quizzes em andamento (gitignored)
└── modulo-01/
    ├── quiz.py         ← runner solo do quiz do módulo
    └── questions.json  ← banco de questões da aula
```

> O **roteiro** de cada aula (`roteiro.json`) fica junto do módulo (ex.: `01-fundamentos/roteiro.json`),
> não aqui — é conteúdo do módulo. Aqui ficam só os drivers e os quizzes.

## Resetar o progresso — `reset.py`
O progresso (aula + quizzes/provas) vive em `.sessions/` (gitignored, individual por aluno). Para
recomeçar do zero sem tocar no conteúdo do curso:
```bash
python3 AWS/apps/reset.py          # apaga todo o progresso
python3 AWS/apps/reset.py --list   # lista sessões sem apagar
python3 AWS/apps/reset.py --id aula-01   # reseta só uma sessão
```

## Formato do `questions.json`

```json
{
  "titulo": "Módulo 01 — ...",
  "aprovacao": 70,
  "questoes": [
    {
      "pergunta": "texto",
      "opcoes": ["A ...", "B ...", "C ...", "D ..."],
      "correta": 0,
      "explicacao": "justificativa da resposta correta",
      "feedbacks": ["por que A ...", "por que B ...", "..."]
    }
  ]
}
```
- `feedbacks` (opcional) dá retorno **por alternativa** — essencial nas provas. Sem ele, mostra só a `explicacao`.

## Convenção ao criar uma nova aula
1. Crie `apps/modulo-NN/questions.json` com as questões da aula.
2. Crie `apps/modulo-NN/quiz.py` (copie o do módulo 01, só muda o caminho).
3. Prefira Python puro, **sem dependências externas** (roda com `python3` e pronto).
