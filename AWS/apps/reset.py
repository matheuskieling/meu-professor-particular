#!/usr/bin/env python3
"""
Reseta o progresso do curso — apaga o estado salvo de aulas e quizzes/provas.

O progresso fica em apps/.sessions/ (aula em andamento, respostas de quiz/prova).
Este script limpa esse estado para recomeçar do zero. Não toca em NENHUM conteúdo
do curso (teoria, prática, roteiros, questões) — só no seu progresso local.

Uso:
    python3 AWS/apps/reset.py            # reseta TODO o progresso do curso
    python3 AWS/apps/reset.py --id aula-01   # reseta só uma sessão específica
    python3 AWS/apps/reset.py --list     # lista as sessões existentes sem apagar
"""

import argparse
import glob
import os

APPS_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(APPS_DIR, ".sessions")


def _sessoes():
    return sorted(glob.glob(os.path.join(SESSIONS_DIR, "*.json")))


def main():
    parser = argparse.ArgumentParser(description="Reseta o progresso do curso (apaga apps/.sessions/).")
    parser.add_argument("--id", help="apaga só a sessão com esse id (ex.: aula-01, prova)")
    parser.add_argument("--list", action="store_true", help="lista as sessões e sai")
    args = parser.parse_args()

    sessoes = _sessoes()

    if args.list:
        if not sessoes:
            print("Nenhuma sessão em andamento — o curso já está no início.")
        else:
            print("Sessões em andamento:")
            for s in sessoes:
                print(f"  • {os.path.splitext(os.path.basename(s))[0]}")
        return

    if args.id:
        alvo = os.path.join(SESSIONS_DIR, f"{args.id}.json")
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
