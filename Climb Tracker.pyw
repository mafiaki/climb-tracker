"""Abre Climb Tracker. La primera vez usa «Iniciar Climb Tracker.bat» para instalar lo necesario."""
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

try:
    from climbtracker.app import main

    main()
except Exception:
    log = HERE / "data" / "error.log"
    log.parent.mkdir(exist_ok=True)
    log.write_text(traceback.format_exc(), encoding="utf-8")
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            None,
            "Climb Tracker no pudo arrancar.\n\n"
            "Si es la primera vez, abre «Iniciar Climb Tracker.bat».\n\n"
            f"Detalles en: data\\error.log",
            "Climb Tracker",
            0x10,
        )
    except Exception:
        pass
