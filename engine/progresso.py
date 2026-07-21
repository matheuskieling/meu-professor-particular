#!/usr/bin/env python3
"""
Relatório de PROGRESSO de um curso — visão geral (não conduz aula, só reporta).

Diferente do `aula.py status` (que olha UMA sessão/módulo), este driver varre o curso
INTEIRO: soma os beats de todos os módulos (`<curso>/NN-*/roteiro.json`) e cruza com o
progresso salvo (`<curso>/.sessions/aula-*.json`) para mostrar:

  • % de cada módulo (barra + concluídos/total);
  • % do curso completo (beats e módulos concluídos);
  • o último beat concluído e quando (responde "onde paramos?");
  • o ritmo (beats concluídos por dia), a partir das datas que o `aula.py` carimba.

É agnóstico de curso: descobre o curso por `--curso <dir>` ou autodetecção (mesma regra
dos outros drivers). Só leitura — nunca altera progresso.

Uso:
    python3 engine/progresso.py [--curso AWS]
"""

import argparse
import glob
import json
import os
from datetime import datetime

import _common

BAR_WIDTH = 20


def _fmt_dt(iso):
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso).astimezone().strftime("%d/%m %H:%M")
    except (ValueError, TypeError):
        return None


def _bar(frac):
    cheio = round(frac * BAR_WIDTH)
    return "█" * cheio + "░" * (BAR_WIDTH - cheio)


def _modulos(curso_root):
    """Lista (roteiro, session_state) por módulo, ordenada pelo número do módulo."""
    out = []
    for rot_path in sorted(glob.glob(os.path.join(curso_root, "[0-9]*", "roteiro.json"))):
        try:
            roteiro = _common.load_json(rot_path)
        except json.JSONDecodeError:
            continue
        if not roteiro or "beats" not in roteiro:
            continue
        modulo = roteiro.get("modulo", os.path.basename(os.path.dirname(rot_path)))
        sess_path = os.path.join(_common.sessions_dir(curso_root), f"aula-{modulo}.json")
        state = _common.load_json(sess_path)  # None se ainda não iniciado
        out.append((modulo, roteiro, state))
    return out


def cmd_progresso(args):
    curso_root = _common.detectar_curso_root(args.curso)
    if not curso_root:
        raise SystemExit("Curso não detectado; informe --curso <dir>.")
    curso_nome = os.path.basename(curso_root.rstrip(os.sep))
    mods = _modulos(curso_root)
    if not mods:
        raise SystemExit(f"Nenhum módulo com roteiro.json encontrado em {curso_nome}.")

    tot_beats = tot_feitos = mods_concluidos = 0
    por_dia = {}
    ultimo = None  # (chave_ordem, modulo, beat_id, ts)
    dados = []  # (modulo, roteiro, state, feitos, n, concluido)

    for modulo, roteiro, state in mods:
        beats = roteiro["beats"]
        n = len(beats)
        status = (state or {}).get("status", {})
        concl = (state or {}).get("concluido_em", {})
        aprox = set((state or {}).get("concluido_aprox", []))
        feitos = sum(1 for b in beats if status.get(b["id"]) == "visto")
        tot_beats += n
        tot_feitos += feitos
        concluido = n > 0 and feitos == n
        if concluido:
            mods_concluidos += 1
        # ritmo + último beat, a partir das datas carimbadas
        idx = {b["id"]: i for i, b in enumerate(beats)}
        for b_id, ts in concl.items():
            dia = ts[:10]
            por_dia[dia] = por_dia.get(dia, 0) + 1
            # ordena por (data, módulo, posição do beat) — desempata beats do mesmo segundo
            chave = (ts, modulo, idx.get(b_id, -1))
            if ultimo is None or chave > ultimo[0]:
                ultimo = (chave, modulo, b_id, ts)
        dados.append((modulo, roteiro, state, feitos, n, concluido))

    # o módulo "atual" é o do último beat concluído; sem datas, o último em progresso
    modulo_atual = ultimo[1] if ultimo else next(
        (m for m, r, s, f, n, c in reversed(dados) if s is not None and not c), None)

    linhas = []
    for modulo, roteiro, state, feitos, n, concluido in dados:
        frac = feitos / n if n else 0
        atual = modulo == modulo_atual
        marca = "✅" if concluido else ("▶ " if atual else "· ")
        seta = "   ← aqui" if atual else ""
        linhas.append(f"  {marca} {modulo} {roteiro.get('titulo', '')[:34]:<34} {_bar(frac)} "
                      f"{round(frac*100):>3}%  ({feitos}/{n}){seta}")

    frac_curso = tot_feitos / tot_beats if tot_beats else 0
    print(f"📊 Progresso — Curso {curso_nome}\n")
    print(f"Curso completo   {_bar(frac_curso)}  {round(frac_curso*100)}%   "
          f"({tot_feitos}/{tot_beats} beats · {mods_concluidos}/{len(mods)} módulos ✅)\n")
    print("Por módulo:")
    for ln in linhas:
        print(ln)

    if ultimo:
        _chave, modulo, b_id, ts = ultimo
        roteiro, state = next((r, s) for m, r, s in mods if m == modulo)
        titulo = next((b["titulo"] for b in roteiro["beats"] if b["id"] == b_id), b_id)
        ap = "~" if b_id in set((state or {}).get("concluido_aprox", [])) else ""
        print(f"\nÚltimo beat concluído: Módulo {modulo} · {b_id} ({titulo}) — {ap}{_fmt_dt(ts)}")

    if por_dia:
        dias = sorted(por_dia)
        media = sum(por_dia.values()) / len(dias)
        recentes = dias[-7:]
        trecho = " · ".join(f"{d[8:10]}/{d[5:7]} → {por_dia[d]}" for d in recentes)
        prefixo = "Ritmo (beats/dia): " if len(dias) <= 7 else "Ritmo (últimos 7 dias): "
        print(f"{prefixo}{trecho}   (média {media:.1f}/dia nos dias ativos)")
    else:
        print("\nRitmo: ainda sem datas registradas (aparecem conforme você avança os beats).")


def main():
    parser = argparse.ArgumentParser(description="Relatório de progresso de um curso (visão geral).")
    parser.add_argument("--curso", default=None, help="diretório do curso (autodetecta se omitido)")
    parser.set_defaults(func=cmd_progresso)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
