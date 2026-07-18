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

Motor compartilhado (vive em `engine/`, serve qualquer curso): o curso é descoberto
pelo caminho do banco (no `start`) ou por `--curso <dir>` / autodetecção. O estado
fica em `<curso>/.sessions/<id>.json` (versionado no fork). Use --id para rodar
várias sessões em paralelo (ex.: 'prova', 'cert', 'revisao').

Formato do bank.json: igual ao do quiz_engine (titulo, aprovacao, questoes[]),
onde cada questão pode ter `feedbacks` (um retorno por alternativa) além de
`explicacao` (justificativa geral da correta). Questões de MÚLTIPLA RESPOSTA
(estilo exame AWS, "Escolha DUAS") usam `corretas: [i, j]` no lugar de `correta`;
a resposta é dada como letras separadas por vírgula (ex.: `answer A,C`).
"""

import argparse
import json
import os
import random

import _common

LETRAS = "ABCDEFGH"


def _load_state(session_id, curso=None):
    path = _common.state_path(session_id, curso=curso)
    state = _common.load_json(path)
    if state is None:
        raise SystemExit(
            f"Nenhuma sessão '{session_id}' ativa. Rode primeiro: "
            f"engine/session.py start <bank.json> --id {session_id}"
        )
    return state


def _save_state(session_id, state, curso=None):
    _common.save_json(_common.state_path(session_id, curso=curso), state)


def _bank_questao(state, pos):
    qi = state["order"][pos]
    return state["bank"]["questoes"][qi]


def _print_questao(state):
    pos = state["pos"]
    total = len(state["order"])
    q = _bank_questao(state, pos)
    print(f"[Questão {pos + 1}/{total}] — {state['bank'].get('titulo', '')}")
    print(f"Pergunta: {q['pergunta']}")
    if q.get("corretas"):
        print(f"(múltipla resposta: selecione {len(q['corretas'])} alternativas, ex.: A,C)")
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
    curso_root = _common.curso_root_de_caminho(args.bank)
    _common.save_json(_common.state_path(args.id, curso_root=curso_root), state)
    print(f"Sessão '{args.id}' iniciada: {bank.get('titulo', '(sem título)')}")
    print(f"{len(order)} questões. Aprovação: {bank.get('aprovacao', 70)}%.\n")
    _print_questao(state)


def cmd_current(args):
    state = _load_state(args.id, args.curso)
    if state["done"]:
        print("Sessão finalizada. Use 'status' para ver a nota ou 'reset' para recomeçar.")
        return
    _print_questao(state)


def cmd_answer(args):
    state = _load_state(args.id, args.curso)
    if state["done"]:
        print("Sessão já finalizada. Use 'status' ou 'reset'.")
        return

    q = _bank_questao(state, state["pos"])
    validas = LETRAS[: len(q["opcoes"])]
    corretas = sorted(q["corretas"]) if q.get("corretas") else [q["correta"]]

    letras = sorted(set(args.letra.replace(",", " ").upper().split()))
    for letra in letras:
        if len(letra) != 1 or letra not in validas:
            raise SystemExit(f"Resposta inválida '{letra}'. Use letras entre: {', '.join(validas)}")
    if len(letras) != len(corretas):
        raise SystemExit(
            f"Esta questão pede {len(corretas)} alternativa(s); você marcou {len(letras)}."
        )

    escolhas = [LETRAS.index(letra) for letra in letras]
    acertou = escolhas == corretas
    feedbacks = q.get("feedbacks") or []

    print(f"Você respondeu: {', '.join(letras)}")
    print(f"Resultado: {'CORRETO ✔' if acertou else 'ERRADO ✗'}")
    for escolha in escolhas:
        if escolha < len(feedbacks) and feedbacks[escolha]:
            print(f"Sua escolha ({LETRAS[escolha]}): {feedbacks[escolha]}")
    if not acertou:
        certas_txt = ", ".join(f"{LETRAS[c]}) {q['opcoes'][c]}" for c in corretas)
        print(f"Correta(s): {certas_txt}")
        for c in corretas:
            if c not in escolhas and c < len(feedbacks) and feedbacks[c]:
                print(f"Por que {LETRAS[c]}: {feedbacks[c]}")
    if q.get("explicacao"):
        print(f"Nota: {q['explicacao']}")

    state["answers"].append({"pos": state["pos"], "escolha": escolhas, "acertou": acertou})
    state["pos"] += 1

    if state["pos"] >= len(state["order"]):
        state["done"] = True
        _save_state(args.id, state, args.curso)
        print("\n--- FIM DA SESSÃO ---")
        _print_resultado(state)
    else:
        _save_state(args.id, state, args.curso)
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
    state = _load_state(args.id, args.curso)
    _print_resultado(state)
    if not state["done"]:
        print(f"Em andamento: questão {state['pos'] + 1}/{len(state['order'])}.")


def cmd_reset(args):
    path = _common.state_path(args.id, curso=args.curso)
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
        p.add_argument("--curso", default=None, help="diretório do curso (autodetecta se omitido)")
        p.set_defaults(func=func)

    p = sub.add_parser("answer", help="responde a questão atual")
    p.add_argument("letra", help="a alternativa: A, B, C, ...")
    p.add_argument("--id", default="active", help="nome da sessão (padrão: active)")
    p.add_argument("--curso", default=None, help="diretório do curso (autodetecta se omitido)")
    p.set_defaults(func=cmd_answer)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
