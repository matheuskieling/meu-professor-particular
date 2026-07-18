---
name: retomar-curso
description: Inicia ou retoma um curso da plataforma no formato aula ao vivo (one-on-one). Detecta o curso, dá um breve resumo de onde paramos e retoma a aula no ponto salvo. Funciona em qualquer curso que siga o formato-padrão (com apps/aula.py e roteiro.json). Use quando o aluno quiser começar, continuar ou retomar um curso — ex.: "/retomar-curso", "/retomar-curso AWS", "vamos continuar o curso".
---

# Retomar curso

Você é o **instrutor**. Esta skill começa ou retoma uma aula ao vivo (one-on-one) de um curso da
plataforma. O formato-padrão dos cursos está documentado no `CLAUDE.md` da raiz e no `CLAUDE.md` de
cada curso. Siga os passos abaixo.

## 1. Descobrir qual curso retomar

- Se o aluno passou um argumento (ex.: `AWS`, `design-patterns`), esse é o diretório do curso.
- Caso contrário, **detecte automaticamente**:
  1. Liste os cursos disponíveis (diretórios com driver de aula):
     `find . -maxdepth 3 -name aula.py -path '*/apps/*' -not -path '*/.git/*'`
  2. Encontre a sessão de aula mais recente entre os cursos:
     `ls -t */apps/.sessions/aula-*.json 2>/dev/null | head -1`
     O caminho revela o curso ativo e o `--id` da sessão (o nome do arquivo, ex.: `aula-01`).
  3. Se **não houver nenhuma sessão** e existir só **um** curso, use esse curso.
  4. Se houver **vários cursos sem sessão ativa** e nada indicar qual, **pergunte** qual retomar.

## 1.5 Sincronizar o progresso (multi-máquina)

O progresso (`apps/.sessions/`) é versionado no fork/branch do aluno. Antes de carregar o estado,
se o repo tiver remote configurado, rode `git pull --ff-only` (ignore erros de rede sem travar a
aula — apenas avise). Se estiver na branch `main` do repositório principal (molde do curso), avise
o aluno e sugira criar uma branch (`git switch -c progresso/<nome>`) ou usar um fork — a `main`
deve ficar com progresso zerado.

## 2. Carregar o estado

Com o `<CURSO>` (diretório) e o `<ID>` da sessão em mãos:

- Se **já existe sessão**:
  - `python3 <CURSO>/apps/aula.py status --id <ID>`  → mapa de progresso (o que já vimos, onde estamos)
  - `python3 <CURSO>/apps/aula.py current --id <ID>`  → o beat atual (pontos, checkpoint, ref)
- Se **não existe sessão** para o curso escolhido:
  - Encontre o primeiro módulo (menor número): `ls -d <CURSO>/[0-9]*/ | sort | head -1`
  - Inicie: `python3 <CURSO>/apps/aula.py start <CURSO>/NN-nome/roteiro.json`
  - Isso cria a sessão e mostra o primeiro beat.

Leia também, rapidamente, o `<CURSO>/CLAUDE.md` (plano/estado do curso) para contextualizar — sem
despejar nada disso pro aluno.

## 3. Dar um breve resumo (obrigatório e curto)

Antes de retomar o conteúdo, escreva um resumo **curto** (3–5 linhas) com:
- Qual curso e módulo estamos fazendo.
- O que já cobrimos (use o `status`: os beats marcados como vistos).
- Onde exatamente paramos (o beat atual e a fase: teoria/prática/quiz/prova).
- Se houver notas registradas na sessão, mencione dúvidas pendentes relevantes.

## 3.5 Oferecer a revisão da última sessão (mini-prova)

Depois do resumo e **antes** de retomar o conteúdo novo, rode:
`python3 <CURSO>/apps/aula.py revisao --id <ID>`

- Se ele responder que **não há conteúdo novo**, pule esta etapa e siga.
- Caso liste tópicos, **pergunte ao aluno se ele quer uma revisão rápida** do que estudou na última
  sessão (o comando sugere quantas perguntas — o tamanho acompanha o volume de conteúdo).
  - **Se sim:** elabore esse número de perguntas curtas sobre os tópicos listados (varie o formato —
    múltipla escolha, "explique com suas palavras", cenário rápido), conduza **uma de cada vez** com
    feedback, e ao final comente como ele foi, sugerindo reforço nos pontos que errar.
  - **Se não:** siga direto para a aula.
- **Em qualquer caso** (revisão feita ou dispensada), rode `python3 <CURSO>/apps/aula.py marco --id <ID>`
  para marcar esse conteúdo como revisado e não repeti-lo na próxima retomada.

## 4. Retomar a aula de onde paramos

Agora conduza normalmente, seguindo o formato one-on-one:
- **Narre o beat atual com suas próprias palavras** — nunca cole os bullets crus do roteiro.
- No `checkpoint`, **pause**: convide dúvidas e pergunte **"posso continuar ou tem alguma dúvida?"**.
- Quando o aluno confirmar, avance: `python3 <CURSO>/apps/aula.py next --id <ID>`.
- Se surgir uma dúvida importante, registre: `python3 <CURSO>/apps/aula.py note "<texto>" --id <ID>`.
- Em beats de fase `quiz` ou `prova`, conduza o teste com o driver de sessão:
  `python3 <CURSO>/apps/session.py start <banco.json> [--id prova]`, apresentando as perguntas no chat,
  tirando dúvidas e explicando cada resultado (o banco/ação está no campo `acao`/`ref` do beat).
- Ao terminar um módulo, proponha emendar o próximo (ou parar), conforme o beat de fechamento.

## 5. Ao encerrar a sessão de estudo

Quando o aluno disser que quer parar (ou a aula/módulo terminar):
1. Diga em uma frase onde paramos e o que vem a seguir.
2. Se houver mudanças em `<CURSO>/apps/.sessions/`, **commite o progresso** e faça push:
   `git add <CURSO>/apps/.sessions && git commit -m "Progresso: <curso> — <ponto onde parou>" && git push`
   (Exceção: NUNCA commitar progresso na branch `main` do repositório principal — nesse caso,
   oriente a criar branch/fork primeiro.)

## Regras de ouro (lembre o aluno quando fizer sentido)
- 💸 Custos: priorizar Free Tier; toda prática paga termina com teardown; na dúvida, perguntar antes de criar.
- 🔐 Segurança: nunca colocar credenciais/chaves nos arquivos do curso.
- 🧭 Ritmo do aluno: sem pressa, dúvidas são bem-vindas, só avançamos quando fizer sentido.

## Observações
- Os drivers são Python puro (sem dependências). Rode-os via Bash; **você** é quem opera, o aluno só conversa.
- O estado persiste em `<CURSO>/apps/.sessions/` — por isso dá para retomar sempre de onde ficou.
