import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DB_PATH = REPO_ROOT / "data" / "livelyborg.db"

ODDS_COLUMNS = [
    "avg_h", "avg_d", "avg_a", "max_h", "max_d", "max_a",
    "avg_o25", "avg_u25", "max_o25", "max_u25",
]
CLOSING_ODDS_COLUMNS = ["avg_ch", "avg_cd", "avg_ca", "psc_h", "psc_d", "psc_a"]
STAT_COLUMNS = ["hthg", "htag", "hs", "as_", "hst", "ast", "hc", "ac", "hy", "ay", "hr", "ar"]

MATCH_COLUMNS = (
    ["div", "season", "match_date", "kickoff_utc", "home_team", "away_team", "fthg", "ftag"]
    + STAT_COLUMNS + ODDS_COLUMNS + CLOSING_ODDS_COLUMNS
)
# home_div / away_div: each club's domestic division, filled for cross-country competitions (e.g. "CL")
FIXTURE_COLUMNS = ["div", "match_date", "kickoff_utc", "home_team", "away_team", "source", "home_div", "away_div"] + ODDS_COLUMNS
OVERLAY_COLUMNS = ["avg_h", "avg_d", "avg_a", "max_h", "max_d", "max_a"]
PRIMARY_FIXTURE_SOURCE = "football-data.co.uk"  # has odds, and wins when two sources list the same match

_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS matches (
    div TEXT NOT NULL,
    season TEXT NOT NULL,
    match_date TEXT NOT NULL,
    kickoff_utc TEXT,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    fthg INTEGER NOT NULL,
    ftag INTEGER NOT NULL,
    {", ".join(f"{c} INTEGER" for c in STAT_COLUMNS)},
    {", ".join(f"{c} REAL" for c in ODDS_COLUMNS + CLOSING_ODDS_COLUMNS)},
    PRIMARY KEY (div, match_date, home_team, away_team)
);
CREATE INDEX IF NOT EXISTS idx_matches_home ON matches (home_team);
CREATE INDEX IF NOT EXISTS idx_matches_away ON matches (away_team);
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches (match_date);

CREATE TABLE IF NOT EXISTS fixtures (
    div TEXT NOT NULL,
    match_date TEXT NOT NULL,
    kickoff_utc TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT '{PRIMARY_FIXTURE_SOURCE}',
    home_div TEXT,
    away_div TEXT,
    {", ".join(f"{c} REAL" for c in ODDS_COLUMNS)},
    PRIMARY KEY (div, match_date, home_team, away_team)
);

-- Market odds from a second source (The Odds API), kept apart from `fixtures` because each fixture
-- source replaces its own rows on every refresh. Merged into fixtures that have no odds of their own.
CREATE TABLE IF NOT EXISTS odds_overlay (
    div TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    kickoff_utc TEXT NOT NULL,
    avg_h REAL, avg_d REAL, avg_a REAL,
    max_h REAL, max_d REAL, max_a REAL,
    bookmakers INTEGER NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (div, home_team, away_team)
);

CREATE TABLE IF NOT EXISTS national_matches (
    match_date TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    fthg INTEGER NOT NULL,
    ftag INTEGER NOT NULL,
    tournament TEXT NOT NULL,
    neutral INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (match_date, home_team, away_team)
);

-- Append-only prediction ledger. Each row's hash covers its prediction and the previous
-- row's hash, so editing or deleting a past prediction breaks the chain. Only the
-- result columns (fthg ... graded_at) are filled in after the match.
-- Crest/emblem URLs reported by the fixture feeds, kept apart from `fixtures` because the primary
-- source (which has no crests) wins duplicate matches. kind is 'team' (key = our team name) or
-- 'league' (key = competition code, e.g. "E0" or "CL").
CREATE TABLE IF NOT EXISTS crests (
    kind TEXT NOT NULL,
    key TEXT NOT NULL,
    url TEXT NOT NULL,
    PRIMARY KEY (kind, key)
);

-- Accounts. The role is not stored: it is derived from the email on every request (see auth.py).
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    name TEXT,
    picture TEXT,
    created_at TEXT NOT NULL,
    last_login_at TEXT NOT NULL
);

-- Only a hash of the session token is stored, so a copy of the database cannot be used to sign in.
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id);

-- Fixtures a user saved. `snapshot` keeps what the card showed, so the entry survives the fixture
-- dropping off the upcoming list after kickoff.
CREATE TABLE IF NOT EXISTS saved_fixtures (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fixture_id TEXT NOT NULL,
    saved_at TEXT NOT NULL,
    snapshot TEXT NOT NULL,
    PRIMARY KEY (user_id, fixture_id)
);

-- Running scores from the live feed, display only: results are still graded from the official results
-- file (see tracking/ledger.py), never from these rows. Keyed by the ledger's fixture id.
CREATE TABLE IF NOT EXISTS live_scores (
    fixture_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    home_goals INTEGER,
    away_goals INTEGER,
    minute INTEGER,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS predictions (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    fixture_id TEXT NOT NULL UNIQUE,
    div TEXT NOT NULL,
    match_date TEXT NOT NULL,
    kickoff_utc TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    created_at TEXT NOT NULL,
    model TEXT NOT NULL,
    p_home REAL NOT NULL,
    p_draw REAL NOT NULL,
    p_away REAL NOT NULL,
    pick TEXT NOT NULL,
    pick_prob REAL NOT NULL,
    odds_h REAL,
    odds_d REAL,
    odds_a REAL,
    prev_hash TEXT NOT NULL,
    hash TEXT NOT NULL,
    fthg INTEGER,
    ftag INTEGER,
    correct INTEGER,
    graded_at TEXT
);

-- AI-written match explanations, generated in the background (one per fixture and predicted outcome)
CREATE TABLE IF NOT EXISTS explanations (
    fixture_id TEXT NOT NULL,
    pick TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (fixture_id, pick)
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def get_db_path() -> Path:
    return Path(os.getenv("LIVELYBORG_DB_PATH") or DEFAULT_DB_PATH)


@contextmanager
def connect(db_path: Optional[Path] = None) -> Iterator[sqlite3.Connection]:
    path = Path(db_path) if db_path else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")  # the API keeps reading while the scheduler writes
        conn.executescript(_SCHEMA)
        _migrate(conn)
        yield conn
        conn.commit()
    finally:
        conn.close()


def _migrate(conn: sqlite3.Connection) -> None:
    """Brings databases created by earlier versions up to the current schema."""
    fixture_cols = {r["name"] for r in conn.execute("PRAGMA table_info(fixtures)")}
    if "source" not in fixture_cols:
        conn.execute(f"ALTER TABLE fixtures ADD COLUMN source TEXT NOT NULL DEFAULT '{PRIMARY_FIXTURE_SOURCE}'")
    for col in ("home_div", "away_div"):
        if col not in fixture_cols:
            conn.execute(f"ALTER TABLE fixtures ADD COLUMN {col} TEXT")


def upsert_matches(conn: sqlite3.Connection, rows: Iterable[Dict]) -> int:
    placeholders = ", ".join("?" for _ in MATCH_COLUMNS)
    sql = f"INSERT OR REPLACE INTO matches ({', '.join(MATCH_COLUMNS)}) VALUES ({placeholders})"
    data = [tuple(r.get(c) for c in MATCH_COLUMNS) for r in rows]
    conn.executemany(sql, data)
    return len(data)


NATIONAL_COLUMNS = ["match_date", "home_team", "away_team", "fthg", "ftag", "tournament", "neutral"]


def upsert_national_matches(conn: sqlite3.Connection, rows: Iterable[Dict]) -> int:
    placeholders = ", ".join("?" for _ in NATIONAL_COLUMNS)
    data = [tuple(r[c] for c in NATIONAL_COLUMNS) for r in rows]
    conn.executemany(f"INSERT OR REPLACE INTO national_matches ({', '.join(NATIONAL_COLUMNS)}) VALUES ({placeholders})", data)
    return len(data)


def load_national_matches(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute("SELECT * FROM national_matches ORDER BY match_date").fetchall()


def replace_fixtures(conn: sqlite3.Connection, rows: Iterable[Dict], source: str = PRIMARY_FIXTURE_SOURCE) -> int:
    """
    Replaces one source's fixture snapshot. The primary source (with odds) overrides any
    other source's listing of the same match; other sources only add matches it lacks.
    """
    columns = ", ".join(FIXTURE_COLUMNS)
    placeholders = ", ".join("?" for _ in FIXTURE_COLUMNS)
    data = [tuple({**r, "source": source}.get(c) for c in FIXTURE_COLUMNS) for r in rows]
    conn.execute("DELETE FROM fixtures WHERE source = ?", (source,))
    if source == PRIMARY_FIXTURE_SOURCE:
        conn.executemany(f"INSERT OR REPLACE INTO fixtures ({columns}) VALUES ({placeholders})", data)
        conn.execute(
            """
            DELETE FROM fixtures WHERE source != ? AND EXISTS (
                SELECT 1 FROM fixtures p WHERE p.source = ? AND p.div = fixtures.div
                AND p.home_team = fixtures.home_team AND p.away_team = fixtures.away_team)
            """,
            (PRIMARY_FIXTURE_SOURCE, PRIMARY_FIXTURE_SOURCE),
        )
    else:
        conn.executemany(
            f"""
            INSERT OR IGNORE INTO fixtures ({columns}) SELECT {placeholders}
            WHERE NOT EXISTS (SELECT 1 FROM fixtures WHERE div = ? AND home_team = ? AND away_team = ?)
            """,
            [row + (row[0], row[3], row[4]) for row in data],
        )
    return conn.execute("SELECT COUNT(*) FROM fixtures WHERE source = ?", (source,)).fetchone()[0]


def upsert_crests(conn: sqlite3.Connection, rows: Iterable[Dict]) -> int:
    """Stores crest URLs ({"kind", "key", "url"}); a newer URL for the same team or league replaces the old one."""
    data = [(r["kind"], r["key"], r["url"]) for r in rows if r.get("url")]
    conn.executemany("INSERT OR REPLACE INTO crests (kind, key, url) VALUES (?, ?, ?)", data)
    return len(data)


def upsert_live_scores(conn: sqlite3.Connection, rows: Iterable[Dict]) -> int:
    data = [(r["fixture_id"], r["status"], r.get("home_goals"), r.get("away_goals"), r.get("minute"), r["updated_at"]) for r in rows]
    conn.executemany(
        "INSERT OR REPLACE INTO live_scores (fixture_id, status, home_goals, away_goals, minute, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        data,
    )
    return len(data)


def load_live_scores(conn: sqlite3.Connection) -> Dict[str, Dict]:
    return {r["fixture_id"]: dict(r) for r in conn.execute("SELECT * FROM live_scores")}


def crest_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM crests").fetchone()[0]


def load_crests(conn: sqlite3.Connection) -> Dict[str, Dict[str, str]]:
    """{"team": {name: url}, "league": {code: url}}"""
    out: Dict[str, Dict[str, str]] = {"team": {}, "league": {}}
    for r in conn.execute("SELECT kind, key, url FROM crests"):
        out.setdefault(r["kind"], {})[r["key"]] = r["url"]
    return out


def load_matches_since(conn: sqlite3.Connection, since_date: str) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM matches WHERE match_date >= ? ORDER BY match_date", (since_date,)
    ).fetchall()


def load_fixtures_after(conn: sqlite3.Connection, after_utc_iso: str) -> List[Dict]:
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM fixtures WHERE kickoff_utc > ? ORDER BY kickoff_utc, div", (after_utc_iso,)
    )]
    overlay = {(r["div"], r["home_team"], r["away_team"]): r for r in conn.execute("SELECT * FROM odds_overlay")}
    for row in rows:
        extra = overlay.get((row["div"], row["home_team"], row["away_team"]))
        if extra and row["avg_h"] is None:  # a fixture's own odds always win
            for col in OVERLAY_COLUMNS:
                row[col] = extra[col]
    return rows


def replace_odds_overlay(conn: sqlite3.Connection, rows: Iterable[Dict], divs: Iterable[str], fetched_at: str) -> int:
    """Replaces the overlay for the given divisions (others keep their last values) and drops stale kickoffs."""
    divs = list(divs)
    if divs:
        conn.execute(f"DELETE FROM odds_overlay WHERE div IN ({', '.join('?' for _ in divs)})", divs)
    data = [(r["div"], r["home_team"], r["away_team"], r["kickoff_utc"],
             *(r[c] for c in OVERLAY_COLUMNS), r["bookmakers"], fetched_at) for r in rows]
    conn.executemany(
        f"INSERT OR REPLACE INTO odds_overlay (div, home_team, away_team, kickoff_utc, {', '.join(OVERLAY_COLUMNS)}, "
        "bookmakers, fetched_at) VALUES (?, ?, ?, ?, " + ", ".join("?" for _ in OVERLAY_COLUMNS) + ", ?, ?)",
        data,
    )
    conn.execute("DELETE FROM odds_overlay WHERE kickoff_utc < ?", (fetched_at,))
    return len(data)


def load_head_to_head(conn: sqlite3.Connection, team_a: str, team_b: str, limit: int = 50) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT * FROM matches
        WHERE (home_team = ? AND away_team = ?) OR (home_team = ? AND away_team = ?)
        ORDER BY match_date DESC LIMIT ?
        """,
        (team_a, team_b, team_b, team_a, limit),
    ).fetchall()


def get_explanation(conn: sqlite3.Connection, fixture_id: str, pick: str) -> Optional[str]:
    row = conn.execute(
        "SELECT text FROM explanations WHERE fixture_id = ? AND pick = ?", (fixture_id, pick)
    ).fetchone()
    return row["text"] if row else None


def save_explanation(conn: sqlite3.Connection, fixture_id: str, pick: str, text: str, created_at: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO explanations (fixture_id, pick, text, created_at) VALUES (?, ?, ?, ?)",
        (fixture_id, pick, text, created_at),
    )


def get_meta(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value))


def data_status(conn: sqlite3.Connection) -> Dict:
    matches = conn.execute(
        "SELECT COUNT(*) AS n, MIN(match_date) AS first, MAX(match_date) AS last FROM matches"
    ).fetchone()
    national = conn.execute("SELECT COUNT(*) AS n, MAX(match_date) AS last FROM national_matches").fetchone()
    fixtures = conn.execute("SELECT COUNT(*) AS n FROM fixtures").fetchone()
    by_source = {r["source"]: r["n"] for r in conn.execute("SELECT source, COUNT(*) AS n FROM fixtures GROUP BY source")}
    ledger = conn.execute(
        "SELECT COUNT(*) AS n, SUM(graded_at IS NOT NULL) AS graded, SUM(correct) AS correct FROM predictions"
    ).fetchone()
    return {
        "historical_matches": matches["n"],
        "history_from": matches["first"],
        "history_to": matches["last"],
        "national_matches": national["n"],
        "national_history_to": national["last"],
        "fixtures_in_snapshot": fixtures["n"],
        "fixtures_by_source": by_source,
        "predictions_locked": ledger["n"],
        "predictions_graded": ledger["graded"] or 0,
        "predictions_correct": ledger["correct"] or 0,
        "last_history_refresh": get_meta(conn, "last_history_refresh"),
        "last_fixtures_refresh": get_meta(conn, "last_fixtures_refresh"),
        "last_fdorg_refresh": get_meta(conn, "last_fdorg_refresh"),
        "fdorg_unmatched_teams": get_meta(conn, "fdorg_unmatched_teams"),
        "last_cycle": get_meta(conn, "last_cycle"),
    }
