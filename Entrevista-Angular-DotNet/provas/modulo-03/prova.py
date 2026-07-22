#!/usr/bin/env python3
"""
Prova — Módulo 03 — Router, Lazy Loading, DI & Interceptors (Angular).

Uso:
    python3 Entrevista-Angular-DotNet/provas/modulo-03/prova.py

Curso Entrevista Angular + .NET (prep de entrevista).
"""

import os
import sys

ENGINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), *[os.pardir]*3, "engine")
sys.path.insert(0, os.path.abspath(ENGINE_DIR))

from quiz_engine import run_quiz  # noqa: E402

QUESTOES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions.json")

if __name__ == "__main__":
    run_quiz(QUESTOES)
