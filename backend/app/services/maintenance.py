"""
Scheduled pool maintenance: TRIM and scrub once a week in a window the cafe
is closed, one after the other in the order the admin chose.

  window   a weekday and a start and end time (server local time; an end
           before the start means the next morning)
  steps    TRIM and / or scrub, in order; the second starts only when the
           first is done, so the disks never do both at once
  end      a step still running when the window ends is paused (scrub -p,
           trim -s) and resumes where it stopped in the next window

The job looks once a minute (MaintenanceJob). What it did in the current or
last window is kept in AppSetting `maintenance_last` for the Server page.
Only steps the job started are paused: a scrub the admin started by hand
is left alone.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.db.models import AppSetting
from app.services.server_status import ServerMonitor

logger = logging.getLogger("ggnet.maintenance")

SETTINGS_KEY = "maintenance"
LAST_KEY = "maintenance_last"
STEPS = ("trim", "scrub")
_HHMM = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


@dataclass(frozen=True)
class MaintenanceSettings:
    enabled: bool = False
    weekday: int = 6                 # 0 Monday … 6 Sunday
    start: str = "03:00"
    end: str = "07:00"
    trim: bool = True
    scrub: bool = True
    order: str = "trim_first"        # or "scrub_first"

    def steps(self) -> list[str]:
        ordered = list(STEPS) if self.order == "trim_first" else list(reversed(STEPS))
        return [s for s in ordered if getattr(self, s)]


def _hm(value: str) -> tuple[int, int]:
    m = _HHMM.match(value)
    if not m:
        raise ValueError(f"Invalid time {value!r}, expected HH:MM")
    return int(m.group(1)), int(m.group(2))


def window_at(s: MaintenanceSettings, now: datetime) -> tuple[datetime, datetime]:
    """The latest window that started at or before `now` (it may be over already)."""
    sh, sm = _hm(s.start)
    eh, em = _hm(s.end)
    days_back = (now.weekday() - s.weekday) % 7
    start = (now - timedelta(days=days_back)).replace(hour=sh, minute=sm, second=0, microsecond=0)
    if start > now:
        start -= timedelta(days=7)
    end = start.replace(hour=eh, minute=em)
    if end <= start:
        end += timedelta(days=1)
    return start, end


# ── Settings and the last run ─────────────────────────────────────────

def _get(db: Session, key: str) -> Any:
    row = db.get(AppSetting, key)
    return json.loads(row.value) if row else None


def _put(db: Session, key: str, value: Any) -> None:
    row = db.get(AppSetting, key)
    if row is None:
        db.add(AppSetting(key=key, value=json.dumps(value)))
    else:
        row.value = json.dumps(value)
    db.commit()


def load_settings(db: Session) -> MaintenanceSettings:
    values = _get(db, SETTINGS_KEY) or {}
    known = MaintenanceSettings.__dataclass_fields__
    return MaintenanceSettings(**{k: v for k, v in values.items() if k in known})


def save_settings(db: Session, s: MaintenanceSettings) -> None:
    _hm(s.start), _hm(s.end)
    _put(db, SETTINGS_KEY, asdict(s))


def last_run(db: Session) -> dict[str, Any] | None:
    return _get(db, LAST_KEY)


# ── One round ─────────────────────────────────────────────────────────

def _running(pool: dict[str, Any], step: str) -> bool:
    if step == "scrub":
        scan = pool.get("scan") or {}
        return scan.get("function") == "scrub" and scan.get("state") == "scanning" and not scan.get("paused")
    return any(d.get("trim_state") == "ACTIVE" for d in pool.get("disks", []))


def _busy(pool: dict[str, Any]) -> bool:
    """Something the job must not add load to: any scrub or resilver running, or a TRIM."""
    scan = pool.get("scan") or {}
    return (scan.get("state") == "scanning" and not scan.get("paused")) or _running(pool, "trim")


def _finished_well(pool: dict[str, Any], step: str) -> bool:
    if step == "scrub":
        return (pool.get("scan") or {}).get("state") == "finished"
    return all(d.get("trim_state") in ("COMPLETE", None) for d in pool.get("disks", []) if not d.get("trim_notsup"))


def _close(run: dict[str, Any], mon: ServerMonitor, now: datetime) -> None:
    """The window is over (or the schedule was turned off): pause what the job still runs."""
    pool = mon.pool()
    for step in run["steps"]:
        if step["status"] != "running":
            continue
        if pool and _running(pool, step["name"]):
            ok = mon.scrub_pause() if step["name"] == "scrub" else mon.trim(False)
            step["status"] = "paused" if ok else "failed"
            step["error"] = None if ok else mon.last_error
            logger.info("Maintenance window over: %s %s", step["name"], step["status"])
        else:
            step["status"] = "done" if pool and _finished_well(pool, step["name"]) else "stopped"
            step["finished_at"] = now.isoformat()
    run["closed"] = True


def tick(db: Session, mon: ServerMonitor, now: datetime | None = None) -> dict[str, Any] | None:
    """One look: start, advance or pause the steps of the current window. Returns the run."""
    s = load_settings(db)
    now = now or datetime.now()
    start, end = window_at(s, now)
    in_window = bool(s.enabled and s.steps()) and start <= now < end
    run = last_run(db)

    if run and not run.get("closed") and (not in_window or run["window_start"] != start.isoformat()):
        _close(run, mon, now)
        _put(db, LAST_KEY, run)
    if not in_window:
        return run
    if run is None or run["window_start"] != start.isoformat() or run.get("closed"):
        run = {"window_start": start.isoformat(), "window_end": end.isoformat(), "closed": False,
               "steps": [{"name": n, "status": "waiting", "started_at": None, "finished_at": None, "error": None}
                         for n in s.steps()]}
        logger.info("Maintenance window %s to %s: %s", start, end, ", then ".join(s.steps()))

    pool = mon.pool()
    if pool is None:
        _put(db, LAST_KEY, run)
        return run
    for step in run["steps"]:
        if step["status"] in ("done", "stopped", "failed"):
            continue
        if step["status"] == "running":
            if _running(pool, step["name"]):
                break                                   # wait for it
            step["status"] = "done" if _finished_well(pool, step["name"]) else "stopped"
            step["finished_at"] = now.isoformat()
            logger.info("Maintenance %s %s", step["name"], step["status"])
            continue
        # Waiting: start it (a scrub paused or a TRIM suspended earlier resumes where it stopped).
        if _busy(pool):
            break                                       # something else uses the disks; try again later
        ok = mon.scrub(True) if step["name"] == "scrub" else mon.trim(True)
        step["status"] = "running" if ok else "failed"
        step["started_at"] = now.isoformat()
        step["error"] = None if ok else mon.last_error
        logger.info("Maintenance %s %s", step["name"], "started" if ok else f"failed: {mon.last_error}")
        break
    _put(db, LAST_KEY, run)
    return run


class MaintenanceJob:
    """Background thread running tick() every minute."""

    def __init__(self, make_session: Callable[[], Session], monitor: ServerMonitor,
                 interval: timedelta = timedelta(seconds=60)):
        self.make_session = make_session
        self.monitor = monitor
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, name="ggnet-maintenance", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=10)

    def _loop(self) -> None:
        while not self._stop.wait(self.interval.total_seconds()):
            try:
                with self.make_session() as db:
                    tick(db, self.monitor)
            except Exception:
                logger.exception("Maintenance round failed")
