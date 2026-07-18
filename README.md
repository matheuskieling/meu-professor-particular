# 🎓 Meu Professor Particular

Plataforma de **cursos de programação guiados por IA**: o agente (Claude Code, Codex, Cursor,
Gemini CLI...) atua como **professor particular** — conduz a aula ao vivo no chat, explica um ponto
por vez, tira dúvidas, aplica quizzes e provas, e **salva onde você parou** pra retomar depois.

| # | Curso | Status |
|---|-------|--------|
| 1 | [AWS & Cloud — mega intensivo](AWS/README.md) | ✅ Completo — 19 módulos + simulados CLF-C02/SAA-C03 |

## 🚀 Começando (5 minutos)

1. **Faça um fork** deste repositório (o repo principal fica com progresso zerado — o seu
   progresso será commitado **no seu fork**, e assim você continua de qualquer máquina).
2. Clone o seu fork e abra seu agente de código na pasta (ex.: `claude` no terminal).
3. Diga: **"vamos começar o curso de AWS"** — ou use a skill `/retomar-curso` (abaixo).

## 🧰 Skills disponíveis (Claude Code)

As skills são comandos que você digita com `/` no Claude Code:

| Skill | O que faz | Quando usar |
|-------|-----------|-------------|
| **`/retomar-curso`** | Detecta o curso, sincroniza seu progresso (`git pull`), resume onde você parou e **retoma a aula exatamente do ponto salvo**. Ao encerrar, commita seu progresso no fork. | Sempre que for **começar ou continuar** a estudar. É o jeito padrão de entrar no curso. Aceita argumento: `/retomar-curso AWS`. |

> Não usa Claude Code? Sem problema — o repo é **agnóstico de agente**. Peça em linguagem natural
> ("vamos continuar o curso de onde paramos") que qualquer agente segue o fluxo descrito em
> `AGENTS.md`/`CLAUDE.md`. Os drivers são Python puro, sem dependências.

## 📚 Como funciona um curso

Cada módulo segue o ciclo **teoria → prática real → quiz → prova** (detalhes no README de cada
curso). Você também pode estudar sozinho pelos arquivos `.md` e rodar os quizzes pelo teclado.
O curso de AWS ainda tem **simulados de certificação fiéis ao exame real** (CLF-C02 e SAA-C03,
65 questões, mesmo tempo e corte) e te avisa **quando você está pronto** pra prova de verdade.

## 🔄 Seu progresso

- Fica em `<Curso>/apps/.sessions/` e é **commitado no seu fork** (o agente faz isso por você ao
  fim de cada sessão de estudo).
- Outra máquina? `git pull` no fork e "vamos continuar".
- Recomeçar do zero: `python3 <Curso>/apps/reset.py`.

## 🗂️ Estrutura

```
├── README.md            ← você está aqui
├── CLAUDE.md            ← instruções-mestre para os agentes (fonte de verdade)
├── AGENTS.md            ← ponteiro para agentes de outros harnesses
├── .claude/skills/      ← skills do Claude Code (ex.: /retomar-curso)
└── AWS/                 ← Curso 1 (README próprio com o passo a passo)
```
