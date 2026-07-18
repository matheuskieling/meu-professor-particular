#!/usr/bin/env python3
"""
Prova do Módulo 19 — Projeto Final: prova final integradora do curso.

Uso:
    python3 AWS/provas/modulo-19/prova.py

Diferente do quiz da aula, a prova dá feedback por ALTERNATIVA: com base no que
você escolheu, explica por que sua resposta está certa ou errada, e — se errou —
qual é a certa e por quê. Aprovação: 70%.
"""

import os
import sys

# sobe até AWS/ e adiciona apps/ ao path pra reusar o motor
AWS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(AWS_DIR, "apps"))

from quiz_engine import run_quiz  # noqa: E402

QUESTOES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions.json")

if __name__ == "__main__":
    run_quiz(QUESTOES)
