---
name: revisar
description: Faz uma revisão acumulada estilo Anki — uma mini-prova amostrando de todo o conteúdo já concluído no curso, com repetição espaçada (perguntas reaparecem de tempos em tempos). Use quando o aluno quiser revisar o que já viu ("quero revisar", "me testa no que já aprendi", "/revisar"). Funciona em qualquer curso da plataforma com engine/revisar.py.
---

# Revisar (repetição espaçada, estilo Anki)

Conduz uma **revisão acumulada** do curso: uma mini-prova que amostra de **tudo que o aluno já
concluiu** e agenda cada pergunta para reaparecer com o tempo. Diferente do recap da última sessão
(feito na retomada) — aqui o foco é fixação de longo prazo. Passos:

## 1. Descobrir o curso
Igual à skill `/retomar-curso`: se o aluno passou um argumento (ex.: `AWS`), use-o; senão, detecte o
curso com sessão mais recente (`ls -t */.sessions/*.json`) ou, havendo um só curso, use-o.
Se o repo tiver remote, `git pull --ff-only` antes (ignore erro de rede, só avise).

## 2. Montar a mini-prova
Rode: `python3 engine/revisar.py nova --n 8 --curso <CURSO>`
- Ajuste `--n` ao tempo do aluno (5 para algo rápido, 10-12 para uma revisão mais longa).
- Se responder que **não há módulos concluídos**, explique que a revisão acumulada abre quando ele
  terminar o primeiro módulo; ofereça seguir a aula normalmente.
- O comando já inicia a sessão (id `revisao`) e mostra a primeira pergunta.

## 3. Conduzir
Apresente cada pergunta no chat e registre a resposta do aluno:
`python3 engine/session.py answer <letra(s)> --id revisao`
(resposta múltipla, quando houver, é `A,C`). Dê o feedback que o driver retorna com suas palavras,
tire dúvidas e, se ele errar, reforce o conceito. Siga até a última pergunta.

## 4. Fechar e reagendar
Ao terminar, rode: `python3 engine/revisar.py fechar --curso <CURSO>`
- Isso atualiza o "baralho": acertos sobem de caixa (a pergunta volta mais tarde), erros voltam para
  a caixa 1 (reaparecem logo). Comente o resultado e o que vale reforçar.
- Se o repo tiver remote e houver mudanças em `<CURSO>/.sessions/`, **commite o progresso**:
  `git add <CURSO>/.sessions && git commit -m "Revisão: <curso>" && git push`
  (nunca na branch `main` do repositório principal — nesse caso, oriente a usar fork/branch).

## Observações
- Fonte das perguntas: os bancos de quiz/prova dos módulos concluídos; nada é perguntado antes de ser
  estudado. Para estudo solo sem sessões de aula, use `--ate NN` (inclui módulos 01..NN).
- O histórico (`.sessions/revisao-deck.json`) é versionado no fork do aluno e acompanha entre
  máquinas; `reset.py` limpa junto.
