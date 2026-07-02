"""
utils/api_client.py
FIFA World Cup 2026 — Live data from worldcup26.ir
Self-healing: API → Cache → CSV fallback. Never crashes.
"""

import json
import time
import pathlib
import logging
from datetime import datetime
from typing import Any

import requests

log = logging.getLogger(__name__)

ROOT       = pathlib.Path(__file__).parent.parent
CACHE_FILE = ROOT / "data" / "api_cache.json"
BASE_URL   = "https://worldcup26.ir"

# Cache TTLs (seconds)
TTL_MATCHES = 300      # 5 minutes — live scores change fast
TTL_GROUPS  = 3600     # 1 hour — group tables update less often
TTL_TEAMS   = 86400    # 24 hours — team data is static

# Request timeout
TIMEOUT = 6


# ── Flag emoji map (country name → flag) ──────────────────────
FLAGS: dict[str, str] = {
    "Argentina": "🇦🇷", "Australia": "🇦🇺", "Austria": "🇦🇹",
    "Belgium": "🇧🇪", "Bolivia": "🇧🇴", "Brazil": "🇧🇷",
    "Cameroon": "🇨🇲", "Canada": "🇨🇦", "Chile": "🇨🇱",
    "China": "🇨🇳", "Colombia": "🇨🇴", "Costa Rica": "🇨🇷",
    "Croatia": "🇭🇷", "Denmark": "🇩🇰", "Ecuador": "🇪🇨",
    "Egypt": "🇪🇬", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "France": "🇫🇷",
    "Germany": "🇩🇪", "Ghana": "🇬🇭", "Greece": "🇬🇷",
    "Honduras": "🇭🇳", "Iran": "🇮🇷", "Iraq": "🇮🇶",
    "Italy": "🇮🇹", "Ivory Coast": "🇨🇮", "Jamaica": "🇯🇲",
    "Japan": "🇯🇵", "Jordan": "🇯🇴", "Kenya": "🇰🇪",
    "Mali": "🇲🇱", "Mexico": "🇲🇽", "Morocco": "🇲🇦",
    "Netherlands": "🇳🇱", "New Zealand": "🇳🇿", "Nigeria": "🇳🇬",
    "Norway": "🇳🇴", "Panama": "🇵🇦", "Paraguay": "🇵🇾",
    "Peru": "🇵🇪", "Poland": "🇵🇱", "Portugal": "🇵🇹",
    "Qatar": "🇶🇦", "Romania": "🇷🇴", "Saudi Arabia": "🇸🇦",
    "Senegal": "🇸🇳", "Serbia": "🇷🇸", "South Korea": "🇰🇷",
    "Spain": "🇪🇸", "Switzerland": "🇨🇭", "Tunisia": "🇹🇳",
    "Turkey": "🇹🇷", "Ukraine": "🇺🇦", "United States": "🇺🇸",
    "Uruguay": "🇺🇾", "Venezuela": "🇻🇪", "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
}


def flag(country: str) -> str:
    """Return flag emoji for a country name, or 🏳 as fallback."""
    return FLAGS.get(country, FLAGS.get(country.split()[0], "🏳️"))


# ── Internal cache helpers ────────────────────────────────────
def _load_cache() -> dict:
    try:
        if CACHE_FILE.exists():
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_cache(cache: dict) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        log.warning(f"Cache write failed: {e}")


def _is_fresh(cache: dict, key: str, ttl: int) -> bool:
    entry = cache.get(key)
    if not entry:
        return False
    age = time.time() - entry.get("fetched_at", 0)
    return age < ttl


# ── Core fetch (API → cache → stale cache) ────────────────────
def _fetch(endpoint: str, cache_key: str, ttl: int) -> tuple[Any, str]:
    """
    Returns (data, source) where source is 'live' | 'cache' | 'error'.
    Never raises — always returns something or None.
    """
    cache = _load_cache()

    if _is_fresh(cache, cache_key, ttl):
        return cache[cache_key]["data"], "cache"

    try:
        resp = requests.get(f"{BASE_URL}/{endpoint}", timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        cache[cache_key] = {"data": data, "fetched_at": time.time()}
        _save_cache(cache)
        return data, "live"
    except Exception as e:
        log.warning(f"API fetch failed ({endpoint}): {e}")
        if cache_key in cache:
            return cache[cache_key]["data"], "cache"
        return None, "error"


# ── Public API functions ───────────────────────────────────────
def get_matches() -> tuple[list | None, str]:
    """Live match results and upcoming fixtures."""
    return _fetch("get/games", "matches", TTL_MATCHES)


def get_groups() -> tuple[list | None, str]:
    """Group stage standings."""
    return _fetch("get/groups", "groups", TTL_GROUPS)


def get_teams() -> tuple[list | None, str]:
    """Team info (name, flag, group)."""
    return _fetch("get/teams", "teams", TTL_TEAMS)


def get_last_updated(key: str = "matches") -> datetime | None:
    """Return when data was last successfully fetched from the API."""
    cache = _load_cache()
    entry = cache.get(key)
    if entry and "fetched_at" in entry:
        return datetime.fromtimestamp(entry["fetched_at"])
    return None


def time_since_update(key: str = "matches") -> str:
    """Human-readable string: 'Updated 3 mins ago' or 'No live data'."""
    ts = get_last_updated(key)
    if not ts:
        return "Using local data"
    secs = (datetime.now() - ts).total_seconds()
    if secs < 60:
        return f"Updated just now"
    elif secs < 3600:
        return f"Updated {int(secs // 60)} min ago"
    elif secs < 86400:
        return f"Updated {int(secs // 3600)}h ago"
    return f"Updated {int(secs // 86400)}d ago"


# ── Parsed helpers (safe field extraction) ────────────────────
def parse_completed_matches(raw: list | None) -> list[dict]:
    """Return list of completed matches sorted by date desc."""
    if not raw:
        return []
    results = []
    for m in raw:
        try:
            home_score = m.get("home_score") or m.get("homeScore")
            away_score = m.get("away_score") or m.get("awayScore")
            if home_score is None or away_score is None:
                continue
            results.append({
                "home": m.get("home_team") or m.get("homeTeam", "?"),
                "away": m.get("away_team") or m.get("awayTeam", "?"),
                "home_score": int(home_score),
                "away_score": int(away_score),
                "date":  m.get("date") or m.get("match_date", ""),
                "stage": m.get("stage") or m.get("round", "Group Stage"),
            })
        except Exception:
            continue
    return sorted(results, key=lambda x: x["date"], reverse=True)


def parse_upcoming_matches(raw: list | None) -> list[dict]:
    """Return upcoming (unplayed) matches."""
    if not raw:
        return []
    upcoming = []
    for m in raw:
        try:
            home_score = m.get("home_score") or m.get("homeScore")
            if home_score is not None:
                continue  # already played
            upcoming.append({
                "home":  m.get("home_team") or m.get("homeTeam", "?"),
                "away":  m.get("away_team") or m.get("awayTeam", "?"),
                "date":  m.get("date") or m.get("match_date", ""),
                "stage": m.get("stage") or m.get("round", "Group Stage"),
            })
        except Exception:
            continue
    return sorted(upcoming, key=lambda x: x["date"])


def total_goals_from_matches(matches: list[dict]) -> int:
    """Sum all goals from completed matches."""
    return sum(m["home_score"] + m["away_score"] for m in matches)
