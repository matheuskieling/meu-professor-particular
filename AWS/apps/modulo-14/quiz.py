#!/usr/bin/env python3
"""
Quiz do Módulo 14 — DNS & Entrega de Conteúdo.

Uso:
    python3 AWS/apps/modulo-14/quiz.py

Testa o que foi visto em 14-dns-cdn/teoria.md e pratica.md.
"""

import os
import sys

ENGINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), *[os.pardir]*3, "engine")
sys.path.insert(0, os.path.abspath(ENGINE_DIR))

from quiz_engine import run_quiz  # noqa: E402

QUESTOES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions.json")

if __name__ == "__main__":
    run_quiz(QUESTOES)
