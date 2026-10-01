"""Katalog publiczny Next.js (frontend/public) dla statycznych materiałów."""
import os
from pathlib import Path


def get_materialy_public_root() -> Path:
    env = os.environ.get("MATERIALY_PUBLIC_ROOT")
    if env:
        return Path(env).resolve()
    # backend/app/materialy_paths.py -> parents[2] = backend, [3] = root projektu
    root = Path(__file__).resolve().parent.parent.parent
    return (root / "frontend" / "public").resolve()
