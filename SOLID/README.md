# Curso de SOLID — Como fazer o curso

Bem-vindo ao curso de **SOLID** — os cinco princípios de design orientado a objetos que separam
código que envelhece bem de código que quebra a cada mudança. Como o de AWS, este curso é um
**one-on-one com o seu agente de IA** (Claude Code, Codex, Cursor, Gemini CLI...): ele conduz a aula,
explica aos poucos, tira suas dúvidas na hora e avança no seu ritmo.

É um curso **menor e mais denso** (7 módulos), **sem custos** e **sem certificação** — SOLID não tem
exame oficial.

**Você escolhe a linguagem dos exemplos.** SOLID é sobre *design*, não sobre sintaxe — então, no
começo, o agente pergunta em qual linguagem você quer os exemplos (C#, Java, TypeScript, Python, Go,
Kotlin, PHP...) e conduz tudo nela. A escolha fica salva (`SOLID/.sessions/preferencias.json`) e vale
pelo curso inteiro; é só pedir pra trocar quando quiser. Os arquivos de estudo solo (`.md`) trazem os
exemplos em **C#** como referência-base.

---

## O que você vai aprender

Não é um curso de sintaxe — é sobre **decisões de design**. Ao final você vai saber reconhecer um
design apodrecendo, nomear o princípio que corrige cada problema e refatorar com segurança — **sem
exagerar** (SOLID mal aplicado vira over-engineering, e o curso ensina a dosar).

| # | Módulo | O que você leva |
|---|--------|-----------------|
| 01 | Fundamentos de Design | O vocabulário: acoplamento x coesão, os sintomas do código podre, de onde SOLID veio |
| 02 | **S**RP | Dar a cada classe uma única razão para mudar |
| 03 | **O**CP | Estender comportamento sem editar o que já funciona |
| 04 | **L**SP | Hierarquias em que o filho realmente substitui o pai |
| 05 | **I**SP | Interfaces enxutas, sem obrigar ninguém a implementar o que não usa |
| 06 | **D**IP | Depender de abstrações + a injeção de dependência (container do .NET, Spring, NestJS... conforme sua linguagem) |
| 07 | Capstone | Refatorar um sistema aplicando os 5 juntos e ver a ponte para Design Patterns |

---

## Os dois jeitos de fazer cada módulo

### 🎧 Jeito 1 — Aula guiada pelo agente (recomendado)
Você **não precisa abrir nenhum arquivo**. Inicie seu harness na pasta do repositório e entre na
aula de um destes jeitos (equivalentes):

- **Pela skill:** digite **`/retomar-curso SOLID`** (no Claude Code) — sincroniza, resume e retoma;
- **Pelas palavras** (qualquer agente): *"vamos começar o curso de SOLID"*, *"bora continuar de onde
  paramos no SOLID"*, *"vamos fazer a prática do OCP"*.

O agente segue um **roteiro**, explica um ponto de cada vez, para e pergunta **"posso continuar?"**,
conduz a **prática** (refatoração no chat), depois o **quiz** e a **prova** — e **salva onde
paramos** pra você retomar depois.

### 📖 Jeito 2 — Estudar sozinho (offline)
Todo o conteúdo também está em arquivos:
- `NN-nome/teoria.md` — o texto teórico, com exemplos "antes/depois" em C# (a linguagem-base; na aula
  guiada o agente traduz pra sua linguagem).
- `NN-nome/pratica.md` — o exercício de refatoração (código de partida + solução comentada).
- `apps/modulo-NN/quiz.py` — o quiz pra responder pelo teclado.
- `provas/modulo-NN/prova.py` — a prova do módulo.

---

## O fluxo de um módulo

```
  1. TEORIA    → o "porquê" do princípio + exemplo antes/depois na sua linguagem
        ↓          o agente explica e pergunta "posso continuar?"
  2. PRÁTICA   → refatorar um trecho com o cheiro do módulo (conduzido no chat)
        ↓
  3. QUIZ      → fixar (o agente conduz as perguntas no chat) — 10 questões
        ↓
  4. PROVA     → avaliação do módulo (feedback por alternativa, aprovação 70%) — 12 questões
        ↓
  → próximo módulo
```

O agente te conduz por essa ordem e sempre pergunta antes de mudar de etapa.

---

## Retomar de onde paramos

Como o **estado é salvo**, pare quando quiser. Na próxima vez, diga "vamos continuar o SOLID" ou
"onde a gente parou?" — o agente recupera o ponto exato (inclusive dentro da teoria ou da prática).

### A skill `/retomar-curso` (Claude Code)
Digite **`/retomar-curso SOLID`**: ela sincroniza seu progresso, carrega o estado salvo, te dá um
**resumo curto** de onde paramos, oferece uma **revisão rápida** da última sessão e **retoma a aula
do ponto exato** — commitando seu progresso ao encerrar.

## Seu progresso: faça um fork (ou uma branch) e commite

O repositório principal fica com **progresso zerado** — é o "molde" do curso. Pra estudar:

1. **Faça um fork** (ou estude numa branch própria, ex.: `progresso/<seu-nome>`).
2. Seu progresso fica em `SOLID/.sessions/` e é **commitado normalmente**:
   ```bash
   git add SOLID/.sessions && git commit -m "Progresso SOLID: módulo 02, beat t3" && git push
   ```
   (peça pro agente fazer isso ao fim de cada sessão — ele já sabe.)
3. Em **outra máquina**? `git pull` e diga "vamos continuar" — a aula retoma de onde parou.

## Revisão de longo prazo (estilo Anki)

Digite **`/revisar`** (ou "me testa no que já aprendi"): monta uma **mini-prova** sorteando de todos
os módulos que você já concluiu, com **repetição espaçada** (o que você erra reaparece mais cedo). O
histórico fica no seu fork (`.sessions/revisao-deck.json`).

## Recomeçar do zero (reset)

```bash
python3 engine/reset.py --curso SOLID        # zera o progresso do SOLID
python3 engine/reset.py --curso SOLID --list # só mostra as sessões (não apaga)
```

---

## Regras de ouro (valem o curso inteiro)

- 🎯 **Dosagem > dogma.** SOLID não é para aplicar cegamente. Cada módulo mostra também *quando NÃO*
  aplicar o princípio — over-engineering é tão ruim quanto o código rígido que ele tenta corrigir.
- 🧩 **Design, não sintaxe.** O foco é onde colocar a fronteira entre classes e quando criar (ou não)
  uma abstração. Você não precisa rodar código: a prática é raciocínio, conduzido no chat.
- 🧭 **Seu ritmo.** Sem pressa. Pergunte quantas vezes precisar; a gente só avança quando fizer sentido.

---

## Pronto pra começar?

Inicie seu harness na pasta do repositório e digite **`/retomar-curso SOLID`** — ou diga
**"vamos começar o curso de SOLID"**. 🚀
