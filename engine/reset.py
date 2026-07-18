#!/usr/bin/env python3
"""
Reseta o progresso de um curso — apaga o estado salvo de aulas, quizzes/provas e o
baralho de revisão. Não toca em NENHUM conteúdo do curso (teoria, prática, roteiros,
questões) — só no progresso local (`<curso>/.sessions/`).

Motor compartilhado (vive em `engine/`, serve qualquer curso): informe `--curso <dir>`
ou deixe autodetectar (curso com sessão mais recente, ou o único existente).

Uso:
    python3 engine/reset.py --curso AWS            # reseta TODO o progresso do curso
    python3 engine/reset.py --curso AWS --id aula-01   # reseta só uma sessão
    python3 engine/reset.py --curso AWS --list     # lista as sessões sem apagar
"""

import argparse
import glob
import os

import _common


def _sessions_dir(curso):
    root = _common.detectar_curso_root(curso)
    if not root:
        raise SystemExit("Curso não detectado; informe --curso <dir>.")
    return _common.sessions_dir(root)


def _sessoes(sessions_dir):
    return sorted(glob.glob(os.path.join(sessions_dir, "*.json")))


def main():
    parser = argparse.ArgumentParser(description="Reseta o progresso de um curso (apaga <curso>/.sessions/).")
    parser.add_argument("--curso", default=None, help="diretório do curso (autodetecta se omitido)")
    parser.add_argument("--id", help="apaga só a sessão com esse id (ex.: aula-01, prova)")
    parser.add_argument("--list", action="store_true", help="lista as sessões e sai")
    args = parser.parse_args()

    sessions_dir = _sessions_dir(args.curso)
    sessoes = _sessoes(sessions_dir)

    if args.list:
        if not sessoes:
            print("Nenhuma sessão em andamento — o curso já está no início.")
        else:
            print("Sessões em andamento:")
            for s in sessoes:
                print(f"  • {os.path.splitext(os.path.basename(s))[0]}")
        return

    if args.id:
        alvo = os.path.join(sessions_dir, f"{args.id}.json")
        if os.path.exists(alvo):
            os.remove(alvo)
            print(f"Sessão '{args.id}' resetada.")
        else:
            print(f"Nenhuma sessão '{args.id}' encontrada.")
        return

    if not sessoes:
        print("Nada para resetar — o curso já está no início. 🌱")
        return

    for s in sessoes:
        os.remove(s)
    print(f"Progresso resetado: {len(sessoes)} sessão(ões) apagada(s). O curso voltou ao início. 🌱")
    print("Use a skill /retomar-curso (ou 'vamos começar o módulo 1') para recomeçar.")


if __name__ == "__main__":
    main()
