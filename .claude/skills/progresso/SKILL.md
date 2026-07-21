---
name: progresso
description: Mostra o progresso de um curso da plataforma — % de cada módulo, % do curso completo, último beat concluído e o ritmo (beats por dia). Use quando o aluno quiser ver o avanço, "quanto falta", onde parou ou o ritmo de estudo — ex.: "/progresso", "/progresso AWS", "quanto já fiz do curso?".
---

# Progresso do curso

Esta skill dá ao aluno uma **visão geral do avanço** num curso da plataforma: quanto de cada módulo
já foi feito, quanto do curso inteiro, qual foi o último beat concluído (e quando) e o ritmo de
estudo. É **só leitura** — não conduz aula nem altera nada. Para retomar a aula, use `/retomar-curso`.

## 1. Descobrir o curso

- Se o aluno passou um argumento (ex.: `AWS`), esse é o diretório do curso.
- Caso contrário, **autodetecte**: o driver já resolve o curso pela sessão mais recente ou pelo único
  curso existente. Se houver ambiguidade real (vários cursos, nenhum indício), **pergunte** qual.

## 2. Sincronizar (multi-máquina)

Se o repo tiver remote, rode `git pull --ff-only` antes (ignore erro de rede sem travar — só avise),
para o progresso refletir o que foi feito em outras máquinas.

## 3. Rodar o relatório

```bash
python3 engine/progresso.py --curso <CURSO> --color always   # ou sem --curso p/ autodetectar
```

Use **sempre `--color always`**: o Bash não roda num TTY, então o `auto` desligaria as cores. O
driver imprime um **painel** (à la `/usage`): barra + % por módulo, % do curso completo, sparkline de
ritmo e o **último beat concluído** com data.

## 4. Apresentar ao aluno — MOSTRE O PAINEL, não reescreva

O painel do driver **É** o relatório visual. A regra de ouro:

- **Cole o painel verbatim num bloco de código** (```` ``` ````), exatamente como o driver imprimiu —
  as barras e a sparkline são a parte visual e renderizam em monoespaçado. **Não** transforme o painel
  em prosa/listas/tabela markdown por conta própria; foi esse o erro que fez o relatório virar texto de
  novo. **Só reescreva em prosa se o aluno pedir** (ex.: "me explica em texto", "resume por escrito");
  fora isso, o padrão é o painel. (As cores ANSI só renderizam no terminal real do aluno; no bloco de
  código elas não aparecem, e tudo bem — o layout já é o visual.)
- **Só embaixo do painel**, adicione **1–3 linhas** de contexto — não repita os números, agregue
  significado: quanto falta para o próximo marco **daquele curso**. Ex.: no AWS, os simulados da
  **CLF-C02** liberam após o **Módulo 07** e os da **SAA-C03** após o **18** — se o aluno tem meta de
  certificação, traduza o % em "faltam ~N beats até lá" e, se deu prazo, sugira um ritmo (beats/dia).
  Esse contexto de metas **não** vem do driver (agnóstico): é o agente que o adiciona lendo o
  `CLAUDE.md` do curso. Se o ritmo estiver parado, incentive sem cobrar; se estiver bom, reforce.

## 5. Datas retroativas (opcional)

O driver carimba a data de conclusão **a cada `next`** — ou seja, vale a partir de agora. Beats
concluídos **antes** dessa funcionalidade aparecem sem data (`—`). Se o aluno quiser recuperar parte
do histórico, rode o backfill (estima a data a partir das notas de cada beat, marcada como aproximada
com `~`):

```bash
python3 engine/aula.py backfill --id aula-<NN> --curso <CURSO>   # por sessão/módulo
```

Faça isso só se ele pedir, e deixe claro que datas com `~` são **estimativas** (derivadas das notas),
não registros exatos.

## Observações
- Driver Python puro, sem dependências. **Você** opera; o aluno só conversa.
- Não confundir com `aula.py status` (que é o progresso de **um** módulo/sessão). Aqui a visão é do
  **curso inteiro**.
