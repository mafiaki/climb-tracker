"""Stats API oficial de Rocket League: encontrar el juego, activar la API en su
.ini y leer del socket local quién está en la partida.

Es una función del propio juego (pensada para overlays de retransmisión): con
PacketSendRate > 0 el juego abre un socket en 127.0.0.1 y emite JSON. No se lee
la memoria del juego ni se toca su proceso.
https://www.rocketleague.com/developer/stats-api
"""
from __future__ import annotations

import codecs
import json
import os
import re
import shutil
import socket
from pathlib import Path

SECTION = "TAGame.MatchStatsExporter_TA"
DEFAULT_PORT = 49123
DEFAULT_WEBPORT = 49124
RATE = 5  # paquetes por segundo al activarla; para saber quién juega sobra
# El juego lee TAStatsAPI.ini y, si no existe, DefaultStatsAPI.ini.
_INI_NAMES = ("TAStatsAPI.ini", "DefaultStatsAPI.ini")
_STEAM_DIR = "rocketleague"

# Plataforma del PrimaryId ("Steam|uid|0") -> plataforma de Tracker.
_PLATFORMS = {"steam": "steam", "epic": "epic", "ps4": "psn", "ps5": "psn", "psn": "psn",
              "xboxone": "xbl", "xbox": "xbl", "xbl": "xbl", "switch": "switch"}
_HEX32 = re.compile(r"[0-9a-fA-F]{32}")


# ---------- carpeta del juego ----------

def game_root(path) -> str | None:
    """Carpeta raíz del juego a partir de ella o de una subcarpeta suya."""
    if not path:
        return None
    p = Path(path)
    for cand in (p, *list(p.parents)[:3]):
        if (cand / "TAGame" / "Config").is_dir():
            return str(cand)
    return None


def find_game_dirs() -> list[str]:
    """Instalaciones de Rocket League en Steam y Epic (sin rutas fijas)."""
    found: list[str] = []
    for lib in _steam_libraries():
        found.append(str(Path(lib) / "steamapps" / "common" / _STEAM_DIR))
    found += _epic_installs()
    out = []
    for d in found:
        root = game_root(d)
        if root and root.lower() not in (x.lower() for x in out):
            out.append(root)
    return out


def _steam_libraries() -> list[str]:
    roots = []
    try:
        import winreg

        for hive, key, name in (
            (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
        ):
            try:
                with winreg.OpenKey(hive, key) as k:
                    roots.append(str(winreg.QueryValueEx(k, name)[0]))
            except OSError:
                pass
    except ImportError:
        pass
    libs = list(roots)
    for root in roots:
        try:
            vdf = (Path(root) / "steamapps" / "libraryfolders.vdf").read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        libs += [m.replace("\\\\", "\\") for m in re.findall(r'"path"\s+"([^"]+)"', vdf)]
    return libs


def _epic_installs() -> list[str]:
    manifests = Path(os.environ.get("PROGRAMDATA") or "C:/ProgramData") / "Epic" / "EpicGamesLauncher" / "Data" / "Manifests"
    out = []
    try:
        items = list(manifests.glob("*.item"))
    except OSError:
        return out
    for item in items:
        try:
            m = json.loads(item.read_text(encoding="utf-8", errors="replace"))
        except (OSError, ValueError):
            continue
        if str(m.get("DisplayName", "")).startswith("Rocket League") or m.get("AppName") == "Sugar":
            if m.get("InstallLocation"):
                out.append(m["InstallLocation"])
    return out


# ---------- el .ini de la Stats API ----------

def ini_file(game_dir) -> Path | None:
    cfg = Path(game_dir) / "TAGame" / "Config"
    return next((cfg / n for n in _INI_NAMES if (cfg / n).is_file()), None)


def _read(path: Path) -> tuple[str, str, bytes]:
    raw = path.read_bytes()
    if raw.startswith(codecs.BOM_UTF16_LE):
        return raw[2:].decode("utf-16-le"), "utf-16-le", codecs.BOM_UTF16_LE
    if raw.startswith(codecs.BOM_UTF8):
        return raw[3:].decode("utf-8"), "utf-8", codecs.BOM_UTF8
    try:
        return raw.decode("utf-8"), "utf-8", b""
    except UnicodeDecodeError:
        return raw.decode("latin-1"), "latin-1", b""


def _section(lines: list[str]) -> tuple[int | None, int]:
    """Índices de la cabecera de nuestra sección y de donde termina."""
    start = None
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            if start is not None:
                return start, i
            if s[1:-1].strip().lower() == SECTION.lower():
                start = i
    return start, len(lines)


def _num(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def read_settings(game_dir) -> dict:
    path = ini_file(game_dir)
    if not path:
        return {"file": None}
    lines = _read(path)[0].splitlines()
    start, end = _section(lines)
    values = {}
    if start is not None:
        for line in lines[start + 1:end]:
            m = re.match(r"\s*(\w+)\s*=\s*(.*?)\s*$", line)
            if m:
                values[m.group(1).lower()] = m.group(2)
    rate = _num(values.get("packetsendrate"), 0)
    port = int(_num(values.get("port"), DEFAULT_PORT))
    webport = int(_num(values.get("webport"), DEFAULT_WEBPORT))
    return {
        "file": str(path),
        "name": path.name,
        "rate": rate,
        "port": port,
        "webport": webport,
        "enabled": rate > 0 and port > 0,
    }


def _write(game_dir, values: dict) -> None:
    """Cambia claves de la sección respetando el resto del archivo. La primera vez
    deja una copia del original al lado (.bak)."""
    path = ini_file(game_dir)
    if not path:
        raise FileNotFoundError("No se encontró DefaultStatsAPI.ini ni TAStatsAPI.ini")
    text, enc, bom = _read(path)
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    start, end = _section(lines)
    if start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(f"[{SECTION}]")
        start, end = len(lines) - 1, len(lines)
    for key, val in values.items():
        idx = next((i for i in range(start + 1, end) if re.match(rf"\s*{key}\s*=", lines[i], re.I)), None)
        if idx is not None:
            lines[idx] = f"{key}={val}"
            continue
        last = max((i for i in range(start, end) if lines[i].strip()), default=start)
        lines.insert(last + 1, f"{key}={val}")
        end += 1
    backup = path.with_name(path.name + ".bak")
    if not backup.exists():
        shutil.copy2(path, backup)
    path.write_bytes(bom + nl.join(lines).encode(enc))


def enable(game_dir) -> dict:
    s = read_settings(game_dir)
    values = {}
    if s.get("rate", 0) <= 0:
        values["PacketSendRate"] = RATE
    if s.get("port", 0) <= 0:
        values["Port"] = DEFAULT_PORT if s.get("webport") != DEFAULT_PORT else DEFAULT_PORT + 2
    if values:
        _write(game_dir, values)
    return read_settings(game_dir)


def disable(game_dir) -> dict:
    _write(game_dir, {"PacketSendRate": 0})
    return read_settings(game_dir)


# ---------- socket ----------

_DECODER = json.JSONDecoder()
_NEXT = re.compile(r'\{\s*"Event"')


def split_messages(buf: str) -> tuple[list[dict], str]:
    """Separa los JSON que llegan pegados (el juego no pone separador). Devuelve
    los mensajes completos y lo que queda a medias."""
    out = []
    i, n = 0, len(buf)
    while True:
        while i < n and buf[i] in " \t\r\n\x00":
            i += 1
        if i >= n:
            return out, ""
        try:
            obj, i = _DECODER.raw_decode(buf, i)
        except ValueError:
            m = _NEXT.search(buf, i + 1)
            if not m:
                return out, buf[i:]  # mensaje a medias: esperar al resto
            i = m.start()  # mensaje roto: saltar al siguiente
            continue
        if isinstance(obj, dict):
            out.append(obj)


def _event(obj: dict) -> tuple[str, dict] | None:
    ev, data = obj.get("Event"), obj.get("Data")
    if not isinstance(ev, str):
        return None
    if isinstance(data, str):  # el juego manda Data como texto JSON
        try:
            data = json.loads(data)
        except ValueError:
            data = {}
    return ev, data if isinstance(data, dict) else {}


def listen(port: int):
    """Conecta al socket TCP del juego y va devolviendo (evento, datos).

    Devuelve None cada pocos segundos sin mensajes (en el menú el juego no manda
    nada) para que quien llama pueda decidir si sigue. Lanza OSError si el juego
    no está abierto o se cierra.
    """
    with socket.create_connection(("127.0.0.1", int(port)), timeout=2) as sock:
        sock.settimeout(5)
        dec = codecs.getincrementaldecoder("utf-8")("replace")
        buf = ""
        yield ("Connected", {})
        while True:
            try:
                chunk = sock.recv(65536)
            except socket.timeout:
                yield None
                continue
            if not chunk:
                raise ConnectionResetError("El juego cerró la conexión")
            buf += dec.decode(chunk)
            msgs, buf = split_messages(buf)
            if len(buf) > 4_000_000:
                buf = ""
            for obj in msgs:
                ev = _event(obj)
                if ev:
                    yield ev


# ---------- jugadores ----------

def parse_player(p: dict) -> dict:
    """Jugador de UpdateState -> cómo buscarlo en Tracker.

    Steam y Epic traen un ID fijo en PrimaryId (el de Epic es el account id, que
    Tracker acepta con guiones). PlayStation, Xbox y Switch traen IDs internos que
    Tracker no conoce, así que con ellos se busca por nombre.
    """
    name = str(p.get("Name") or "").strip()
    parts = str(p.get("PrimaryId") or "").split("|")
    kind = parts[0].strip().lower() if parts else ""
    uid = parts[1].strip() if len(parts) > 1 else ""
    split = parts[2].strip() if len(parts) > 2 else "0"
    platform = _PLATFORMS.get(kind)
    out = {
        "key": f"{kind}|{uid}|{split}".lower() if uid else f"name|{name}".lower(),
        "name": name or "?",
        "team": p.get("TeamNum"),
        "slot": int(_num(p.get("Shortcut"), 0)),
        "platform": platform,
        "ident": None,
        "alt": None,  # segundo intento si el primero no existe en Tracker
        "kind": "player",
    }
    if not platform or not uid or uid == "0":
        out["kind"] = "bot"
    elif split not in ("", "0"):
        out["kind"] = "guest"  # invitado a pantalla partida: sin perfil propio
    elif platform == "steam":
        out["ident"] = uid
    elif platform == "epic":
        out["ident"] = epic_uuid(uid)
        out["alt"] = name or None
    else:
        out["ident"] = name or None
    if out["kind"] == "player" and not out["ident"]:
        out["kind"] = "bot"
    if out["kind"] == "bot":  # todos los bots traen el mismo PrimaryId
        out["key"] = f"bot|{name}|{out['slot']}".lower()
    return out


def epic_uuid(uid: str) -> str:
    """9dfa38bf97f9...b96a -> 9dfa38bf-97f9-...-64ea869eb96a (como lo quiere Tracker)."""
    if _HEX32.fullmatch(uid):
        u = uid.lower()
        return f"{u[:8]}-{u[8:12]}-{u[12:16]}-{u[16:20]}-{u[20:]}"
    return uid


# Listas del juego -> listas de Tracker. Las casuales cuentan todas como "Casual".
_CASUAL = {1, 2, 3, 4}
_RANKED_BY_SIZE = {1: 10, 2: 11, 3: 13, 4: 61}


def tracker_playlist(playlist_id, team_size: int, known: set[int]) -> int | None:
    """Lista de Tracker que corresponde a la partida. Si el juego no manda
    PlaylistId (o es privada, entreno, etc.) se usa la competitiva del tamaño."""
    try:
        pid = int(playlist_id)
    except (TypeError, ValueError):
        pid = None
    if pid in known and pid != 0:
        return pid
    if pid in _CASUAL:
        return 0
    return _RANKED_BY_SIZE.get(team_size)


def affects_mmr(playlist_id, known: set[int]) -> bool:
    """Si la partida mueve un MMR que sigue Tracker (no privada, exhibición, etc.).
    Sin PlaylistId no se puede saber, así que se supone que sí."""
    try:
        pid = int(playlist_id)
    except (TypeError, ValueError):
        return True
    return pid in _CASUAL or (pid in known and pid != 0)
