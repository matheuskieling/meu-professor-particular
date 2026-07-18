"""
Resolução de curso/sessão compartilhada pelos drivers do `engine/`.

O `engine/` é único e serve TODOS os cursos da plataforma. Cada curso é um diretório
direto na raiz do repositório (ex.: `AWS/`, `Design-Patterns/`) e guarda seu próprio
progresso em `<curso>/.sessions/`. Estas funções descobrem, a partir de um caminho de
conteúdo (roteiro/banco) ou de um id de sessão, a qual curso a operação pertence — sem
o driver precisar morar dentro do curso.
"""

import glob
import json
import os

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(ENGINE_DIR)


def curso_root_de_caminho(caminho):
    """Curso ao qual um arquivo de conteúdo pertence (1º segmento sob a raiz do repo)."""
    rel = os.path.relpath(os.path.abspath(caminho), REPO_ROOT)
    seg = rel.split(os.sep)[0]
    if seg in ("", "..", "engine"):
        raise SystemExit(f"Caminho fora de um curso: {caminho}")
    return os.path.join(REPO_ROOT, seg)


def sessions_dir(curso_root):
    return os.path.join(curso_root, ".sessions")


def _todas_sessions(session_id="*"):
    return glob.glob(os.path.join(REPO_ROOT, "*", ".sessions", f"{session_id}.json"))


def detectar_curso_root(preferido=None):
    """Descobre o curso: --curso explícito > sessão mais recente > único curso com apps/."""
    if preferido:
        root = os.path.join(REPO_ROOT, preferido)
        if not os.path.isdir(root):
            raise SystemExit(f"Curso '{preferido}' não encontrado na raiz do repositório.")
        return root
    sess = _todas_sessions()
    if sess:
        mais_nova = max(sess, key=os.path.getmtime)
        return os.path.dirname(os.path.dirname(mais_nova))
    cursos = [d for d in glob.glob(os.path.join(REPO_ROOT, "*"))
              if os.path.isdir(os.path.join(d, "apps"))]
    if len(cursos) == 1:
        return cursos[0]
    return None


def state_path(session_id, curso=None, curso_root=None):
    """Caminho do arquivo de estado da sessão, resolvendo o curso quando necessário."""
    if curso_root is None:
        if curso:
            curso_root = os.path.join(REPO_ROOT, curso)
        else:
            hits = _todas_sessions(session_id)
            if len(hits) == 1:
                return hits[0]
            if len(hits) > 1:
                raise SystemExit(
                    f"Sessão '{session_id}' existe em mais de um curso; use --curso <dir>.")
            curso_root = detectar_curso_root()
            if not curso_root:
                raise SystemExit("Curso não detectado; informe --curso <dir>.")
    return os.path.join(sessions_dir(curso_root), f"{session_id}.json")


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
