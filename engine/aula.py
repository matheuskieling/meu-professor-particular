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
    revisao [--id NOME]                conteúdo estudado desde a última sessão + nº sugerido de perguntas
    marco   [--id NOME]                marca o ponto atual como "já revisado" (chamar após a revisão)
    backfill [--id NOME]               estima datas de beats já concluídos a partir das notas (retroativo)
    note "<texto>" [--id NOME]         registra uma nota/dúvida no ponto atual
    reset   [--id NOME]                apaga o progresso da aula

Datas de conclusão: cada `next` carimba `concluido_em[beat] = agora`. O `status` mostra a data ao
lado de cada beat e destaca o último concluído (responde "onde paramos?"). O relatório de progresso
do curso (visão geral + %) fica em `engine/progresso.py`.

Revisão espaçada: a cada retomada, `revisao` mostra os beats de teoria/prática vistos desde o último
`marco` (a "última sessão") e sugere quantas perguntas de revisão fazer — o tamanho acompanha o
volume de conteúdo. O instrutor oferece essa mini-prova ao aluno; depois chama `marco` para não
repetir o mesmo conteúdo na próxima vez.

Motor compartilhado: este driver vive em `engine/` e serve QUALQUER curso. O curso é
descoberto pelo caminho do roteiro (no `start`) ou por `--curso <dir>` / autodetecção
(nos demais comandos). O estado fica em `<curso>/.sessions/<id>.json` (versionado no
fork do aluno). O --id padrão deriva do roteiro.

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

import _common


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _fmt_dt(iso):
    """'2026-07-21T14:30:00+00:00' -> '21/07 14:30' (hora local). Robusto a valor faltando."""
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso).astimezone()
        return dt.strftime("%d/%m %H:%M")
    except (ValueError, TypeError):
        return None


def _default_id(roteiro):
    return f"aula-{roteiro.get('modulo', 'x')}"


def _load(session_id, curso=None):
    path = _common.state_path(session_id, curso=curso)
    state = _common.load_json(path)
    if state is None:
        raise SystemExit(
            f"Nenhuma aula '{session_id}' em andamento. Comece com: "
            f"engine/aula.py start <roteiro.json>"
        )
    return state


def _save(session_id, state, curso=None):
    _common.save_json(_common.state_path(session_id, curso=curso), state)


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
    curso_root = _common.curso_root_de_caminho(args.roteiro)
    state = {
        "roteiro_path": os.path.abspath(args.roteiro),
        "roteiro": roteiro,
        "pos": 0,
        "marco_sessao": 0,
        "status": {b["id"]: "pendente" for b in roteiro["beats"]},
        "concluido_em": {},
        "notes": [],
        "iniciado_em": _now(),
    }
    _common.save_json(_common.state_path(session_id, curso_root=curso_root), state)
    print(f"Aula iniciada: Módulo {roteiro.get('modulo', '?')} — {roteiro.get('titulo', '')}")
    print(f"{len(roteiro['beats'])} beats. Sessão: '{session_id}'.\n")
    _show_beat(state)


def _resolve_id(args, needs_default=False):
    return args.id or "aula-01"


def cmd_current(args):
    state = _load(args.id, args.curso)
    _show_beat(state)


def cmd_next(args):
    state = _load(args.id, args.curso)
    beats = _beats(state)
    if state["pos"] < len(beats):
        beat_id = beats[state["pos"]]["id"]
        state["status"][beat_id] = "visto"
        # carimba a data de conclusão do beat (primeira vez que é marcado como visto)
        state.setdefault("concluido_em", {}).setdefault(beat_id, _now())
        state["pos"] += 1
    _save(args.id, state, args.curso)
    _show_beat(state)


def cmd_back(args):
    state = _load(args.id, args.curso)
    if state["pos"] > 0:
        state["pos"] -= 1
    _save(args.id, state, args.curso)
    _show_beat(state)


def cmd_goto(args):
    state = _load(args.id, args.curso)
    beats = _beats(state)
    idx = next((i for i, b in enumerate(beats) if b["id"] == args.beat_id), None)
    if idx is None:
        raise SystemExit(f"Beat '{args.beat_id}' não existe neste roteiro.")
    state["pos"] = idx
    _save(args.id, state, args.curso)
    _show_beat(state)


def cmd_status(args):
    state = _load(args.id, args.curso)
    beats = _beats(state)
    r = state["roteiro"]
    concl = state.get("concluido_em", {})
    aprox = set(state.get("concluido_aprox", []))
    print(f"Aula: Módulo {r.get('modulo', '?')} — {r.get('titulo', '')}")
    print(f"Progresso: {state['pos']}/{len(beats)} beats.\n")
    for i, b in enumerate(beats):
        visto = state["status"].get(b["id"]) == "visto"
        marca = "▶" if i == state["pos"] else ("✔" if visto else "·")
        data = _fmt_dt(concl.get(b["id"]))
        quando = ""
        if data:
            quando = f"  · ~{data}" if b["id"] in aprox else f"  · {data}"
        elif visto:
            quando = "  · —"
        print(f"  {marca} {b['id']:>4}  [{b['fase']:<10}] {b['titulo']}{quando}")
    # último beat concluído — o beat logo antes da posição atual (onde paramos), com sua data
    ult = next((b for b in reversed(beats[:state["pos"]])
                if state["status"].get(b["id"]) == "visto"), None)
    if ult:
        data = _fmt_dt(concl.get(ult["id"]))
        quando = (f"~{data}" if ult["id"] in aprox else data) if data else "sem data"
        print(f"\nÚltimo beat concluído: {ult['id']} ({ult['titulo']}) — {quando}")
    if state.get("notes"):
        print("\nNotas registradas:")
        for n in state["notes"]:
            print(f"  - [{n['beat']}] ({n['ts']}) {n['text']}")


def _sugerir_n_perguntas(n_topicos):
    """Nº de perguntas de revisão acompanha o volume de conteúdo (mín. 2, máx. 6)."""
    if n_topicos <= 0:
        return 0
    return min(6, max(2, round(n_topicos / 2)))


def cmd_revisao(args):
    state = _load(args.id, args.curso)
    beats = _beats(state)
    marco = state.get("marco_sessao", 0)
    pos = state["pos"]
    # conteúdo estudado na última sessão: beats de teoria/prática entre o marco e a posição atual
    trecho = beats[marco:pos]
    conteudo = [b for b in trecho if b.get("fase") in ("teoria", "pratica")]

    if not conteudo:
        print("Sem conteúdo novo de teoria/prática desde a última revisão — pode seguir a aula direto.")
        return

    n = _sugerir_n_perguntas(len(conteudo))
    print(f"Conteúdo estudado desde a última sessão ({len(conteudo)} tópicos):")
    for b in conteudo:
        print(f"  • [{b['fase']}] {b['titulo']} (id: {b['id']})")
        for p in b.get("pontos", []):
            print(f"      - {p}")
        if b.get("ref"):
            print(f"      apoio: {b['ref']}")
    print(f"\nTamanho sugerido da revisão: ~{n} perguntas (escala com o volume de conteúdo).")
    print("— Instrução ao instrutor: PERGUNTE ao aluno se ele quer uma revisão rápida da última "
          f"sessão (~{n} perguntas). Se sim, elabore perguntas curtas sobre os tópicos acima "
          "(varie o formato), conduza uma a uma com feedback e comente o resultado — sugerindo "
          "reforço no que ele errar. Se não quiser, siga a aula. Em qualquer caso, ao terminar a "
          "revisão, rode 'aula.py marco' para não repetir esse conteúdo na próxima retomada.")


def cmd_marco(args):
    state = _load(args.id, args.curso)
    state["marco_sessao"] = state["pos"]
    _save(args.id, state, args.curso)
    print(f"Marco de revisão atualizado para a posição {state['pos']}. "
          "A próxima retomada vai revisar apenas o conteúdo novo a partir daqui.")


def cmd_backfill(args):
    """Estima a data de beats já concluídos (visto) a partir do ts das notas do beat.

    Retroativo e best-effort: só preenche beats que estão 'visto', ainda não têm
    data e possuem ao menos uma nota (usa a nota mais antiga). As datas assim
    inferidas são marcadas como aproximadas (aparecem com '~' no status/progresso).
    Beats sem nota permanecem sem data — nada é inventado.
    """
    state = _load(args.id, args.curso)
    concl = state.setdefault("concluido_em", {})
    aprox = set(state.get("concluido_aprox", []))
    # menor ts de nota por beat
    primeira_nota = {}
    for n in state.get("notes", []):
        b, ts = n.get("beat"), n.get("ts")
        if b and ts and (b not in primeira_nota or ts < primeira_nota[b]):
            primeira_nota[b] = ts
    novos = 0
    for b_id, visto in state.get("status", {}).items():
        if visto == "visto" and b_id not in concl and b_id in primeira_nota:
            concl[b_id] = primeira_nota[b_id]
            aprox.add(b_id)
            novos += 1
    state["concluido_aprox"] = sorted(aprox)
    _save(args.id, state, args.curso)
    sem_data = sum(1 for b_id, v in state.get("status", {}).items()
                   if v == "visto" and b_id not in concl)
    print(f"Backfill: {novos} beat(s) ganharam data aproximada (via notas). "
          f"{sem_data} beat(s) concluído(s) seguem sem data (nenhuma nota associada).")


def cmd_note(args):
    state = _load(args.id, args.curso)
    beats = _beats(state)
    beat_id = beats[state["pos"]]["id"] if state["pos"] < len(beats) else "fim"
    state.setdefault("notes", []).append({"beat": beat_id, "ts": _now(), "text": args.texto})
    _save(args.id, state, args.curso)
    print(f"Nota registrada no beat '{beat_id}'.")


def cmd_reset(args):
    path = _common.state_path(args.id, curso=args.curso)
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
        ("revisao", cmd_revisao, "conteúdo desde a última sessão + nº sugerido de perguntas"),
        ("marco", cmd_marco, "marca o ponto atual como já revisado"),
        ("backfill", cmd_backfill, "estima datas de beats já concluídos a partir das notas"),
        ("reset", cmd_reset, "apaga o progresso"),
    ]:
        p = sub.add_parser(name, help=helptext)
        p.add_argument("--id", default="aula-01", help="nome da sessão (padrão: aula-01)")
        p.add_argument("--curso", default=None, help="diretório do curso (autodetecta se omitido)")
        p.set_defaults(func=func)

    p = sub.add_parser("goto", help="pula para um beat")
    p.add_argument("beat_id", help="id do beat (ex.: t3, p2)")
    p.add_argument("--id", default="aula-01")
    p.add_argument("--curso", default=None, help="diretório do curso (autodetecta se omitido)")
    p.set_defaults(func=cmd_goto)

    p = sub.add_parser("note", help="registra uma nota/dúvida no beat atual")
    p.add_argument("texto", help="texto da nota")
    p.add_argument("--id", default="aula-01")
    p.add_argument("--curso", default=None, help="diretório do curso (autodetecta se omitido)")
    p.set_defaults(func=cmd_note)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
