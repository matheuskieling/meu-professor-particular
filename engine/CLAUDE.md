# engine/ — Motor compartilhado da plataforma (todos os cursos)

Esta pasta contém os **drivers Python que servem TODOS os cursos**. Eles ficam aqui uma única vez —
nenhum curso precisa copiá-los ou recriá-los. Um curso novo é só **conteúdo** (roteiros + bancos de
questões); os drivers daqui operam sobre qualquer curso.

São Python puro, **sem dependências** (`python3` e pronto).

## Os drivers

| Arquivo | Papel |
|---------|-------|
| `aula.py` | Conduz a **aula ao vivo** a partir de um `roteiro.json`; salva o progresso, carimba a **data de conclusão de cada beat** e a revisão da última sessão. |
| `progresso.py` | **Relatório de progresso do curso inteiro** (só leitura): % por módulo, % do curso, último beat concluído e ritmo (beats/dia). |
| `session.py` | Conduz **quiz / prova / simulado** a partir de um `questions.json` (feedback por alternativa; suporta múltipla resposta). |
| `revisar.py` | **Revisão acumulada estilo Anki** (repetição espaçada) amostrando dos módulos já concluídos. |
| `reset.py` | Zera o progresso de um curso (apaga `<curso>/.sessions/`). |
| `quiz_engine.py` | Motor do **modo solo** (teclado), usado pelos runners `modulo-NN/quiz.py` e `provas/modulo-NN/prova.py` de cada curso. |
| `_common.py` | Resolução de curso/sessão compartilhada (não é executado direto). |

## Como o curso é descoberto (agnóstico de curso)

Cada curso é um **diretório direto na raiz do repositório** (ex.: `AWS/`, `Design-Patterns/`) e
guarda seu progresso em `<curso>/.sessions/` (versionado no fork do aluno). Os drivers descobrem o
curso assim:
- **Comandos com caminho** (`aula.py start <roteiro>`, `session.py start <banco>`): o curso é o 1º
  segmento do caminho sob a raiz do repo. Ex.: `AWS/01-fundamentos/roteiro.json` → curso `AWS`.
- **Comandos com estado** (`current`, `next`, `answer`, `status`, `revisar`, `reset`...): passe
  `--curso <dir>` **ou** deixe autodetectar (a sessão mais recente, ou o único curso existente).

## Uso (exemplos)

```bash
# Aula ao vivo
python3 engine/aula.py start AWS/01-fundamentos/roteiro.json     # curso derivado do caminho
python3 engine/aula.py current --id aula-01 --curso AWS
python3 engine/aula.py next    --id aula-01 --curso AWS

# Progresso do curso (visão geral: % por módulo, % do curso, último beat, ritmo)
python3 engine/progresso.py --curso AWS
python3 engine/aula.py backfill --id aula-01 --curso AWS              # (retroativo) estima datas via notas

# Quiz / prova / simulado
python3 engine/session.py start AWS/apps/modulo-01/questions.json     # quiz da aula
python3 engine/session.py answer A,C --id prova --curso AWS           # múltipla resposta

# Revisão espaçada (Anki) e reset
python3 engine/revisar.py nova  --curso AWS
python3 engine/reset.py         --curso AWS
```

## Formato do `questions.json` (bancos de quiz/prova/simulado)

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
- `feedbacks` (opcional): retorno **por alternativa** — essencial nas provas. Sem ele, mostra só a `explicacao`.
- **Múltipla resposta** (estilo exame, "Escolha DUAS"): use `corretas: [i, j]` no lugar de `correta`;
  responde-se com letras separadas por vírgula (`answer A,C`). Nesse caso as opções costumam ser 5.

## Como adicionar um curso novo (sem recriar drivers)

0. **Antes de escrever qualquer arquivo**, converse com o aluno: proponha o **currículo** para ele
   aprovar e **decida a questão da linguagem**. Pergunte-se: *o tema é agnóstico de linguagem* (design
   patterns, algoritmos, arquitetura, SOLID — os exemplos poderiam ser em qualquer linguagem OO)? Se
   **sim**, diga isso ao aluno em uma frase, **avise que o curso deixará cada aluno escolher a
   linguagem dos exemplos ao estudar**, e **pergunte em qual linguagem-base** você deve escrever os
   exemplos nos arquivos (ofereça a preferência conhecida do aluno como padrão — ex.: C# p/ dev .NET).
   Se o tema for de **infra** (tipo AWS) ou *sobre uma linguagem específica*, não há essa pergunta.
1. Crie o diretório do curso na raiz (ex.: `Design-Patterns/`) com um `CLAUDE.md` e um `README.md`.
2. Crie os módulos `NN-nome/` com `roteiro.json` + `teoria.md` + `pratica.md`.
3. Crie os bancos: `apps/modulo-NN/questions.json` (quiz) e `provas/modulo-NN/questions.json` (prova).
   Opcionalmente os runners solo `apps/modulo-NN/quiz.py` e `provas/modulo-NN/prova.py` (copie de um
   curso existente — são stubs de 4 linhas que só apontam o `questions.json` ao lado).
4. **Se o curso for agnóstico de linguagem** (design, algoritmos, padrões — a linguagem dos exemplos
   é gosto do aluno): declare isso no `CLAUDE.md` do curso, escreva os arquivos numa **linguagem-base**
   única e siga a convenção de **preferência salva** (`<Curso>/.sessions/preferencias.json`) descrita no
   `CLAUDE.md` da raiz. O `/retomar-curso` já pergunta a linguagem no início e a honra nas retomadas —
   sem código novo no motor. Cursos de infra ou *sobre* uma linguagem específica ignoram isso.
5. Pronto. As skills `/retomar-curso` e `/revisar` e os drivers do `engine/` já funcionam nele —
   nada de copiar motor. O progresso vai para `Design-Patterns/.sessions/`.

> Regra de manutenção: a **lógica** dos drivers mora só aqui. Não duplique drivers dentro de cursos.
> Nos roteiros, o campo `acao` chama `engine/session.py ...` (caminho fixo a partir da raiz do repo).
