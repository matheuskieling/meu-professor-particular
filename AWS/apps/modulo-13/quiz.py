#!/usr/bin/env python3
"""
Quiz do Módulo 13 — Segurança Avançada.

Uso:
    python3 AWS/apps/modulo-13/quiz.py

Testa o que foi visto em 13-seguranca-avancada/teoria.md e pratica.md.
"""

import os
import sys

# permite importar o motor da pasta apps/ independente de onde você chama
APPS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APPS_DIR)

from quiz_engine import run_quiz  # noqa: E402

QUESTOES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions.json")

if __name__ == "__main__":
    run_quiz(QUESTOES)
