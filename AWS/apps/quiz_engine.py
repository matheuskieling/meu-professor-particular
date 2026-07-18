"""
Motor de quiz/prova reutilizável para o curso de AWS.

Cada aula tem um quiz e cada módulo tem uma prova; ambos usam este motor.
Um runner fininho aponta para um `questions.json` e chama `run_quiz(...)`.
Sem dependências externas — roda com Python 3.

Formato do JSON:
{
  "titulo": "Módulo 01 — ...",
  "aprovacao": 70,                # % mínimo pra aprovar (opcional, padrão 70)
  "questoes": [
    {
      "pergunta": "texto",
      "opcoes": ["A ...", "B ...", "C ...", "D ..."],
      "correta": 0,              # índice (0-based) da opção correta
      "explicacao": "por que a resposta certa é certa",
      "feedbacks": [             # OPCIONAL — feedback por alternativa
        "por que A está certa/errada",
        "por que B está errada",
        "..."
      ]
    }
  ]
}

- `explicacao`: usada como justificativa geral da resposta correta.
- `feedbacks`: se presente, mostra um retorno específico para a opção que o aluno
  escolheu (o diferencial das PROVAS). Se ausente, cai no comportamento simples
  (mostra só a `explicacao`). As duas coisas podem coexistir.
"""

import json
import os
import random
import sys


def _supports_color():
    return sys.stdout.isatty() and os.environ.get("TERM") not in (None, "dumb")


if _supports_color():
    VERDE, VERMELHO, AMARELO, AZUL, CINZA, NEGRITO, RESET = (
        "\033[92m", "\033[91m", "\033[93m", "\033[94m", "\033[90m", "\033[1m", "\033[0m",
    )
else:
    VERDE = VERMELHO = AMARELO = AZUL = CINZA = NEGRITO = RESET = ""

LETRAS = "ABCDEFGH"


def carregar_questoes(caminho_json):
    with open(caminho_json, "r", encoding="utf-8") as f:
        return json.load(f)


def _perguntar(questao, numero, total):
    print(f"\n{NEGRITO}{AZUL}Questão {numero}/{total}{RESET}")
    print(f"{NEGRITO}{questao['pergunta']}{RESET}\n")
    for i, opcao in enumerate(questao["opcoes"]):
        print(f"  {NEGRITO}{LETRAS[i]}{RESET}) {opcao}")

    validas = LETRAS[: len(questao["opcoes"])]
    while True:
        resp = input(f"\nSua resposta ({'/'.join(validas)}) — ou 'q' pra sair: ").strip().upper()
        if resp == "Q":
            return None
        if len(resp) == 1 and resp in validas:
            return LETRAS.index(resp)
        print(f"{AMARELO}Digite uma das letras: {', '.join(validas)}{RESET}")


def _mostrar_feedback(questao, escolha):
    """Feedback baseado na alternativa escolhida (usado principalmente nas provas)."""
    correta = questao["correta"]
    feedbacks = questao.get("feedbacks")
    acertou = escolha == correta

    if acertou:
        print(f"{VERDE}✔ Correto!{RESET}")
    else:
        print(f"{VERMELHO}✗ Errado.{RESET}")

    # 1) por que a SUA escolha está certa/errada
    if feedbacks and escolha < len(feedbacks) and feedbacks[escolha]:
        marca = "sua resposta"
        cor = VERDE if acertou else VERMELHO
        print(f"{cor}→ {LETRAS[escolha]}) ({marca}): {feedbacks[escolha]}{RESET}")

    # 2) se errou, qual é a certa e por quê
    if not acertou:
        print(f"{NEGRITO}Resposta certa: {LETRAS[correta]}) {questao['opcoes'][correta]}{RESET}")
        if feedbacks and correta < len(feedbacks) and feedbacks[correta]:
            print(f"{VERDE}→ por que a {LETRAS[correta]} é a certa: {feedbacks[correta]}{RESET}")

    # 3) justificativa geral (se houver e ainda não coberta)
    if questao.get("explicacao"):
        print(f"{CINZA}ℹ {questao['explicacao']}{RESET}")

    return acertou


def run_quiz(caminho_json, embaralhar=True):
    dados = carregar_questoes(caminho_json)
    questoes = list(dados["questoes"])
    if embaralhar:
        random.shuffle(questoes)

    total = len(questoes)
    aprovacao = dados.get("aprovacao", 70)
    print(f"{NEGRITO}{AZUL}=== {dados.get('titulo', 'Quiz')} ==={RESET}")
    print(f"{total} questões. Responda com a letra. Aprovação: {aprovacao}%. Boa sorte!\n")

    acertos = 0
    erradas = []
    respondidas = 0
    for idx, questao in enumerate(questoes, start=1):
        escolha = _perguntar(questao, idx, total)
        if escolha is None:
            print(f"\n{AMARELO}Interrompido.{RESET}")
            break
        respondidas += 1
        if _mostrar_feedback(questao, escolha):
            acertos += 1
        else:
            erradas.append(questao)
    else:
        _resumo(acertos, total, erradas, aprovacao)
        return

    _resumo(acertos, respondidas, erradas, aprovacao, parcial=True)


def _resumo(acertos, total, erradas, aprovacao, parcial=False):
    if total == 0:
        return
    pct = round(100 * acertos / total)
    aprovado = pct >= aprovacao
    cor = VERDE if aprovado else (AMARELO if pct >= 50 else VERMELHO)
    titulo = "RESULTADO PARCIAL" if parcial else "RESULTADO"
    print(f"\n{NEGRITO}{AZUL}=== {titulo} ==={RESET}")
    print(f"Acertos: {cor}{NEGRITO}{acertos}/{total} ({pct}%){RESET}")
    if not parcial:
        if aprovado:
            print(f"{VERDE}APROVADO! (mínimo {aprovacao}%) 🎉{RESET}")
        else:
            print(f"{VERMELHO}Não atingiu {aprovacao}%. Revise e tente de novo.{RESET}")
    if erradas:
        print(f"\n{NEGRITO}Tópicos pra revisar:{RESET}")
        for q in erradas:
            print(f"  • {q['pergunta']}")
