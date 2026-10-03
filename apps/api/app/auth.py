"""
Sign in with Google, server-side sessions and role-based access.

- The browser sends the Google ID token; we verify its signature, audience (GOOGLE_CLIENT_ID),
  expiry and that Google has verified the email. Only then is a session created.
- The session is a random token in an HttpOnly cookie. Only its SHA-256 hash is stored.
- The role is never stored or sent by the client: it is computed from the verified email on every
  request. ADMIN_EMAILS (comma-separated) lists the admins and defaults to the site owner.
"""
import datetime as dt
import hashlib
import os
import secrets
from typing import Dict, Optional

from fastapi import Depends, HTTPException, Request

from apps.api.app.data import db
from apps.api.app.models.accounts import User

COOKIE_NAME = "lb_session"
SESSION_DAYS = 30
DEFAULT_ADMIN_EMAILS = "devtonicllc@gmail.com"


def normalise_email(email: str) -> str:
    return (email or "").strip().lower()


def admin_emails() -> set:
    raw = os.getenv("ADMIN_EMAILS", DEFAULT_ADMIN_EMAILS)
    return {normalise_email(e) for e in raw.split(",") if e.strip()}


def role_for(email: str) -> str:
    return "admin" if normalise_email(email) in admin_emails() else "user"


def google_client_id() -> Optional[str]:
    return os.getenv("GOOGLE_CLIENT_ID") or None


def verify_google_credential(credential: str) -> Dict:
    """
    Returns the verified claims of a Google ID token, or raises ValueError. Kept as one small function so
    tests can replace it without network access.
    """
    client_id = google_client_id()
    if not client_id:
        raise ValueError("Google sign-in is not configured on the server")
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    claims = id_token.verify_oauth2_token(credential, google_requests.Request(), client_id)
    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise ValueError("Wrong token issuer")
    if not claims.get("email") or claims.get("email_verified") is not True:
        raise ValueError("Google has not verified this email address")
    return claims


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def create_session(claims: Dict) -> str:
    """Creates or updates the user and returns a new session token (the cookie value)."""
    email = normalise_email(claims["email"])
    now = _now()
    token = secrets.token_urlsafe(32)
    with db.connect() as conn:
        conn.execute(
            """
            INSERT INTO users (email, name, picture, created_at, last_login_at) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET name = excluded.name, picture = excluded.picture,
                                             last_login_at = excluded.last_login_at
            """,
            (email, claims.get("name"), claims.get("picture"), now.isoformat(), now.isoformat()),
        )
        user_id = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()["id"]
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now.isoformat(),))
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (_hash(token), user_id, now.isoformat(), (now + dt.timedelta(days=SESSION_DAYS)).isoformat()),
        )
    return token


def delete_session(token: str) -> None:
    with db.connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash(token),))


def user_for_token(token: Optional[str]) -> Optional[Dict]:
    """The signed-in user's row (id, email, name, picture) for a session token, or None."""
    if not token:
        return None
    with db.connect() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.email, u.name, u.picture FROM sessions s JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ? AND s.expires_at > ?
            """,
            (_hash(token), _now().isoformat()),
        ).fetchone()
    return dict(row) if row else None


def to_user(row: Dict) -> User:
    return User(email=row["email"], name=row["name"], picture=row["picture"], role=role_for(row["email"]))


def optional_user(request: Request) -> Optional[Dict]:
    return user_for_token(request.cookies.get(COOKIE_NAME))


def require_user(user: Optional[Dict] = Depends(optional_user)) -> Dict:
    if not user:
        raise HTTPException(status_code=401, detail="Sign in to continue")
    return user


def require_admin_role(user: Dict = Depends(require_user)) -> Dict:
    if role_for(user["email"]) != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")
    return user


def cookie_secure(request: Request) -> bool:
    """Secure cookies whenever the visitor reached us over HTTPS (directly or behind a proxy)."""
    override = os.getenv("COOKIE_SECURE")
    if override is not None:
        return override == "1"
    return request.url.scheme == "https" or request.headers.get("x-forwarded-proto", "").split(",")[0].strip() == "https"
