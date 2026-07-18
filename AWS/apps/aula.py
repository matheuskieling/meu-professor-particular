#!/usr/bin/env python3
"""
Driver de AULA ao vivo — feito para o Claude conduzir um one-on-one.

A aula não é um arquivo que o aluno lê sozinho: é uma conversa guiada. Este driver
guarda o ROTEIRO (a lista ordenada de "beats" — os pontos que o Claude quer ensinar)
e o PROGRESSO (onde paramos), persistindo em arquivo. Assim dá pra parar e retomar
sempre de onde ficou.

Quem ENSINA é o Claude: o driver só entrega o próximo beat (título + pontos-chave +
a deixa de checkpoint) e registra o avanço. O Claude narra em linguagem natural,
tira dúvidas e pergunta "posso continuar?" antes de chamar `next`.

Comandos:
    start <roteiro.json> [--id NOME]   inicia/zera a aula e mostra o beat atual
    current [--id NOME]                mostra o beat atual (retomar de onde paramos)
    next    [--id NOME]                marca o beat atual como visto e avança
    back    [--id NOME]                volta um beat
    goto <beat-id> [--id NOME]         pula para um beat específico
    status  [--id NOME]                mapa de progresso (o que já vimos e o que falta)
    note "<texto>" [--id NOME]         registra uma nota/dúvida no ponto atual
    reset   [--id NOME]                apaga o progresso da aula

Estado em AWS/apps/.sessions/<id>.json (gitignored). O --id padrão deriva do roteiro.

Formato do roteiro.json:
{
  "modulo": "01",
  "titulo": "Fundamentos de Cloud & AWS",
  "beats": [
    {
      "id": "t1",
      "fase": "teoria",                 # teoria | pratica | quiz | prova | fechamento
      "titulo": "O que é a nuvem",
      "pontos": ["cue 1", "cue 2"],     # pontos que o Claude vai desenvolver
      "checkpoint": "pergunte se ...",  # deixa para a pausa "posso continuar?"
      "acao": "rodar session.py ...",   # (opcional) ação concreta na prática/teste
      "ref": "01-fundamentos/teoria.md#secao"   # (opcional) referência de apoio
    }
  ]
}
"""

import argparse
import json
import os
from datetime import datetime, timezone

APPS_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(APPS_DIR, ".sessions")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _state_path(session_id):
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")


def _default_id(roteiro):
    return f"aula-{roteiro.get('modulo', 'x')}"


def _load(session_id):
    path = _state_path(session_id)
    if not os.path.exists(path):
        raise SystemExit(
            f"Nenhuma aula '{session_id}' em andamento. Comece com: "
            f"aula.py start <roteiro.json> --id {session_id}"
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(session_id, state):
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    with open(_state_path(session_id), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _beats(state):
    return state["roteiro"]["beats"]


def _show_beat(state):
    beats = _beats(state)
    pos = state["pos"]
    total = len(beats)
    if pos >= total:
        print("🎓 Roteiro concluído! Use 'status' para revisar ou 'reset' para recomeçar.")
        return
    b = beats[pos]
    print(f"══ Beat {pos + 1}/{total} · [{b['fase'].upper()}] · {b['titulo']} "
          f"(id: {b['id']}) ══")
    if b.get("pontos"):
        print("Pontos a desenvolver:")
        for p in b["pontos"]:
            print(f"  • {p}")
    if b.get("acao"):
        print(f"Ação: {b['acao']}")
    if b.get("ref"):
        print(f"Apoio: {b['ref']}")
    if b.get("checkpoint"):
        print(f"Checkpoint: {b['checkpoint']}")
    print("— Lembrete ao instrutor: narre com suas palavras, não despeje tudo de uma vez; "
          "convide dúvidas e pergunte 'posso continuar?' antes de 'next'.")
    notas = [n for n in state.get("notes", []) if n["beat"] == b["id"]]
    if notas:
        print("Notas deste beat:")
        for n in notas:
            print(f"  - ({n['ts']}) {n['text']}")


def cmd_start(args):
    with open(args.roteiro, "r", encoding="utf-8") as f:
        roteiro = json.load(f)
    session_id = args.id or _default_id(roteiro)
    state = {
        "roteiro_path": os.path.abspath(args.roteiro),
        "roteiro": roteiro,
        "pos": 0,
        "status": {b["id"]: "pendente" for b in roteiro["beats"]},
        "notes": [],
        "iniciado_em": _now(),
    }
    _save(session_id, state)
    print(f"Aula iniciada: Módulo {roteiro.get('modulo', '?')} — {roteiro.get('titulo', '')}")
    print(f"{len(roteiro['beats'])} beats. Sessão: '{session_id}'.\n")
    _show_beat(state)


def _resolve_id(args, needs_default=False):
    return args.id or "aula-01"


def cmd_current(args):
    state = _load(args.id)
    _show_beat(state)


def cmd_next(args):
    state = _load(args.id)
    beats = _beats(state)
    if state["pos"] < len(beats):
        state["status"][beats[state["pos"]]["id"]] = "visto"
        state["pos"] += 1
    _save(args.id, state)
    _show_beat(state)


def cmd_back(args):
    state = _load(args.id)
    if state["pos"] > 0:
        state["pos"] -= 1
    _save(args.id, state)
    _show_beat(state)


def cmd_goto(args):
    state = _load(args.id)
    beats = _beats(state)
    idx = next((i for i, b in enumerate(beats) if b["id"] == args.beat_id), None)
    if idx is None:
        raise SystemExit(f"Beat '{args.beat_id}' não existe neste roteiro.")
    state["pos"] = idx
    _save(args.id, state)
    _show_beat(state)


def cmd_status(args):
    state = _load(args.id)
    beats = _beats(state)
    r = state["roteiro"]
    print(f"Aula: Módulo {r.get('modulo', '?')} — {r.get('titulo', '')}")
    print(f"Progresso: {state['pos']}/{len(beats)} beats.\n")
    for i, b in enumerate(beats):
        marca = "▶" if i == state["pos"] else ("✔" if state["status"].get(b["id"]) == "visto" else "·")
        print(f"  {marca} {b['id']:>4}  [{b['fase']:<10}] {b['titulo']}")
    if state.get("notes"):
        print("\nNotas registradas:")
        for n in state["notes"]:
            print(f"  - [{n['beat']}] ({n['ts']}) {n['text']}")


def cmd_note(args):
    state = _load(args.id)
    beats = _beats(state)
    beat_id = beats[state["pos"]]["id"] if state["pos"] < len(beats) else "fim"
    state.setdefault("notes", []).append({"beat": beat_id, "ts": _now(), "text": args.texto})
    _save(args.id, state)
    print(f"Nota registrada no beat '{beat_id}'.")


def cmd_reset(args):
    path = _state_path(args.id)
    if os.path.exists(path):
        os.remove(path)
        print(f"Aula '{args.id}' apagada.")
    else:
        print(f"Nenhuma aula '{args.id}' pra apagar.")


def main():
    parser = argparse.ArgumentParser(description="Driver de aula ao vivo conduzida pelo Claude.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("start", help="inicia/zera a aula")
    p.add_argument("roteiro", help="caminho do roteiro.json")
    p.add_argument("--id", default=None, help="nome da sessão (padrão: aula-<modulo>)")
    p.set_defaults(func=cmd_start)

    for name, func, helptext in [
        ("current", cmd_current, "mostra o beat atual"),
        ("next", cmd_next, "avança para o próximo beat"),
        ("back", cmd_back, "volta um beat"),
        ("status", cmd_status, "mapa de progresso"),
        ("reset", cmd_reset, "apaga o progresso"),
    ]:
        p = sub.add_parser(name, help=helptext)
        p.add_argument("--id", default="aula-01", help="nome da sessão (padrão: aula-01)")
        p.set_defaults(func=func)

    p = sub.add_parser("goto", help="pula para um beat")
    p.add_argument("beat_id", help="id do beat (ex.: t3, p2)")
    p.add_argument("--id", default="aula-01")
    p.set_defaults(func=cmd_goto)

    p = sub.add_parser("note", help="registra uma nota/dúvida no beat atual")
    p.add_argument("texto", help="texto da nota")
    p.add_argument("--id", default="aula-01")
    p.set_defaults(func=cmd_note)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
