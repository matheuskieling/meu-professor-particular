# Courses — Plataforma de Cursos

Este repositório é uma **plataforma pessoal de cursos** na área de programação, criada para o
aprendizado do dono do repositório. Cada curso vive em seu próprio diretório na raiz e é
construído de forma incremental, misturando **teoria** e **prática guiada**.

O papel do Claude aqui não é só gerar conteúdo estático: é atuar como **instrutor**. Isso
significa explicar conceitos, propor exercícios, guiar passo a passo execuções reais (ex.:
comandos na AWS, código, configurações) e verificar o entendimento antes de avançar.

## Estrutura

```
courses/
├── CLAUDE.md          ← este arquivo (visão geral da plataforma)
├── AWS/               ← Curso 1: AWS & Cloud (mega intensivo)
│   └── CLAUDE.md      ← contexto e plano do curso de AWS
└── <futuros cursos>/  ← cada curso novo ganha seu próprio diretório + CLAUDE.md
```

**Convenção importante:** todo diretório dentro da raiz tem seu próprio `CLAUDE.md`
descrevendo o que ele contém, o objetivo e como o conteúdo está organizado. O `CLAUDE.md`
de cada diretório é a fonte de verdade sobre aquele escopo — leia-o antes de trabalhar ali.

## Filosofia dos cursos

- **Da base ao avançado.** Começamos pelos fundamentos e subimos até dar plena autonomia.
- **Teoria + prática.** Textos teóricos para entender o "porquê", seguidos de exercícios
  práticos reais para fixar o "como".
- **Aprender fazendo.** Sempre que possível, o aluno executa de verdade (na AWS, no terminal,
  no código) com o Claude guiando cada etapa.
- **Incremental.** O conteúdo cresce conforme avançamos. Nada precisa estar completo de início.

## Como os cursos funcionam — formato padrão (vale para TODOS os cursos)

Este é o formato-padrão da plataforma. **Todo curso novo replica esta estrutura.** A ideia central:
o curso é um **one-on-one com o Claude**, não uma leitura solitária. O Claude conduz a aula ao vivo,
explica um ponto por vez, convida dúvidas, pergunta **"posso continuar?"** e **salva onde paramos**
para retomar depois. Os arquivos `.md` continuam existindo para quem quiser estudar sozinho.

### Estrutura padrão de um curso

```
<Curso>/
├── CLAUDE.md              ← plano do curso + anatomia dos módulos (fonte de verdade)
├── README.md             ← como fazer o curso (para o aluno)
├── NN-nome/              ← um diretório por módulo, numerado
│   ├── roteiro.json      ← ESPINHA da aula ao vivo: "beats" ordenados que o Claude conduz
│   ├── teoria.md         ← texto teórico (para estudo solo / referência)
│   └── pratica.md        ← passo a passo da prática guiada
├── apps/                 ← drivers + apps de teste (Python puro, sem dependências)
│   ├── aula.py           ← driver da AULA ao vivo (lê roteiro.json, salva progresso)
│   ├── session.py        ← driver de QUIZ/PROVA (lê questions.json)
│   ├── quiz_engine.py    ← motor do quiz no modo solo (teclado)
│   ├── reset.py          ← zera o progresso local (recomeçar do início)
│   ├── .sessions/        ← estado de aulas/quizzes em andamento (gitignored)
│   └── modulo-NN/questions.json   ← banco de questões da aula
├── provas/modulo-NN/     ← prova de fim de módulo (feedback por alternativa)
└── (extras do curso)     ← ex.: AWS tem certificacoes/; outros cursos terão o que fizer sentido
```

Os **drivers** (`aula.py`, `session.py`, `quiz_engine.py`) são **agnósticos de curso** — ao criar um
curso novo, copie a pasta `apps/` de um curso existente e crie só o conteúdo (roteiros e questões).

### Os dois modos de cada módulo

1. **Aula ao vivo (padrão):** o Claude roda `apps/aula.py`, que guarda o **roteiro** (o que ensinar)
   e o **progresso** (onde paramos). O Claude narra cada beat com as próprias palavras, tira dúvidas,
   e só avança (`aula.py next`) quando o aluno confirma. Ao chegar em beats de quiz/prova, dispara o
   `session.py`. O estado persiste → dá para **parar e retomar sempre de onde ficou**.
2. **Solo:** o aluno lê os `.md` e roda os quizzes pelo teclado (`quiz.py`, `prova.py`).

O **progresso é local e individual** (`apps/.sessions/`, gitignored) — quem clona o repo começa do
zero. Para recomeçar no meio, `python3 <Curso>/apps/reset.py` zera o progresso sem tocar no conteúdo.

### Anatomia de um módulo (ciclo aprender → praticar → testar → avaliar)

`roteiro.json` (espinha da aula) · `teoria.md` (o porquê) · `pratica.md` (fazer de verdade) ·
**quiz** da aula (fixar) · **prova** do módulo (avaliar, 70%) · extras de certificação quando houver.
Cada curso detalha isso no seu próprio `CLAUDE.md` (ver `AWS/CLAUDE.md` como referência viva).

### Retomar um curso

Para começar/retomar qualquer curso, o aluno usa a skill **`/retomar-curso`**: ela detecta o curso,
dá um breve resumo de onde paramos e retoma a aula no ponto salvo. Funciona em qualquer curso que siga
este formato-padrão. (Definição em `.claude/skills/retomar-curso/`.)

## Cursos

| # | Curso | Diretório | Status |
|---|-------|-----------|--------|
| 1 | AWS & Cloud (mega intensivo) | `AWS/` | ✅ Completo — 19 módulos + simulados CLF-C02/SAA-C03 |
