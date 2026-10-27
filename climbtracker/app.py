"""Ventana de Climb Tracker: guarda la lista de jugadores, los refresca en segundo
plano y entrega los datos a la interfaz web (carpeta ui/)."""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import webbrowser
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError

import webview

from . import statsapi, tracker, updater

# Todo relativo a la carpeta del programa (la del .exe si va empaquetado), para que sea portable.
APP_DIR = updater.APP_DIR
DATA_DIR = APP_DIR / "data"
PKG_DIR = Path(__file__).resolve().parent  # en el .exe, la copia que va dentro de _internal
UI_INDEX = PKG_DIR / "ui" / "index.html"
ICON = PKG_DIR / "assets" / "icon.ico"

DEFAULT_CONFIG = {
    "players": [],
    "playlist": 11,
    "refresh_minutes": 2,
    "on_top": False,
    "compact": False,
    "match_pos": "off",  # sección de la partida (Stats API del juego): "top", "bottom" u "off"
    "session_start": None,  # cuándo empezó la sesión actual (botón "Nueva sesión")
    "result_mode": "both",  # MMR ganado/perdido: "day", "session" o "both"
    "match_rank": "tab",  # rango en "En partida": de la pestaña elegida ("tab") o de la lista jugada ("match")
    "rl_dir": None,  # carpeta del juego elegida a mano; si no, se busca sola
    "live_ini": False,  # la Stats API se activó desde la app
    "window": {"width": 340, "height": 600, "x": None, "y": None},
}
THRESHOLDS_MAX_AGE = 24 * 3600
MATCH_POSITIONS = ("top", "bottom", "off")
LIVE_RETRY = 5  # segundos entre intentos de conectar con el juego
LIVE_TTL = 5 * 60  # no volver a pedir a Tracker un rival visto hace menos de esto
# Al acabar una partida: primer refresco a los 15 s (o al caducar la caché de
# Tracker) y, si el MMR aún no ha cambiado, otros dos intentos más espaciados.
POST_DELAY = 15
POST_RETRIES = (45, 90)
POST_MAX_AGE = 20 * 60  # pasado esto se deja de esperar el MMR nuevo
KNOWN_PLAYLISTS = {p["id"] for p in tracker.PLAYLISTS}


def _key(platform: str, ident: str) -> str:
    return f"{platform}:{ident}".lower()


def _iso_ts(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


class Backend:
    """Métodos públicos = API que llama la interfaz con window.pywebview.api.*"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._wake = threading.Event()
        self._client = tracker.TrackerClient()
        self._window = None
        self._ready = False
        saved = _load_json(DATA_DIR / "config.json", {})
        if "show_match" in saved and "match_pos" not in saved:
            # Antes era una casilla ("mostrar debajo"): activada pasa a "abajo".
            saved["match_pos"] = "bottom" if saved["show_match"] else "off"
        saved.pop("show_match", None)
        self._config = {**DEFAULT_CONFIG, **saved}
        if not self._config.get("session_start"):
            # Primera vez: la sesión empieza al abrir la app; luego solo con el botón.
            self._config["session_start"] = datetime.now().astimezone().isoformat()
        self._config.pop("live", None)  # clave vieja: la sección ahora va apagada salvo que se encienda
        self._cache: dict = _load_json(DATA_DIR / "cache.json", {})
        self._thresholds: dict = _load_json(DATA_DIR / "thresholds.json", {})
        self._next: dict[str, float] = {}
        self._fails: dict[str, int] = {}
        self._loading: set[str] = set()
        # En partida: lo que manda la Stats API y lo que se va trayendo de Tracker.
        # Se escucha siempre (también con la sección oculta) para refrescar el MMR
        # de la lista al acabar cada partida.
        self._live_wake = threading.Event()
        self._live_status = "waiting"  # waiting (sin juego o sin Stats API) · connected
        self._match: dict | None = None
        self._post: dict[str, dict] = {}  # clave fija -> partida recién acabada, esperando su MMR
        self._in_replay = False
        self._live_info: dict[str, dict] = {}  # clave del juego -> perfil, error, próximo intento
        self._live_loading: set[str] = set()
        self._game_dir: str | None = None  # "" = buscado y no encontrado
        self._ini_reset = False

    # ---------- llamadas desde la interfaz ----------

    def get_state(self) -> dict:
        with self._lock:
            cfg = {k: v for k, v in self._config.items() if k not in ("players", "window")}
            return {
                "config": cfg,
                "players": [self._view(p) for p in self._config["players"]],
                "playlists": tracker.PLAYLISTS,
                "platforms": tracker.PLATFORMS,
                "thresholds": {k: v["rows"] for k, v in self._thresholds.items()},
                "live": self._live_state(),
                "version": updater.VERSION,
                "repo_url": updater.REPO_URL,
            }

    def ready(self) -> None:
        first = not self._ready
        self._ready = True
        if first:
            threading.Thread(target=self._check_update_at_start, daemon=True).start()
        self._wake.set()
        self._live_wake.set()
        self._push_live()

    def check_update(self) -> dict:
        try:
            info = updater.check()
        except HTTPError as e:
            return {"error": "Aún no hay versiones publicadas en GitHub" if e.code == 404
                    else "GitHub no responde ahora mismo; prueba en un rato"}
        except Exception:
            return {"error": "No se pudo conectar con GitHub. ¿Hay internet?"}
        return {k: info[k] for k in ("current", "latest", "available", "notes", "url")}

    def install_update(self) -> dict:
        try:
            info = updater.check()
            if not info["available"]:
                return {"ok": False, "error": "Ya tienes la última versión"}
            if updater.FROZEN:
                # .exe: la versión nueva se baja aparte y se copia encima al cerrar esta.
                new_exe = updater.stage(info)
            elif updater.install(APP_DIR, info["zip"]):
                updater.install_requirements(APP_DIR)
        except Exception as e:
            return {"ok": False, "error": f"No se pudo actualizar: {e}"}
        self._on_closing()  # guarda ajustes y ventana antes de reiniciar
        if updater.FROZEN:
            updater.launch_apply(new_exe)
        else:
            updater.restart(APP_DIR)
        threading.Timer(0.8, self._window.destroy).start()
        return {"ok": True}

    def open_repo(self) -> None:
        webbrowser.open(updater.REPO_URL)

    def add_player(self, platform: str, query: str) -> dict:
        platform, ident = tracker.parse_query(platform, query or "")
        if not ident:
            return {"ok": False, "error": "Escribe un nombre o ID"}
        try:
            prof = self._client.profile(platform, ident)
        except tracker.NotFound:
            return {"ok": False, "error": "No se encontró ese jugador en esa plataforma"}
        except tracker.TrackerError as e:
            return {"ok": False, "error": str(e)}
        return self._add_profile(prof)

    def _add_profile(self, prof: dict) -> dict:
        key = _key(prof["platform"], prof["id"])
        with self._lock:
            if any(_key(p["platform"], p["id"]) == key for p in self._config["players"]):
                return {"ok": False, "error": f"{prof['name']} ya está en la lista"}
            player = {"platform": prof["platform"], "id": prof["id"], "name": prof["name"]}
            self._config["players"].append(player)
            self._cache[key] = {"profile": prof, "sessions": [], "error": None}
            self._next[key] = 0  # que el hilo traiga ya sus partidas
            self._save()
        self._wake.set()
        return {"ok": True, "player": self._view(player)}

    def remove_player(self, key: str) -> None:
        with self._lock:
            self._config["players"] = [
                p for p in self._config["players"] if _key(p["platform"], p["id"]) != key
            ]
            self._cache.pop(key, None)
            self._post.pop(key, None)
            self._save()

    def move_player(self, key: str, delta: int) -> None:
        with self._lock:
            players = self._config["players"]
            idx = next((i for i, p in enumerate(players) if _key(p["platform"], p["id"]) == key), None)
            if idx is None:
                return
            new = max(0, min(len(players) - 1, idx + int(delta)))
            players.insert(new, players.pop(idx))
            self._save()

    def set_option(self, name: str, value) -> None:
        if name == "match_pos" and value not in MATCH_POSITIONS:
            return
        if name not in ("playlist", "refresh_minutes", "on_top", "compact", "match_pos",
                        "session_start", "result_mode", "match_rank"):
            return
        with self._lock:
            self._config[name] = value
            self._save()
        if name == "on_top" and self._window:
            self._window.on_top = bool(value)
        if name == "refresh_minutes":
            self._reschedule()
        if name == "match_pos":
            self._live_wake.set()  # buscar ya a los de la partida en curso
            self._push_live()

    def refresh_now(self) -> None:
        with self._lock:
            self._next.clear()
            self._fails.clear()
            for info in self._live_info.values():
                info["t"] = info["next"] = 0
        self._wake.set()
        self._live_wake.set()

    # ---------- en partida (Stats API) ----------

    def add_live_player(self, key: str) -> dict:
        """Pasa a la lista fija a alguien de la partida, sin volver a buscarlo."""
        with self._lock:
            lp = next((p for p in (self._match or {}).get("players", []) if p["key"] == key), None)
            prof = (self._live_info.get(key) or {}).get("profile")
        if not lp or lp["kind"] != "player":
            return {"ok": False, "error": "Ese jugador ya no está en la partida"}
        if prof:
            res = self._add_profile(prof)
        else:
            res = self.add_player(lp["platform"], lp["ident"])
            if not res["ok"] and lp.get("alt"):
                res = self.add_player(lp["platform"], lp["alt"])
        self._push_live()
        return res

    def dismiss_live(self) -> None:
        # Solo se oculta: la partida sigue contando para refrescar el MMR al acabar.
        with self._lock:
            if self._match:
                self._match["hidden"] = True
        self._push_live()

    def dismiss_ini_reset(self) -> None:
        with self._lock:
            self._ini_reset = False
            self._config["live_ini"] = False
            self._save()
        self._push_live()

    def get_live_setup(self) -> dict:
        game_dir = self._find_game_dir(refresh=True)
        ini = statsapi.read_settings(game_dir) if game_dir else None
        with self._lock:
            if ini and ini.get("enabled"):
                self._ini_reset = False
            return {
                "dir": game_dir,
                "picked": bool(self._config.get("rl_dir")),
                "ini": ini,
                "status": self._live_status,
                "rate": statsapi.RATE,
            }

    def pick_game_dir(self) -> dict:
        try:
            res = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        except Exception:
            res = None
        if not res:
            return self.get_live_setup()
        root = statsapi.game_root(res[0] if isinstance(res, (list, tuple)) else res)
        if not root:
            return {**self.get_live_setup(), "error": "Esa carpeta no es la del juego (no tiene TAGame\\Config)."}
        with self._lock:
            self._config["rl_dir"] = root
            self._save()
        return self.get_live_setup()

    def enable_stats_api(self) -> dict:
        return self._edit_ini(statsapi.enable, True)

    def disable_stats_api(self) -> dict:
        return self._edit_ini(statsapi.disable, False)

    def open_game_config(self) -> None:
        game_dir = self._find_game_dir()
        if game_dir:
            os.startfile(str(Path(game_dir) / "TAGame" / "Config"))

    def get_thresholds(self, playlist: int):
        pid = str(int(playlist))
        with self._lock:
            cached = self._thresholds.get(pid)
            if cached and time.time() - cached["fetched"] < THRESHOLDS_MAX_AGE:
                return cached["rows"]
        try:
            rows = self._client.thresholds(int(playlist))
        except tracker.TrackerError:
            return cached["rows"] if cached else None
        with self._lock:
            self._thresholds[pid] = {"fetched": time.time(), "rows": rows}
            _save_json(DATA_DIR / "thresholds.json", self._thresholds)
        return rows

    def open_profile(self, key: str) -> None:
        for p in list(self._config["players"]):
            if _key(p["platform"], p["id"]) == key:
                webbrowser.open(tracker.profile_url(p["platform"], p["id"]))

    # ---------- interno ----------

    def _check_update_at_start(self) -> None:
        # Al abrir la app: si hay versión nueva, la interfaz muestra un aviso.
        info = self.check_update()
        if info.get("available"):
            self._push({"type": "update", "update": info})

    def _show_match(self) -> bool:
        return self._config.get("match_pos", "off") != "off"

    def _view(self, player: dict) -> dict:
        key = _key(player["platform"], player["id"])
        entry = self._cache.get(key) or {}
        return {
            "key": key,
            "platform": player["platform"],
            "name": (entry.get("profile") or {}).get("name") or player.get("name") or player["id"],
            "profile": entry.get("profile"),
            "sessions": entry.get("sessions") or [],
            "error": entry.get("error"),
            "loading": key in self._loading,
            "post": self._post_view(key),
        }

    def _post_view(self, key: str | None) -> dict | None:
        post = self._post.get(key) if key else None
        return post and {"won": post["won"]}

    def _save(self) -> None:
        _save_json(DATA_DIR / "config.json", self._config)
        _save_json(DATA_DIR / "cache.json", self._cache)

    def _push(self, event: dict) -> None:
        if self._ready and self._window:
            try:
                self._window.run_js(f"window.RLT && RLT.onEvent({json.dumps(event)})")
            except Exception:
                pass

    def _push_player(self, player: dict) -> None:
        with self._lock:
            view = self._view(player)
            in_match = self._match is not None
        self._push({"type": "player", "player": view})
        if in_match:  # puede estar también en la partida
            self._push_live()

    def _reschedule(self) -> None:
        # Al cambiar el intervalo, recalcula la próxima consulta de cada jugador.
        with self._lock:
            for key in list(self._next):
                prof = (self._cache.get(key) or {}).get("profile") or {}
                self._next[key] = self._next_due(prof)
        self._wake.set()

    def _next_due(self, prof: dict) -> float:
        return self._due_after(prof, max(1, float(self._config.get("refresh_minutes") or 2)) * 60)

    def _due_after(self, prof: dict, delay: float) -> float:
        now = time.time()
        due = now + delay
        # Tracker guarda cada perfil en caché unos minutos (expiryDate); pedirlo
        # antes devuelve lo mismo, así que se espera a que caduque.
        expires = _iso_ts(prof.get("expires"))
        if expires and now < expires < now + 15 * 60:
            due = max(due, expires + 5)
        return due

    def _worker(self) -> None:
        while True:
            self._wake.wait(timeout=1.0)
            self._wake.clear()
            if not self._ready:
                continue
            with self._lock:
                players = list(self._config["players"])
            now = time.time()
            for player in players:
                key = _key(player["platform"], player["id"])
                if self._next.get(key, 0) <= now:
                    self._refresh(player, key)

    def _refresh(self, player: dict, key: str) -> None:
        with self._lock:
            self._loading.add(key)
        self._push_player(player)
        try:
            prof = self._client.profile(player["platform"], player["id"])
            with self._lock:
                old = self._cache.get(key) or {}
            sessions = old.get("sessions")
            if not sessions or (old.get("profile") or {}).get("updated") != prof["updated"]:
                sessions = self._client.sessions(player["platform"], player["id"])
            with self._lock:
                if not any(_key(p["platform"], p["id"]) == key for p in self._config["players"]):
                    return  # lo quitaron mientras se descargaba
                self._cache[key] = {"profile": prof, "sessions": sessions, "error": None}
                player["name"] = prof["name"]
                self._fails.pop(key, None)
                self._next[key] = self._next_due(prof)
                self._check_post(key, prof)
                self._save()
        except tracker.TrackerError as e:
            with self._lock:
                fails = self._fails[key] = self._fails.get(key, 0) + 1
                entry = self._cache.setdefault(key, {})
                entry["error"] = {"kind": e.kind, "message": str(e)}
                # Reintentos cada vez más espaciados: 1, 2, 4, 8... hasta 15 min.
                self._next[key] = time.time() + min(60 * 2 ** (fails - 1), 900)
                self._check_post(key)
        except Exception as e:  # datos con forma inesperada, etc.
            with self._lock:
                self._cache.setdefault(key, {})["error"] = {"kind": "error", "message": f"Error: {e}"}
                self._next[key] = time.time() + 300
        finally:
            with self._lock:
                self._loading.discard(key)
            self._push_player(player)

    # ---------- en partida: interno ----------

    def _find_game_dir(self, refresh: bool = False) -> str | None:
        with self._lock:
            if self._game_dir is not None and not refresh:
                return self._game_dir or None
            picked = self._config.get("rl_dir")
        found = statsapi.game_root(picked) or next(iter(statsapi.find_game_dirs()), None)
        with self._lock:
            self._game_dir = found or ""
        return found

    def _edit_ini(self, action, enabled: bool) -> dict:
        game_dir = self._find_game_dir()
        if not game_dir:
            return {**self.get_live_setup(), "error": "No se encontró la carpeta del juego."}
        try:
            action(game_dir)
        except PermissionError:
            return {**self.get_live_setup(), "error": "Windows no deja escribir en la carpeta del juego. "
                    "Ábrela con «Abrir carpeta» y cambia el archivo a mano."}
        except OSError as e:
            return {**self.get_live_setup(), "error": f"No se pudo cambiar el archivo: {e}"}
        with self._lock:
            self._config["live_ini"] = enabled
            self._ini_reset = False
            self._save()
        self._push_live()
        return {**self.get_live_setup(), "done": True}

    def _check_ini_reset(self) -> None:
        # Las actualizaciones del juego pueden devolver el .ini a PacketSendRate=0.
        if not self._config.get("live_ini"):
            return
        game_dir = self._find_game_dir()
        s = statsapi.read_settings(game_dir) if game_dir else {}
        if s.get("file") and not s.get("enabled"):
            with self._lock:
                self._ini_reset = True

    def _live_port(self) -> int:
        game_dir = self._find_game_dir()
        port = statsapi.read_settings(game_dir).get("port") if game_dir else None
        return port if port and port > 0 else statsapi.DEFAULT_PORT

    def _fixed_entry(self, lp: dict) -> tuple[str | None, dict | None]:
        """Si el jugador de la partida está en la lista fija: (su clave, su caché)."""
        if lp["kind"] != "player":
            return None, None
        keys = {_key(lp["platform"], lp["ident"])}
        prof = (self._live_info.get(lp["key"]) or {}).get("profile")
        if prof:
            keys.add(_key(prof["platform"], prof["id"]))
        for p in self._config["players"]:
            k = _key(p["platform"], p["id"])
            entry = self._cache.get(k) or {}
            uid = (entry.get("profile") or {}).get("uid")
            # Los de Epic se guardan por nombre; en la partida llegan por account id.
            if k in keys or (uid and lp["platform"] == "epic" and uid.lower() == lp["ident"].lower()):
                return k, entry
        return None, None

    def _live_view(self, lp: dict) -> dict:
        fkey, fixed = self._fixed_entry(lp)
        info = self._live_info.get(lp["key"]) or {}
        prof = (fixed or {}).get("profile") or info.get("profile")
        return {
            "key": lp["key"],
            "name": lp["name"],
            "team": lp["team"],
            "kind": lp["kind"],
            "platform": lp["platform"],
            "profile": prof,
            "sessions": (fixed or {}).get("sessions") or [],
            "error": None if prof else info.get("error"),
            "loading": lp["key"] in self._live_loading or fkey in self._loading,
            "tracked": fkey,
            "post": self._post_view(fkey),
        }

    def _live_state(self) -> dict:
        m = self._match
        show = m and not m["hidden"] and self._show_match()
        return {
            "status": self._live_status,
            "ini_reset": self._ini_reset,
            "match": show and {
                "playlist": m["playlist"],
                "ended": m["ended"],
                "winner": m["winner"],
                "players": [self._live_view(p) for p in m["players"]],
            } or None,
        }

    def _push_live(self) -> None:
        with self._lock:
            state = self._live_state()
        self._push({"type": "live", "live": state})

    def _set_live_status(self, status: str) -> None:
        with self._lock:
            if self._live_status == status:
                return
            self._live_status = status
        self._push_live()

    def _live_worker(self) -> None:
        """Escucha el socket local de la Stats API. Sin juego abierto (o sin la API
        activada) la conexión se rechaza al momento y se reintenta en silencio."""
        self._check_ini_reset()
        while True:
            try:
                for msg in statsapi.listen(self._live_port()):
                    if msg is None:
                        continue
                    try:
                        self._on_stats(*msg)
                    except Exception:
                        pass  # un mensaje con forma rara no debe cortar la escucha
            except OSError:
                pass
            self._set_live_status("waiting")
            self._end_match()  # el juego se cerró
            time.sleep(LIVE_RETRY)

    def _on_stats(self, event: str, data: dict) -> None:
        if event == "Connected":
            self._set_live_status("connected")
        elif event == "UpdateState":
            self._on_update(data)
        elif event == "MatchEnded":
            try:
                winner = int(data.get("WinnerTeamNum"))
            except (TypeError, ValueError):
                winner = None
            self._after_match(winner)
        elif event == "ReplayCreated":  # repetición guardada, no es una partida
            with self._lock:
                self._in_replay = True
                self._match = None
            self._push_live()
        elif event == "MatchDestroyed":
            self._end_match()

    def _on_update(self, data: dict) -> None:
        if self._in_replay:
            return
        players = [statsapi.parse_player(p) for p in data.get("Players") or [] if isinstance(p, dict)]
        players = [p for p in players if p["team"] in (0, 1)]
        if not players:
            return
        players.sort(key=lambda p: (p["team"], p["slot"], p["name"].lower()))
        game = data.get("Game") or {}
        size = max(Counter(p["team"] for p in players).values())
        pid = statsapi.tracker_playlist(game.get("PlaylistId"), size, KNOWN_PLAYLISTS)
        guid = str(data.get("MatchGuid") or "")
        sig = (guid, pid, tuple((p["key"], p["team"], p["name"]) for p in players))
        with self._lock:
            old = self._match
            if old and old["sig"] == sig and not old["ended"]:
                return  # nada nuevo (llega varias veces por segundo)
            same = bool(old and old["guid"] == guid and not old["ended"])
            if not same:
                self._prune_live_info({p["key"] for p in players})
            self._match = {
                "guid": guid, "sig": sig, "playlist": pid, "raw_playlist": game.get("PlaylistId"),
                "ended": False, "players": players,
                # Si solo cambió quién está (alguien se fue), sigue siendo la misma partida.
                "hidden": same and old["hidden"],
                "post_done": same and old["post_done"],
                "winner": old["winner"] if same else None,
            }
        self._push_live()
        self._live_wake.set()

    def _end_match(self) -> None:
        self._after_match(None)  # si salió antes de acabar (o se cerró el juego)
        with self._lock:
            self._in_replay = False
            if not self._match or self._match["ended"]:
                return
            self._match["ended"] = True  # se queda como "Última partida"
        self._push_live()

    def _after_match(self, winner: int | None) -> None:
        """Al acabar una partida, refresca cuanto antes a los de la lista fija que
        jugaban en ella para ver su MMR nuevo (solo una vez por partida)."""
        with self._lock:
            m = self._match
            if not m or m["post_done"] or m["ended"] or self._in_replay:
                return
            m["post_done"] = True
            m["winner"] = winner
            if m["playlist"] is None or not statsapi.affects_mmr(m["raw_playlist"], KNOWN_PLAYLISTS):
                return  # privada, exhibición, entreno...: no mueve el MMR
            targets = self._post_targets(m)
            now = time.time()
            for key, team in targets.items():
                prof = (self._cache.get(key) or {}).get("profile") or {}
                before = (prof.get("playlists") or {}).get(str(m["playlist"])) or {}
                self._post[key] = {
                    "pl": m["playlist"], "mmr": before.get("mmr"), "matches": before.get("matches"),
                    "won": None if winner is None or team is None else team == winner,
                    "tries": 0, "t": now,
                }
                self._next[key] = self._due_after(prof, POST_DELAY)
            players = [p for p in self._config["players"] if _key(p["platform"], p["id"]) in targets]
        for p in players:
            self._push_player(p)
        self._wake.set()

    def _post_targets(self, m: dict) -> dict[str, int | None]:
        """Jugadores de la lista fija que estaban en la partida -> su equipo."""
        targets: dict[str, int | None] = {}
        unpaired = set()
        for lp in m["players"]:
            fkey, _ = self._fixed_entry(lp)
            if fkey:
                targets[fkey] = lp["team"]
            elif lp["kind"] == "player":
                unpaired.add(lp["platform"])
        # Los de Epic se emparejan por el account id que da Tracker al refrescarlos.
        # Si aún no se tiene, no se sabe si estaban, así que se refrescan también.
        if "epic" in unpaired:
            for p in self._config["players"]:
                k = _key(p["platform"], p["id"])
                uid = ((self._cache.get(k) or {}).get("profile") or {}).get("uid")
                if p["platform"] == "epic" and k not in targets and not uid:
                    targets[k] = None
        return targets

    def _check_post(self, key: str, prof: dict | None = None) -> None:
        """Tras refrescar a alguien que acaba de jugar: si su MMR aún no ha cambiado,
        vuelve a mirar más tarde (Tracker cachea cada perfil ~6 min)."""
        post = self._post.get(key)
        if not post:
            return
        if time.time() - post["t"] > POST_MAX_AGE:
            del self._post[key]
            return
        if prof is None:
            return  # falló la consulta: sigue esperando con los reintentos normales
        now = (prof.get("playlists") or {}).get(str(post["pl"])) or {}
        changed = (now.get("mmr"), now.get("matches")) != (post["mmr"], post["matches"])
        if changed or post["tries"] >= len(POST_RETRIES):
            del self._post[key]
            return
        self._next[key] = self._due_after(prof, POST_RETRIES[post["tries"]])
        post["tries"] += 1

    def _prune_live_info(self, keep: set[str]) -> None:
        old = time.time() - 3600
        for k in [k for k, v in self._live_info.items() if k not in keep and v.get("t", 0) < old]:
            del self._live_info[k]

    def _live_due(self, lp: dict, now: float) -> bool:
        if lp["kind"] != "player" or lp["key"] in self._live_loading:
            return False
        fkey, fixed = self._fixed_entry(lp)
        if fkey and (fixed or {}).get("profile"):
            return False  # ya lo trae el refresco de la lista fija
        info = self._live_info.get(lp["key"]) or {}
        if info.get("profile") and now - info.get("t", 0) < LIVE_TTL:
            return False
        return info.get("next", 0) <= now

    def _live_lookups(self) -> None:
        """Busca en Tracker a los de la partida, de uno en uno (el cliente ya espacia
        las peticiones y las comparte con el refresco de la lista fija)."""
        while True:
            self._live_wake.wait(timeout=5.0)
            self._live_wake.clear()
            if not self._ready:
                continue
            while True:
                with self._lock:
                    m = self._match
                    now = time.time()
                    show = m and not m["ended"] and not m["hidden"] and self._show_match()
                    lp = next((p for p in m["players"] if self._live_due(p, now)), None) if show else None
                if not lp:
                    break
                self._live_fetch(lp)

    def _live_fetch(self, lp: dict) -> None:
        key = lp["key"]
        with self._lock:
            self._live_loading.add(key)
            info = dict(self._live_info.get(key) or {})
        self._push_live()
        try:
            try:
                prof = self._client.profile(lp["platform"], lp["ident"])
            except tracker.NotFound:
                if not lp.get("alt") or lp["alt"] == lp["ident"]:
                    raise
                prof = self._client.profile(lp["platform"], lp["alt"])
            info = {"profile": prof, "t": time.time(), "error": None, "next": 0, "fails": 0}
        except tracker.NotFound:
            info.update(error={"kind": "notfound", "message": "No aparece en Tracker"}, next=time.time() + 3600)
        except tracker.TrackerError as e:
            fails = info.get("fails", 0) + 1
            info.update(error={"kind": e.kind, "message": str(e)}, fails=fails,
                        next=time.time() + min(30 * 2 ** (fails - 1), 300))
        except Exception as e:
            info.update(error={"kind": "error", "message": f"Error: {e}"}, next=time.time() + 300)
        finally:
            with self._lock:
                self._live_info[key] = info
                self._live_loading.discard(key)
            self._push_live()

    def _on_closing(self) -> None:
        w = self._window
        with self._lock:
            try:
                self._config["window"] = {"width": w.width, "height": w.height, "x": w.x, "y": w.y}
            except Exception:
                pass
            self._save()


def _on_some_screen(x: int, y: int) -> bool:
    try:
        return any(
            s.x <= x + 40 < s.x + s.width and s.y <= y + 10 < s.y + s.height
            for s in webview.screens
        )
    except Exception:
        return True


def main() -> None:
    backend = Backend()
    geo = {**DEFAULT_CONFIG["window"], **(backend._config.get("window") or {})}
    if geo.get("x") is not None and not _on_some_screen(geo["x"], geo["y"]):
        geo["x"] = geo["y"] = None  # el monitor donde estaba ya no existe
    window = webview.create_window(
        "Climb Tracker",
        url=str(UI_INDEX),
        js_api=backend,
        width=int(geo["width"]),
        height=int(geo["height"]),
        x=geo.get("x"),
        y=geo.get("y"),
        min_size=(270, 220),
        on_top=bool(backend._config.get("on_top")),
        background_color="#0d1117",
    )
    backend._window = window
    window.events.closing += backend._on_closing
    threading.Thread(target=backend._worker, daemon=True).start()
    threading.Thread(target=backend._live_worker, daemon=True).start()
    threading.Thread(target=backend._live_lookups, daemon=True).start()
    threading.Thread(target=updater.cleanup_staging, daemon=True).start()
    webview.start(private_mode=True, icon=str(ICON) if ICON.exists() else None)
