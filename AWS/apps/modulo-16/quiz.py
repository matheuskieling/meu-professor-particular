#!/usr/bin/env python3
"""
Quiz do Módulo 16 — CI/CD & DevOps.

Uso:
    python3 AWS/apps/modulo-16/quiz.py

Testa o que foi visto em 16-cicd-devops/teoria.md e pratica.md.
"""

import os
import sys

ENGINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), *[os.pardir]*3, "engine")
sys.path.insert(0, os.path.abspath(ENGINE_DIR))

from quiz_engine import run_quiz  # noqa: E402

QUESTOES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions.json")

if __name__ == "__main__":
    run_quiz(QUESTOES)
