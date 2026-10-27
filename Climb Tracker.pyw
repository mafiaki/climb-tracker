"""Abre Climb Tracker.

Desde el código: la primera vez usa «Iniciar Climb Tracker.bat» para instalar lo necesario.
Empaquetado (Climb Tracker.exe) no necesita nada instalado.
"""
import sys
import traceback
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)
HERE = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
if not FROZEN:
    sys.path.insert(0, str(HERE))

try:
    if len(sys.argv) >= 4 and sys.argv[1] == "--apply-update":
        # El .exe nuevo, desde la carpeta temporal, se copia encima de la app vieja.
        from climbtracker import updater

        updater.apply(Path(sys.argv[2]), int(sys.argv[3]))
    else:
        from climbtracker.app import main

        main()
except Exception:
    log = HERE / "data" / "error.log"
    log.parent.mkdir(exist_ok=True)
    log.write_text(traceback.format_exc(), encoding="utf-8")
    try:
        import ctypes

        first_time = "" if FROZEN else "Si es la primera vez, abre «Iniciar Climb Tracker.bat».\n\n"
        ctypes.windll.user32.MessageBoxW(
            None,
            f"Climb Tracker no pudo arrancar.\n\n{first_time}Detalles en: data\\error.log",
            "Climb Tracker",
            0x10,
        )
    except Exception:
        pass
