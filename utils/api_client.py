"""
utils/api_client.py
FIFA World Cup 2026 Companion Stats Hub

Reads live match & group data from data/api_cache.json (updated by the daily
Render cron job / refresh_data.py).  Falls back to a minimal hardcoded set if
the cache is missing or corrupt so the app never crashes.
"""

import json
import time
import pathlib
import datetime

ROOT       = pathlib.Path(__file__).parent.parent
CACHE_PATH = ROOT / "data" / "api_cache.json"

# ── Team-name flag emoji map ──────────────────────────────────────────────────
FLAGS: dict[str, str] = {
    "Algeria": "🇩🇿", "Argentina": "🇦🇷", "Australia": "🇦🇺", "Austria": "🇦🇹",
    "Belgium": "🇧🇪", "Bolivia": "🇧🇴", "Bosnia and Herzegovina": "🇧🇦",
    "Brazil": "🇧🇷", "Cameroon": "🇨🇲", "Canada": "🇨🇦", "Cape Verde": "🇨🇻",
    "Chile": "🇨🇱", "China": "🇨🇳", "Colombia": "🇨🇴", "Costa Rica": "🇨🇷",
    "Croatia": "🇭🇷", "Curacao": "🇨🇼", "Czech Republic": "🇨🇿",
    "Democratic Republic of the Congo": "🇨🇩", "Congo DR": "🇨🇩",
    "Denmark": "🇩🇰", "Ecuador": "🇪🇨", "Egypt": "🇪🇬", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "France": "🇫🇷", "Georgia": "🇬🇪", "Germany": "🇩🇪", "Ghana": "🇬🇭",
    "Greece": "🇬🇷", "Haiti": "🇭🇹", "Honduras": "🇭🇳", "Iran": "🇮🇷",
    "Iraq": "🇮🇶", "Italy": "🇮🇹", "Ivory Coast": "🇨🇮", "Jamaica": "🇯🇲",
    "Japan": "🇯🇵", "Jordan": "🇯🇴", "Kenya": "🇰🇪", "Korea Republic": "🇰🇷",
    "South Korea": "🇰🇷", "Mali": "🇲🇱", "Mexico": "🇲🇽", "Morocco": "🇲🇦",
    "Netherlands": "🇳🇱", "New Zealand": "🇳🇿", "Nigeria": "🇳🇬",
    "Norway": "🇳🇴", "Panama": "🇵🇦", "Paraguay": "🇵🇾", "Peru": "🇵🇪",
    "Poland": "🇵🇱", "Portugal": "🇵🇹", "Qatar": "🇶🇦", "Romania": "🇷🇴",
    "Saudi Arabia": "🇸🇦", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Senegal": "🇸🇳",
    "Serbia": "🇷🇸", "South Africa": "🇿🇦", "Spain": "🇪🇸",
    "Sweden": "🇸🇪", "Switzerland": "🇨🇭", "Tunisia": "🇹🇳", "Turkey": "🇹🇷",
    "Ukraine": "🇺🇦", "United States": "🇺🇸", "Uruguay": "🇺🇾",
    "Uzbekistan": "🇺🇿", "Venezuela": "🇻🇪", "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
}

# Stage label mapping for display
STAGE_LABELS: dict[str, str] = {
    "group":  "Group Stage",
    "r32":    "Round of 32",
    "r16":    "Round of 16",
    "qf":     "Quarter-Final",
    "sf":     "Semi-Final",
    "third":  "Third Place Play-Off",
    "final":  "Final",
}

# ── Fallback data (used only if cache is absent/corrupt) ──────────────────────
_FALLBACK_MATCHES = [
    {"home": "Mexico",       "away": "South Africa", "home_score": 2, "away_score": 0, "stage": "Group Stage",  "date": "06/11/2026"},
    {"home": "United States","away": "Canada",        "home_score": 1, "away_score": 2, "stage": "Group Stage",  "date": "06/12/2026"},
    {"home": "Argentina",    "away": "Morocco",       "home_score": 3, "away_score": 0, "stage": "Group Stage",  "date": "06/13/2026"},
    {"home": "France",       "away": "Germany",       "home_score": 2, "away_score": 1, "stage": "Group Stage",  "date": "06/14/2026"},
]


# ── Cache loader ──────────────────────────────────────────────────────────────
def _load_cache() -> dict:
    """Return the parsed api_cache.json, or an empty dict on failure."""
    try:
        raw = CACHE_PATH.read_bytes().decode("utf-8", errors="replace")
        return json.loads(raw)
    except Exception:
        return {}


# ── Public helpers ─────────────────────────────────────────────────────────────
def flag(country: str) -> str:
    """Return flag emoji for a country name (graceful fallback)."""
    return FLAGS.get(country, FLAGS.get(country.split()[0], "🏳️"))


def get_matches() -> tuple[list, str]:
    """
    Return (raw_games_list, source_label).

    raw_games_list is the list of raw game dicts from the cache so that
    parse_completed_matches / parse_upcoming_matches can filter them.
    Falls back to _FALLBACK_MATCHES if the cache is missing.
    """
    cache = _load_cache()
    try:
        games = cache["matches"]["data"]["games"]
        if not games:
            raise ValueError("empty games list")
        return games, "cache"
    except Exception:
        return _FALLBACK_MATCHES, "fallback"


def get_groups() -> tuple[list, str]:
    """Return (groups_list, source_label) from cache or fallback."""
    cache = _load_cache()
    try:
        groups_data = cache["groups"]["data"]
        # groups_data may be a list or dict depending on the API source
        if isinstance(groups_data, list):
            return groups_data, "cache"
        return list(groups_data.values()) if isinstance(groups_data, dict) else [], "cache"
    except Exception:
        return [], "fallback"


def parse_completed_matches(raw: list) -> list[dict]:
    """
    Convert raw game dicts (from cache) to the normalised format used by pages.
    Handles both the real cache format and the fallback format transparently.
    """
    results = []
    for g in raw:
        # Detect if this is already in normalised format (fallback / old style)
        if "home" in g and "away" in g:
            results.append(g)
            continue

        # Real cache format
        if g.get("finished", "").upper() != "TRUE":
            continue
        try:
            results.append({
                "home":       g.get("home_team_name_en", "?"),
                "away":       g.get("away_team_name_en", "?"),
                "home_score": int(g.get("home_score", 0)),
                "away_score": int(g.get("away_score", 0)),
                "stage":      STAGE_LABELS.get(g.get("type", ""), g.get("type", "Match")),
                "date":       g.get("local_date", ""),
                "matchday":   g.get("matchday", ""),
                "group":      g.get("group", ""),
            })
        except (ValueError, TypeError):
            continue
    return results


def parse_upcoming_matches(raw: list) -> list[dict]:
    """
    Return list of unplayed matches in normalised format.
    """
    upcoming = []
    for g in raw:
        # Already normalised (fallback format — no upcoming)
        if "home" in g and "away" in g:
            continue
        if g.get("finished", "").upper() == "TRUE":
            continue
        try:
            upcoming.append({
                "home":    g.get("home_team_name_en", "?"),
                "away":    g.get("away_team_name_en", "?"),
                "stage":   STAGE_LABELS.get(g.get("type", ""), g.get("type", "Match")),
                "date":    g.get("local_date", ""),
                "matchday":g.get("matchday", ""),
                "group":   g.get("group", ""),
            })
        except Exception:
            continue
    return upcoming


def total_goals_from_matches(matches: list[dict]) -> int:
    """Sum total goals from a list of normalised match dicts."""
    return sum(
        m.get("home_score", 0) + m.get("away_score", 0)
        for m in matches
    )


def time_since_update(key: str = "matches") -> str:
    """
    Return a human-readable string describing when the cache was last updated.
    E.g. "Updated 47 min ago" or "Data Source: Kaggle (Swapnil Tripathi)".
    """
    cache = _load_cache()
    try:
        fetched_at = float(cache[key]["fetched_at"])
        age_secs   = time.time() - fetched_at
        if age_secs < 60:
            return "Updated just now"
        if age_secs < 3600:
            return f"Updated {int(age_secs // 60)} min ago"
        if age_secs < 86400:
            return f"Updated {int(age_secs // 3600)}h ago"
        days = int(age_secs // 86400)
        return f"Updated {days}d ago"
    except Exception:
        return "Data Source: Kaggle · FIFA WC 2026"


def get_last_updated(key: str = "matches") -> datetime.datetime | None:
    """Return the cache update time as a datetime, or None if unavailable."""
    cache = _load_cache()
    try:
        return datetime.datetime.fromtimestamp(float(cache[key]["fetched_at"]))
    except Exception:
        return None


def get_current_round() -> str:
    """Return the latest active/most-recent stage as a human label."""
    cache = _load_cache()
    try:
        games = cache["matches"]["data"]["games"]
        finished = [g for g in games if g.get("finished", "").upper() == "TRUE"]
        if not finished:
            return "Group Stage"
        last = finished[-1]
        return STAGE_LABELS.get(last.get("type", ""), "Tournament")
    except Exception:
        return "Tournament"


def get_games_played_count() -> int:
    """
    Return the approximate max group-stage games completed per team.
    Used by data_loader to dynamically set GAMES_PLAYED.
    """
    cache = _load_cache()
    try:
        games = cache["matches"]["data"]["games"]
        group_finished = [
            g for g in games
            if g.get("type") == "group" and g.get("finished", "").upper() == "TRUE"
        ]
        if not group_finished:
            return 3
        # Each group has 4 teams, each team plays 3 matches = 6 games per group
        # 12 groups × 6 = 72 group games total in a 48-team WC
        completed = len(group_finished)
        # Estimate games played per team from fraction of group stage done
        games_per_team = min(3, round(completed / 24))  # 24 = 12 groups × 2 games avg
        return max(1, games_per_team)
    except Exception:
        return 3
