"""Crea la versión portable para Windows (no necesita Python instalado).

Resultado:
  dist/Climb Tracker/                         la app lista para usar (Climb Tracker.exe)
  dist/Climb-Tracker-vX.Y.Z-windows.zip       lo que se sube al release de GitHub

Uso: python tools/build.py   (necesita: pip install pyinstaller)
"""
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from climbtracker.updater import ASSET_SUFFIX, EXE_NAME, VERSION  # noqa: E402

NAME = Path(EXE_NAME).stem
DIST = ROOT / "dist"
BUILD = ROOT / "build"


def main() -> None:
    shutil.rmtree(DIST / NAME, ignore_errors=True)
    pkg = ROOT / "climbtracker"
    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--windowed",
        "--name", NAME,
        "--icon", str(pkg / "assets" / "icon.ico"),
        "--add-data", f"{pkg / 'ui'};climbtracker/ui",
        "--add-data", f"{pkg / 'assets'};climbtracker/assets",
        "--collect-all", "curl_cffi",
        "--hidden-import", "_cffi_backend",
        "--distpath", str(DIST), "--workpath", str(BUILD), "--specpath", str(BUILD),
        str(ROOT / "Climb Tracker.pyw"),
    ], check=True, cwd=ROOT)

    app = DIST / NAME
    if (app / "data").exists():
        raise SystemExit("dist trae una carpeta data/: no se empaqueta para no publicar datos de nadie")
    zip_path = DIST / f"Climb-Tracker-v{VERSION}{ASSET_SUFFIX}"
    zip_path.unlink(missing_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(app.rglob("*")):
            if path.is_file():
                zf.write(path, Path(NAME) / path.relative_to(app))
    print(f"\nListo: {app}\nZip para el release: {zip_path} ({zip_path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
