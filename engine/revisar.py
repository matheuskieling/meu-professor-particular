#!/usr/bin/env python3
"""
Revisão acumulada com repetição espaçada (estilo Anki).

Diferente do recap da última sessão (`aula.py revisao`), este sistema monta uma
mini-prova amostrando de **todo o conteúdo já concluído** e agenda cada pergunta
para reaparecer de tempos em tempos — mais espaçada quando você acerta, mais cedo
quando erra (caixas de Leitner: 1, 3, 7, 16 e 35 dias).

Fonte das perguntas: os bancos que já existem (quizzes das aulas e provas dos
módulos). Só entram módulos **concluídos** (todos os beats de teoria/prática vistos
na aula), para nunca perguntar algo que o aluno ainda não estudou.

Histórico ("baralho"): <curso>/.sessions/revisao-deck.json — versionado no fork do
aluno, então acompanha entre máquinas. O reset.py limpa junto.

Motor compartilhado (vive em `engine/`, serve qualquer curso): informe `--curso <dir>`
ou deixe autodetectar (curso com sessão mais recente, ou o único existente).

Comandos:
    revisar.py nova [--n N] [--ate NN] [--id revisao] [--curso DIR]
        Monta uma mini-prova (N perguntas, priorizando vencidas + novas + aleatórias)
        e a inicia via session.py. Depois responda com:
            python3 engine/session.py answer <letra(s)> --id revisao
    revisar.py fechar [--id revisao] [--curso DIR]
        Lê a mini-prova respondida e atualiza o agendamento de cada pergunta.
    revisar.py status [--curso DIR]
        Mostra o estado do baralho (rastreadas, dominadas, vencidas hoje, disponíveis).

Opções:
    --n N       nº de perguntas da mini-prova (padrão 8; limitado ao que há disponível)
    --ate NN    força incluir os módulos 01..NN mesmo sem sessão de aula (p/ quem estuda solo)
"""

import argparse
import glob
import json
import os
import random
import subprocess
import sys
from datetime import date

import _common

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_PY = os.path.join(ENGINE_DIR, "session.py")
LETRAS = "ABCDEFGH"


def _resolver_curso(preferido):
    root = _common.detectar_curso_root(preferido)
    if not root:
        raise SystemExit("Curso não detectado; informe --curso <dir>.")
    sess = _common.sessions_dir(root)
    return root, sess, os.path.join(sess, "revisao-deck.json")

# Caixas de Leitron: intervalo em dias até a pergunta ficar "vencida" de novo.
INTERVALOS = {1: 1, 2: 3, 3: 7, 4: 16, 5: 35}


def _hoje():
    return date.today()


def _load(path, default=None):
    if not os.path.exists(path):
        return {} if default is None else default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _num_modulo(path):
    """Extrai 'NN' de .../modulo-NN/questions.json."""
    return os.path.basename(os.path.dirname(path)).split("-")[-1]


def _modulos_concluidos(sessions_dir):
    """Módulos cujos beats de teoria/prática foram todos vistos na aula."""
    concluidos = set()
    for sess in glob.glob(os.path.join(sessions_dir, "aula-*.json")):
        st = _load(sess)
        roteiro = st.get("roteiro", {})
        beats = roteiro.get("beats", [])
        ensino = [b for b in beats if b.get("fase") in ("teoria", "pratica")]
        if ensino and all(st.get("status", {}).get(b["id"]) == "visto" for b in ensino):
            if roteiro.get("modulo"):
                concluidos.add(roteiro["modulo"])
    return concluidos


def _pool(mods, course_root):
    """Todas as questões dos módulos elegíveis, com um qid estável cada."""
    pool = []
    for tipo, base in (("quiz", os.path.join(course_root, "apps", "modulo-*", "questions.json")),
                       ("prova", os.path.join(course_root, "provas", "modulo-*", "questions.json"))):
        for path in sorted(glob.glob(base)):
            nn = _num_modulo(path)
            if nn not in mods:
                continue
            banco = _load(path)
            for i, q in enumerate(banco.get("questoes", [])):
                qid = f"m{nn}-{tipo}#{i}"
                pool.append((qid, q))
    return pool


def _vencida(meta, hoje):
    dias = (hoje - date.fromisoformat(meta["ultima"])).days
    return dias >= INTERVALOS.get(meta.get("caixa", 1), 1)


def _selecionar(pool, deck, n, hoje):
    """Prioriza vencidas (mais atrasadas primeiro), depois novas, depois aleatórias."""
    vencidas, novas, resto = [], [], []
    for qid, q in pool:
        meta = deck.get(qid)
        if not meta:
            novas.append((qid, q))
        elif _vencida(meta, hoje):
            atraso = (hoje - date.fromisoformat(meta["ultima"])).days - INTERVALOS[meta["caixa"]]
            vencidas.append((atraso, qid, q))
        else:
            resto.append((qid, q))
    vencidas.sort(key=lambda x: -x[0])
    random.shuffle(novas)
    random.shuffle(resto)
    ordenada = [(qid, q) for _, qid, q in vencidas] + novas + resto
    escolhidas = ordenada[:n]
    random.shuffle(escolhidas)  # embaralha a ordem da mini-prova
    return escolhidas, len(vencidas), len(novas)


def cmd_nova(args):
    course_root, sessions_dir, deck_path = _resolver_curso(args.curso)
    if args.ate:
        mods = {f"{i:02d}" for i in range(1, int(args.ate) + 1)}
    else:
        mods = _modulos_concluidos(sessions_dir)

    if not mods:
        print("Ainda não há módulos concluídos para a revisão acumulada.")
        print("Termine ao menos um módulo (ou use --ate NN para incluir os módulos 01..NN).")
        return

    pool = _pool(mods, course_root)
    if not pool:
        print("Nenhum banco de questões encontrado para os módulos elegíveis.")
        return

    deck = _load(deck_path, {})
    hoje = _hoje()
    n = min(args.n, len(pool))
    escolhidas, n_venc, n_novas = _selecionar(pool, deck, n, hoje)

    mods_txt = ", ".join(sorted(mods))
    bank = {
        "titulo": f"Revisão acumulada — {len(escolhidas)} perguntas (módulos: {mods_txt})",
        "aprovacao": 70,
        "questoes": [],
    }
    for qid, q in escolhidas:
        item = dict(q)
        item["qid"] = qid  # rastreio; o session.py ignora campos extras
        bank["questoes"].append(item)

    bank_path = os.path.join(sessions_dir, "revisao-bank.json")
    _save(bank_path, bank)

    print(f"Mini-prova de revisão: {len(escolhidas)} perguntas de {len(mods)} módulo(s) "
          f"[{mods_txt}].")
    print(f"(prioridade: {min(n_venc, n)} vencida(s), {n_novas} nova(s) no baralho; "
          f"restante sorteado do já visto)")
    print("Conduza normalmente; ao final rode: python3 engine/revisar.py fechar\n")

    # inicia a sessão de perguntas reutilizando o motor de sempre (sem embaralhar de novo)
    subprocess.run(
        [sys.executable, SESSION_PY, "start", bank_path, "--id", args.id, "--no-shuffle"],
        check=True,
    )


def cmd_fechar(args):
    course_root, sessions_dir, deck_path = _resolver_curso(args.curso)
    sess_path = os.path.join(sessions_dir, f"{args.id}.json")
    state = _load(sess_path)
    if not state:
        raise SystemExit("Nenhuma mini-prova de revisão para fechar. Rode 'revisar.py nova' antes.")
    if state.get("revisao_processada"):
        print("Esta mini-prova já foi processada no baralho.")
        return

    deck = _load(deck_path, {})
    hoje = _hoje()
    ordem = state["order"]
    questoes = state["bank"]["questoes"]

    subiu, caiu = 0, 0
    for a in state.get("answers", []):
        q = questoes[ordem[a["pos"]]]
        qid = q.get("qid")
        if not qid:
            continue
        meta = deck.get(qid, {"caixa": 1, "vezes": 0, "acertos": 0})
        meta["vezes"] += 1
        if a["acertou"]:
            meta["acertos"] += 1
            meta["caixa"] = min(5, meta.get("caixa", 1) + 1)
            subiu += 1
        else:
            meta["caixa"] = 1
            caiu += 1
        meta["ultima"] = hoje.isoformat()
        from datetime import timedelta
        meta["proxima"] = (hoje + timedelta(days=INTERVALOS[meta["caixa"]])).isoformat()
        deck[qid] = meta

    _save(deck_path, deck)
    state["revisao_processada"] = True
    _save(sess_path, state)

    acertos = sum(1 for a in state.get("answers", []) if a["acertou"])
    total = len(state.get("answers", []))
    print(f"Revisão processada: {acertos}/{total} acertos.")
    print(f"Agendamento atualizado — {subiu} pergunta(s) subiram de caixa (voltam mais tarde), "
          f"{caiu} volta(ram) pra caixa 1 (reaparecem logo).")
    _resumo_baralho(deck, hoje)


def cmd_status(args):
    _, _, deck_path = _resolver_curso(args.curso)
    deck = _load(deck_path, {})
    if not deck:
        print("Baralho de revisão vazio ainda. Rode 'revisar.py nova' após concluir um módulo.")
        return
    _resumo_baralho(deck, _hoje())


def _resumo_baralho(deck, hoje):
    total = len(deck)
    dominadas = sum(1 for m in deck.values() if m.get("caixa", 1) >= 5)
    vencidas = sum(1 for m in deck.values() if _vencida(m, hoje))
    print(f"Baralho: {total} perguntas rastreadas · {dominadas} dominadas (caixa 5) · "
          f"{vencidas} vencida(s) para revisar.")


def main():
    parser = argparse.ArgumentParser(description="Revisão acumulada com repetição espaçada (Anki-like).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("nova", help="monta e inicia uma mini-prova de revisão")
    p.add_argument("--n", type=int, default=8, help="nº de perguntas (padrão 8)")
    p.add_argument("--ate", help="força incluir módulos 01..NN (para estudo solo)")
    p.add_argument("--id", default="revisao", help="id da sessão (padrão: revisao)")
    p.add_argument("--curso", default=None, help="diretório do curso (autodetecta se omitido)")
    p.set_defaults(func=cmd_nova)

    p = sub.add_parser("fechar", help="processa a mini-prova respondida no baralho")
    p.add_argument("--id", default="revisao")
    p.add_argument("--curso", default=None, help="diretório do curso (autodetecta se omitido)")
    p.set_defaults(func=cmd_fechar)

    p = sub.add_parser("status", help="mostra o estado do baralho")
    p.add_argument("--curso", default=None, help="diretório do curso (autodetecta se omitido)")
    p.set_defaults(func=cmd_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
