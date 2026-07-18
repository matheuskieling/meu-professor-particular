# Revisar (repetição espaçada, estilo Anki)

Leia o arquivo `.claude/skills/revisar/SKILL.md` deste repositório (é a definição canônica deste
comando, válida para qualquer agente) e siga exatamente as instruções dele: detectar o curso, montar
uma mini-prova de revisão acumulada do conteúdo já concluído (`apps/revisar.py nova`), conduzi-la com
`apps/session.py answer ... --id revisao` e fechar com `apps/revisar.py fechar` para reagendar.

Se o usuário passou um argumento (ex.: `AWS`), esse é o diretório do curso.
