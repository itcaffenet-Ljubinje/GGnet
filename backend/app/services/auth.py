"""
Sign-in for the web UI and API.

Users have a role: `admin` may do everything, `staff` sees everything and may
only turn PCs on, shut them down and restart them (allowed() below). A
signed-in browser holds a random session token in an HttpOnly cookie; scripts
may send the same token as `Authorization: Bearer`. Only a SHA-256 of the
token is stored, so a copy of the database signs nobody in. Passwords are
hashed with scrypt (standard library, no extra package).

The first admin is created from the web UI with a one-time setup code, so
whoever opens the UI first on the cafe network does not become the admin:
the code is written to `<data_dir>/setup-code` while there is no user, and
the installer prints it.

What the PCs use (the iPXE script, the agent's heartbeat and download, the
Secure Boot certificate) needs no sign-in.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import re
import secrets
import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import get_config
from app.db.models import Activity, AuthSession, User, UserRole

logger = logging.getLogger("ggnet.auth")

COOKIE = "ggnet_session"
SESSION_HOURS = 12
USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,31}$")
PASSWORD_MIN = 8
_SCRYPT = {"n": 2**14, "r": 8, "p": 1}


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, dklen=32, **_SCRYPT)
    return "scrypt${n}${r}${p}${salt}${digest}".format(
        **_SCRYPT, salt=base64.b64encode(salt).decode(), digest=base64.b64encode(digest).decode())


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, digest = stored.split("$")
        if scheme != "scrypt":
            return False
        got = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt), dklen=32,
                             n=int(n), r=int(r), p=int(p))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(got, base64.b64decode(digest))


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def start_session(db: Session, user: User, ip: str | None) -> str:
    """A new session for the user; returns its token (shown once, never stored)."""
    token = secrets.token_urlsafe(32)
    now = _now()
    db.execute(delete(AuthSession).where(AuthSession.expires_at < now))
    db.add(AuthSession(token_hash=_token_hash(token), user_id=user.id, ip_address=ip,
                       created_at=now, expires_at=now + timedelta(hours=SESSION_HOURS)))
    user.last_login_at = now
    db.commit()
    return token


def user_for(db: Session, token: str | None) -> User | None:
    """The signed-in user of a token; None when unknown, expired or disabled."""
    if not token:
        return None
    s = db.scalar(select(AuthSession).where(AuthSession.token_hash == _token_hash(token)))
    if s is None or s.expires_at < _now() or s.user.disabled:
        return None
    return s.user


def end_session(db: Session, token: str | None) -> None:
    if token:
        db.execute(delete(AuthSession).where(AuthSession.token_hash == _token_hash(token)))
        db.commit()


def end_sessions_of(db: Session, user_id: int) -> None:
    """Sign a user out everywhere (password changed, disabled, deleted)."""
    db.execute(delete(AuthSession).where(AuthSession.user_id == user_id))


def user_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User)) or 0


def admin_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User).where(
        User.role == UserRole.ADMIN, User.disabled.is_(False))) or 0


# ── What staff may do ─────────────────────────────────────────────────

_STAFF_WRITES = (
    re.compile(r"^/api/v1/machines/\d+/power$"),
    re.compile(r"^/api/v1/machines/bulk$"),      # the endpoint allows staff the power actions only
    re.compile(r"^/api/v1/auth/(logout|password)$"),
)


def allowed(user: User, method: str, path: str) -> bool:
    if user.role is UserRole.ADMIN:
        return True
    if method in ("GET", "HEAD"):
        return not path.startswith("/api/v1/users") and not path.startswith("/api/v1/activity")
    return any(p.match(path) for p in _STAFF_WRITES)


def record(db: Session, user: User | None, method: str, path: str, status_code: int,
           ip: str | None) -> None:
    """One activity log entry; never fails the request it describes."""
    try:
        db.add(Activity(username=user.username if user else None, action=f"{method} {path}"[:200],
                        status_code=status_code, ip_address=ip))
        db.commit()
    except Exception:
        logger.exception("Writing the activity log failed")
        db.rollback()


# ── First admin ───────────────────────────────────────────────────────

def setup_code_path(cfg: dict | None = None) -> Path:
    cfg = cfg if cfg is not None else get_config()
    return Path(cfg["paths"]["data_dir"]) / "setup-code"


def setup_code(db: Session, path: Path | None = None) -> str | None:
    """
    The one-time code that creates the first admin; made while there is no
    user and removed once there is one. None when users exist.
    """
    path = path or setup_code_path()
    if user_count(db) > 0:
        path.unlink(missing_ok=True)
        return None
    try:
        code = path.read_text().strip()
        if code:
            return code
    except OSError:
        pass
    code = "-".join(secrets.token_hex(2) for _ in range(3))      # e.g. 3f9a-0c71-b2e4
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code + "\n")
        path.chmod(0o600)
    except OSError as e:
        logger.error("Cannot write the setup code to %s: %s", path, e)
        return None
    logger.warning("No users yet: create the first admin in the web UI with setup code %s", code)
    return code


# ── Too many wrong passwords ──────────────────────────────────────────

class LoginThrottle:
    """At most `limit` failed sign-ins per IP address in `window` seconds."""

    def __init__(self, limit: int = 5, window: float = 300.0):
        self.limit = limit
        self.window = window
        self._failures: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, ip: str, now: float) -> deque[float]:
        q = self._failures.setdefault(ip, deque())
        while q and now - q[0] > self.window:
            q.popleft()
        return q

    def blocked(self, ip: str) -> bool:
        with self._lock:
            return len(self._recent(ip, time.monotonic())) >= self.limit

    def failed(self, ip: str) -> None:
        with self._lock:
            self._recent(ip, time.monotonic()).append(time.monotonic())

    def succeeded(self, ip: str) -> None:
        with self._lock:
            self._failures.pop(ip, None)
