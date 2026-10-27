"""Acceso a los datos de rocketleague.tracker.network.

Ni Psyonix ni Tracker Network ofrecen una API pública de rangos, así que esto usa
la misma API interna que su web. Está detrás de Cloudflare: curl_cffi imita la
huella TLS de un navegador real. Las peticiones van en fila y espaciadas para no
abusar del servicio.
"""
from __future__ import annotations

import re
import threading
import time
from urllib.parse import quote, unquote

from curl_cffi import requests as cffi

API = "https://api.tracker.gg/api"
SITE = "https://rocketleague.tracker.network/rocket-league/profile"
_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Origin": "https://rocketleague.tracker.network",
    "Referer": "https://rocketleague.tracker.network/",
}
# Huellas de navegador a probar si Cloudflare bloquea una (las versiones viejas fallan).
_IMPERSONATE = ("chrome", "safari", "firefox")
_MIN_GAP = 1.5  # segundos mínimos entre peticiones

PLATFORMS = [
    {"id": "steam", "label": "Steam"},
    {"id": "epic", "label": "Epic"},
    {"id": "psn", "label": "PlayStation"},
    {"id": "xbl", "label": "Xbox"},
    {"id": "switch", "label": "Switch"},
]

PLAYLISTS = [
    {"id": 10, "short": "1v1", "name": "Ranked Duel 1v1"},
    {"id": 11, "short": "2v2", "name": "Ranked Doubles 2v2"},
    {"id": 13, "short": "3v3", "name": "Ranked Standard 3v3"},
    {"id": 34, "short": "Torneo", "name": "Tournament Matches"},
    {"id": 27, "short": "Hoops", "name": "Hoops"},
    {"id": 28, "short": "Rumble", "name": "Rumble"},
    {"id": 29, "short": "Dropshot", "name": "Dropshot"},
    {"id": 30, "short": "Snowday", "name": "Snowday"},
    {"id": 61, "short": "4v4", "name": "Ranked 4v4 Quads"},
    {"id": 63, "short": "Heatseeker", "name": "Heatseeker"},
    {"id": 0, "short": "Casual", "name": "Casual"},
]
_PLAYLIST_BY_NAME = {p["name"]: p["id"] for p in PLAYLISTS}

_TIERS_EN = [
    "Unranked", "Bronze I", "Bronze II", "Bronze III", "Silver I", "Silver II", "Silver III",
    "Gold I", "Gold II", "Gold III", "Platinum I", "Platinum II", "Platinum III",
    "Diamond I", "Diamond II", "Diamond III", "Champion I", "Champion II", "Champion III",
    "Grand Champion I", "Grand Champion II", "Grand Champion III", "Supersonic Legend",
]


class TrackerError(Exception):
    def __init__(self, message: str, kind: str = "error"):
        super().__init__(message)
        self.kind = kind


class NotFound(TrackerError):
    pass


class TrackerClient:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last = 0.0
        self._imp = 0
        self._session = None

    def _get(self, path: str) -> dict:
        with self._lock:
            for _ in range(len(_IMPERSONATE)):
                wait = self._last + _MIN_GAP - time.monotonic()
                if wait > 0:
                    time.sleep(wait)
                if self._session is None:
                    self._session = cffi.Session(impersonate=_IMPERSONATE[self._imp])
                try:
                    r = self._session.get(API + path, headers=_HEADERS, timeout=20)
                except Exception as e:
                    self._session = None
                    raise TrackerError("Sin conexión con Tracker", "network") from e
                finally:
                    self._last = time.monotonic()
                if r.status_code == 200:
                    return r.json()
                if r.status_code in (400, 404):  # 400: nombre que la plataforma no admite
                    raise NotFound(_error_message(r) or "No encontrado", "notfound")
                if r.status_code == 429:
                    raise TrackerError("Demasiadas peticiones, esperando", "ratelimit")
                if r.status_code == 403:
                    # Cloudflare rechazó esta huella: prueba con la siguiente.
                    self._session = None
                    self._imp = (self._imp + 1) % len(_IMPERSONATE)
                    continue
                raise TrackerError(f"Tracker respondió {r.status_code}", "http")
            raise TrackerError("Tracker está bloqueando las peticiones", "blocked")

    def profile(self, platform: str, ident: str) -> dict:
        return parse_profile(self._get(f"/v2/rocket-league/standard/profile/{platform}/{quote(ident, safe='')}"))

    def sessions(self, platform: str, ident: str) -> list[dict]:
        try:
            raw = self._get(f"/v2/rocket-league/standard/profile/{platform}/{quote(ident, safe='')}/sessions")
        except NotFound:
            return []
        return parse_sessions(raw)

    def thresholds(self, playlist: int) -> list[dict]:
        """MMR mínimo y máximo de cada rango y división en una lista de juego."""
        raw = self._get(f"/v1/rocket-league/distribution/{int(playlist)}")
        return [
            {"tier": e["tier"], "division": e["division"], "min": e["minMMR"], "max": e["maxMMR"]}
            for e in raw["data"]["data"]
            if e.get("playlist") == playlist and e.get("minMMR") is not None
        ]


def _error_message(r) -> str | None:
    try:
        return r.json()["errors"][0]["message"]
    except Exception:
        return None


def _val(stats: dict, key: str):
    return (stats.get(key) or {}).get("value")


def _meta(stats: dict, key: str) -> dict:
    return (stats.get(key) or {}).get("metadata") or {}


def parse_profile(raw: dict) -> dict:
    d = raw["data"]
    info = d["platformInfo"]
    meta = d.get("metadata") or {}
    playlists: dict[str, dict] = {}
    peaks: dict[str, dict] = {}
    for seg in d.get("segments", []):
        attrs = seg.get("attributes") or {}
        st = seg.get("stats") or {}
        if seg.get("type") == "playlist" and "playlistId" in attrs:
            tier_m, div_m = _meta(st, "tier"), _meta(st, "division")
            playlists[str(attrs["playlistId"])] = {
                "mmr": _val(st, "rating"),
                "tier": _val(st, "tier") or 0,
                "division": _val(st, "division") or 0,
                "icon": tier_m.get("iconUrl"),
                "deltaUp": div_m.get("deltaUp"),
                "deltaDown": div_m.get("deltaDown"),
                "estimated": bool(tier_m.get("estimated") or div_m.get("estimated")),
                "matches": _val(st, "matchesPlayed") or 0,
                "streak": _val(st, "winStreak") or 0,
                "streakType": _meta(st, "winStreak").get("type"),
            }
        elif seg.get("type") == "peak-rating" and "playlistId" in attrs:
            tier_name = _meta(st, "peakRating").get("tierName")
            peaks[str(attrs["playlistId"])] = {
                "mmr": _val(st, "peakRating"),
                "tier": _TIERS_EN.index(tier_name) if tier_name in _TIERS_EN else None,
            }
    return {
        "platform": info["platformSlug"],
        "id": info.get("platformUserIdentifier") or info.get("platformUserHandle"),
        "uid": info.get("platformUserId"),
        "name": info.get("platformUserHandle"),
        "avatar": info.get("avatarUrl"),
        "season": meta.get("currentSeason"),
        "updated": (meta.get("lastUpdated") or {}).get("value"),
        "expires": d.get("expiryDate"),
        "playlists": playlists,
        "peaks": peaks,
    }


def parse_sessions(raw: dict) -> list[dict]:
    """Partidas recientes, de la más nueva a la más vieja.

    Tracker a veces agrupa varias partidas en una entrada (cuando no vio el perfil
    entre medias) y su campo de victoria/derrota no siempre cuadra con el cambio de
    MMR; por eso se guardan las cifras en bruto y la interfaz decide con el delta.
    """
    out = []
    for sess in (raw.get("data") or {}).get("items", []):
        for m in sess.get("matches", []):
            md, st = m.get("metadata") or {}, m.get("stats") or {}
            out.append({
                "pl": _PLAYLIST_BY_NAME.get(md.get("playlist")),
                "t": md.get("dateCollected"),
                "n": _val(st, "matchesPlayed") or 0,
                "w": _val(st, "wins") or 0,
                "mmr": _val(st, "rating"),
                "d": _meta(st, "rating").get("ratingDelta"),
            })
    out.sort(key=lambda e: e["t"] or "", reverse=True)
    return out


def parse_query(platform: str, query: str) -> tuple[str, str]:
    """Acepta nombre, ID, enlace de Steam o enlace de Tracker; devuelve (plataforma, id)."""
    q = query.strip()
    m = re.search(r"tracker\.network/rocket-league/profile/([a-z]+)/([^/?#]+)", q)
    if m:
        return m.group(1), unquote(m.group(2))
    if platform == "steam":
        m = re.search(r"steamcommunity\.com/(?:profiles|id)/([^/?#]+)", q)
        if m:
            q = m.group(1)
    return platform, q


def profile_url(platform: str, ident: str) -> str:
    return f"{SITE}/{platform}/{quote(ident, safe='')}/overview"
