"""Actualizaciones desde GitHub Releases.

`check()` pregunta a GitHub cuál es la última versión publicada. Cómo se instala
depende de cómo se esté usando la app:

- Versión portable (.exe): baja el zip de Windows del release a una carpeta
  temporal (`stage`) y abre ese .exe nuevo con `--apply-update`. Ese proceso
  espera a que se cierre la app vieja, se copia encima de su carpeta sin tocar
  `data/` (`apply`) y la vuelve a abrir. Así se evita que Windows bloquee el
  .exe en uso.
- Desde el código (.pyw con Python): copia los archivos del código fuente del
  release encima de la carpeta (`install`) y reinicia.

En los dos casos `data/` (jugadores, ajustes y caché de cada uno) no se toca.
"""
from __future__ import annotations

import ctypes
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

VERSION = "1.1.0"
REPO = "mafiaki/climb-tracker"
REPO_URL = f"https://github.com/{REPO}"
EXE_NAME = "Climb Tracker.exe"
ASSET_SUFFIX = "-windows.zip"  # nombre del zip portable en cada release

FROZEN = getattr(sys, "frozen", False)  # True si va empaquetado como .exe
APP_DIR = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent.parent

_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
_KEEP = {"data", ".git"}  # nunca se tocan al actualizar
_STAGING_PREFIX = "climb-tracker-update-"
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
    asset = next((a["browser_download_url"] for a in rel.get("assets", [])
                  if a["name"].endswith(ASSET_SUFFIX)), None)
    return {
        "current": VERSION,
        "latest": latest,
        "available": _parse(latest) > _parse(VERSION),
        "notes": rel.get("body") or "",
        "url": rel.get("html_url") or REPO_URL,
        "zip": rel["zipball_url"],
        "asset": asset,
    }


def _extract(data: bytes, dest: Path, strip_root: bool) -> None:
    """Descomprime en dest. strip_root quita la carpeta de primer nivel del zip."""
    dest = dest.resolve()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for info in zf.infolist():
            parts = info.filename.split("/")[1 if strip_root else 0:]
            if info.is_dir() or not parts or not parts[-1] or parts[0] in _KEEP:
                continue
            target = dest.joinpath(*parts).resolve()
            if dest not in target.parents:
                continue  # rutas raras que saldrían de la carpeta
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_name(target.name + ".new")
            tmp.write_bytes(zf.read(info))
            os.replace(tmp, target)


# ---------- desde el código fuente ----------

def install(app_dir: Path, zip_url: str) -> bool:
    """Copia el código nuevo encima de app_dir. Devuelve si cambió requirements.txt."""
    req_file = app_dir / "requirements.txt"
    old_req = req_file.read_bytes() if req_file.exists() else b""
    # GitHub mete todo el código dentro de una carpeta "usuario-repo-commit/".
    _extract(_get(zip_url, timeout=120), app_dir, strip_root=True)
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
    subprocess.Popen([sys.executable, str(app_dir / "Climb Tracker.pyw")], cwd=app_dir, creationflags=_NO_WINDOW)


# ---------- versión portable (.exe) ----------

def stage(info: dict) -> Path:
    """Baja el zip portable a una carpeta temporal y devuelve la ruta de su .exe."""
    if not info.get("asset"):
        raise RuntimeError("esta versión no tiene descarga para Windows")
    folder = Path(tempfile.gettempdir()) / f"{_STAGING_PREFIX}{info['latest']}-{os.getpid()}"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    _extract(_get(info["asset"], timeout=600), folder, strip_root=False)
    exe = next(folder.rglob(EXE_NAME), None)
    if not exe:
        raise RuntimeError("el zip descargado no trae el programa")
    return exe


def launch_apply(new_exe: Path) -> None:
    """Abre el .exe nuevo para que se copie encima de esta carpeta cuando esta app se cierre."""
    subprocess.Popen([str(new_exe), "--apply-update", str(APP_DIR), str(os.getpid())],
                     cwd=new_exe.parent, creationflags=_NO_WINDOW)


def _wait_for_exit(pid: int, timeout: float) -> None:
    synchronize = 0x00100000
    handle = ctypes.windll.kernel32.OpenProcess(synchronize, False, pid)
    if handle:
        ctypes.windll.kernel32.WaitForSingleObject(handle, int(timeout * 1000))
        ctypes.windll.kernel32.CloseHandle(handle)
    time.sleep(0.5)  # que Windows suelte los archivos


def apply(dest: Path, old_pid: int) -> None:
    """Lo ejecuta el .exe nuevo desde la carpeta temporal: se copia encima de dest y la abre."""
    _wait_for_exit(old_pid, timeout=30)
    if not (dest / EXE_NAME).is_file():
        return  # no es la carpeta de la app: no se toca nada
    src = APP_DIR
    new_files = set()
    for path in src.rglob("*"):
        rel = path.relative_to(src)
        if path.is_dir() or rel.parts[0] in _KEEP:
            continue
        new_files.add(rel)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(20):
            try:
                shutil.copy2(path, target)
                break
            except PermissionError:
                time.sleep(0.5)
    # Archivos de la versión vieja que la nueva ya no trae (librerías que cambiaron de nombre…).
    internal = dest / "_internal"
    if internal.is_dir():
        for path in internal.rglob("*"):
            if path.is_file() and path.relative_to(dest) not in new_files:
                path.unlink(missing_ok=True)
    subprocess.Popen([str(dest / EXE_NAME)], cwd=dest, creationflags=_NO_WINDOW)


def cleanup_staging() -> None:
    """Borra las descargas de actualizaciones anteriores (cuando ya no están en uso)."""
    time.sleep(15)
    for folder in Path(tempfile.gettempdir()).glob(f"{_STAGING_PREFIX}*"):
        shutil.rmtree(folder, ignore_errors=True)
