#!/usr/bin/env python3
"""
Driver de sessão de quiz/prova — feito para o Claude operar em segundo plano.

Diferente do modo "solo" (quiz_engine.py, que lê do teclado), este driver é uma
MÁQUINA DE ESTADO sem interação de stdin: cada comando faz uma coisa, imprime o
resultado e persiste o estado em arquivo. Assim o Claude conduz a prova pelo chat —
apresenta a pergunta, recebe sua resposta em linguagem natural, chama `answer` e
te explica o retorno.

Comandos:
    start <bank.json> [--id NOME] [--no-shuffle]   inicia uma sessão e mostra a Q1
    current [--id NOME]                            remostra a questão atual
    answer <A-H> [--id NOME]                       corrige, dá feedback e avança
    status  [--id NOME]                            progresso e nota parcial
    reset   [--id NOME]                            apaga a sessão

O estado fica em AWS/.sessions/<id>.json (ignorado pelo git). Uma sessão "ativa"
por vez basta para um aluno; use --id para rodar várias em paralelo (ex.: 'prova').

Formato do bank.json: igual ao do quiz_engine (titulo, aprovacao, questoes[]),
onde cada questão pode ter `feedbacks` (um retorno por alternativa) além de
`explicacao` (justificativa geral da correta).
"""

import argparse
import json
import os
import random

LETRAS = "ABCDEFGH"
APPS_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(APPS_DIR, ".sessions")


def _state_path(session_id):
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")


def _load_state(session_id):
    path = _state_path(session_id)
    if not os.path.exists(path):
        raise SystemExit(
            f"Nenhuma sessão '{session_id}' ativa. Rode primeiro: "
            f"session.py start <bank.json> --id {session_id}"
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_state(session_id, state):
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    with open(_state_path(session_id), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _bank_questao(state, pos):
    qi = state["order"][pos]
    return state["bank"]["questoes"][qi]


def _print_questao(state):
    pos = state["pos"]
    total = len(state["order"])
    q = _bank_questao(state, pos)
    print(f"[Questão {pos + 1}/{total}] — {state['bank'].get('titulo', '')}")
    print(f"Pergunta: {q['pergunta']}")
    for i, opc in enumerate(q["opcoes"]):
        print(f"  {LETRAS[i]}) {opc}")


def cmd_start(args):
    with open(args.bank, "r", encoding="utf-8") as f:
        bank = json.load(f)
    order = list(range(len(bank["questoes"])))
    if not args.no_shuffle:
        random.shuffle(order)
    state = {
        "bank_path": os.path.abspath(args.bank),
        "bank": bank,
        "order": order,
        "pos": 0,
        "answers": [],
        "done": False,
    }
    _save_state(args.id, state)
    print(f"Sessão '{args.id}' iniciada: {bank.get('titulo', '(sem título)')}")
    print(f"{len(order)} questões. Aprovação: {bank.get('aprovacao', 70)}%.\n")
    _print_questao(state)


def cmd_current(args):
    state = _load_state(args.id)
    if state["done"]:
        print("Sessão finalizada. Use 'status' para ver a nota ou 'reset' para recomeçar.")
        return
    _print_questao(state)


def cmd_answer(args):
    state = _load_state(args.id)
    if state["done"]:
        print("Sessão já finalizada. Use 'status' ou 'reset'.")
        return

    letra = args.letra.strip().upper()
    q = _bank_questao(state, state["pos"])
    validas = LETRAS[: len(q["opcoes"])]
    if len(letra) != 1 or letra not in validas:
        raise SystemExit(f"Resposta inválida '{args.letra}'. Use uma de: {', '.join(validas)}")

    escolha = LETRAS.index(letra)
    correta = q["correta"]
    acertou = escolha == correta
    feedbacks = q.get("feedbacks") or []

    print(f"Você respondeu: {letra}")
    print(f"Resultado: {'CORRETO ✔' if acertou else 'ERRADO ✗'}")
    if escolha < len(feedbacks) and feedbacks[escolha]:
        print(f"Sua escolha ({letra}): {feedbacks[escolha]}")
    if not acertou:
        print(f"Correta: {LETRAS[correta]}) {q['opcoes'][correta]}")
        if correta < len(feedbacks) and feedbacks[correta]:
            print(f"Por que {LETRAS[correta]}: {feedbacks[correta]}")
    if q.get("explicacao"):
        print(f"Nota: {q['explicacao']}")

    state["answers"].append({"pos": state["pos"], "escolha": escolha, "acertou": acertou})
    state["pos"] += 1

    if state["pos"] >= len(state["order"]):
        state["done"] = True
        _save_state(args.id, state)
        print("\n--- FIM DA SESSÃO ---")
        _print_resultado(state)
    else:
        _save_state(args.id, state)
        print("\n--- Próxima ---")
        _print_questao(state)


def _print_resultado(state):
    total = len(state["order"])
    acertos = sum(1 for a in state["answers"] if a["acertou"])
    respondidas = len(state["answers"])
    pct = round(100 * acertos / respondidas) if respondidas else 0
    aprovacao = state["bank"].get("aprovacao", 70)
    status = "APROVADO 🎉" if pct >= aprovacao else "REPROVADO"
    print(f"Nota: {acertos}/{respondidas} ({pct}%) — {status} (mínimo {aprovacao}%)")
    if respondidas < total:
        print(f"(sessão incompleta: {respondidas}/{total} respondidas)")
    erradas = [a for a in state["answers"] if not a["acertou"]]
    if erradas:
        print("Questões erradas (pra revisar):")
        for a in erradas:
            q = _bank_questao(state, a["pos"])
            print(f"  • {q['pergunta']}")


def cmd_status(args):
    state = _load_state(args.id)
    _print_resultado(state)
    if not state["done"]:
        print(f"Em andamento: questão {state['pos'] + 1}/{len(state['order'])}.")


def cmd_reset(args):
    path = _state_path(args.id)
    if os.path.exists(path):
        os.remove(path)
        print(f"Sessão '{args.id}' apagada.")
    else:
        print(f"Nenhuma sessão '{args.id}' pra apagar.")


def main():
    parser = argparse.ArgumentParser(description="Driver de quiz/prova conduzido pelo Claude.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("start", help="inicia uma sessão")
    p.add_argument("bank", help="caminho do questions.json")
    p.add_argument("--id", default="active", help="nome da sessão (padrão: active)")
    p.add_argument("--no-shuffle", action="store_true", help="mantém a ordem original")
    p.set_defaults(func=cmd_start)

    for name, func, helptext in [
        ("current", cmd_current, "remostra a questão atual"),
        ("status", cmd_status, "mostra progresso e nota"),
        ("reset", cmd_reset, "apaga a sessão"),
    ]:
        p = sub.add_parser(name, help=helptext)
        p.add_argument("--id", default="active", help="nome da sessão (padrão: active)")
        p.set_defaults(func=func)

    p = sub.add_parser("answer", help="responde a questão atual")
    p.add_argument("letra", help="a alternativa: A, B, C, ...")
    p.add_argument("--id", default="active", help="nome da sessão (padrão: active)")
    p.set_defaults(func=cmd_answer)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
