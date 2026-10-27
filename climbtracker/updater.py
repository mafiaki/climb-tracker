"""Actualizaciones desde GitHub Releases.

`check()` pregunta a GitHub cuál es la última versión publicada. `install()` baja
su zip y copia los archivos encima de la carpeta del programa sin tocar `data/`
(jugadores, ajustes y caché de cada uno). Después la app se reinicia sola.
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

VERSION = "1.0.0"
REPO = "mafiaki/climb-tracker"
REPO_URL = f"https://github.com/{REPO}"
_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
_KEEP = {"data", ".git"}  # nunca se tocan al actualizar
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _get(url: str, timeout: float) -> bytes:
    req = Request(url, headers={
        "User-Agent": f"ClimbTracker/{VERSION}",
        "Accept": "application/vnd.github+json",
    })
    with urlopen(req, timeout=timeout) as r:
        return r.read()


def _parse(version: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", version)[:3])


def check() -> dict:
    """Última versión publicada y si es más nueva que esta."""
    rel = json.loads(_get(_LATEST, timeout=10))
    latest = rel["tag_name"].lstrip("vV")
    return {
        "current": VERSION,
        "latest": latest,
        "available": _parse(latest) > _parse(VERSION),
        "notes": rel.get("body") or "",
        "url": rel.get("html_url") or REPO_URL,
        "zip": rel["zipball_url"],
    }


def install(app_dir: Path, zip_url: str) -> bool:
    """Copia la versión nueva encima de app_dir. Devuelve si cambió requirements.txt."""
    app_dir = app_dir.resolve()
    req_file = app_dir / "requirements.txt"
    old_req = req_file.read_bytes() if req_file.exists() else b""
    with zipfile.ZipFile(io.BytesIO(_get(zip_url, timeout=120))) as zf:
        for info in zf.infolist():
            # GitHub mete todo dentro de una carpeta "usuario-repo-commit/".
            parts = info.filename.split("/")[1:]
            if info.is_dir() or not parts or not parts[-1] or parts[0] in _KEEP:
                continue
            dest = app_dir.joinpath(*parts).resolve()
            if app_dir not in dest.parents:
                continue  # rutas raras que saldrían de la carpeta
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_name(dest.name + ".new")
            tmp.write_bytes(zf.read(info))
            os.replace(tmp, dest)
    return (req_file.read_bytes() if req_file.exists() else b"") != old_req


def install_requirements(app_dir: Path) -> None:
    python = Path(sys.executable).with_name("python.exe")
    if not python.exists():
        python = Path(sys.executable)
    subprocess.run(
        [str(python), "-m", "pip", "install", "-r", str(app_dir / "requirements.txt")],
        cwd=app_dir, creationflags=_NO_WINDOW, timeout=900, check=True,
    )


def restart(app_dir: Path) -> None:
    """Abre otra vez la app (la ventana actual se cierra después)."""
    subprocess.Popen(
        [sys.executable, str(app_dir / "Climb Tracker.pyw")],
        cwd=app_dir, creationflags=_NO_WINDOW,
    )
