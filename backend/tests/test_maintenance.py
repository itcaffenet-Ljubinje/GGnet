"""Weekly TRIM and scrub in a maintenance window (app.services.maintenance, /api/v1/server/schedule)."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.session import make_engine
from app.services import maintenance
from app.services.maintenance import MaintenanceSettings, window_at

SUNDAY_3AM = datetime(2026, 10, 25, 3, 0)          # a Sunday


class FakeMonitor:
    """A pool whose scrub and TRIM run until the test finishes them."""

    def __init__(self):
        self.scan = {"function": "scrub", "state": "finished", "paused": False}
        self.trimming = False
        self.calls: list[str] = []
        self.last_error = ""

    def pool(self):
        return {"scan": dict(self.scan),
                "disks": [{"trim_state": "ACTIVE" if self.trimming else "COMPLETE", "trim_notsup": False}]}

    def scrub(self, start):
        self.calls.append("scrub" if start else "scrub -s")
        self.scan = {"function": "scrub", "state": "scanning" if start else "canceled", "paused": False}
        return True

    def scrub_pause(self):
        self.calls.append("scrub -p")
        self.scan["paused"] = True
        return True

    def trim(self, start):
        self.calls.append("trim" if start else "trim -s")
        self.trimming = start
        return True


@pytest.fixture
def db(db_url):
    engine = make_engine(db_url)
    with sessionmaker(bind=engine)() as session:
        yield session
    engine.dispose()


def _enable(db, **kw):
    maintenance.save_settings(db, MaintenanceSettings(enabled=True, **kw))


def test_window_at():
    s = MaintenanceSettings(weekday=6, start="03:00", end="07:00")
    assert window_at(s, SUNDAY_3AM) == (SUNDAY_3AM, SUNDAY_3AM.replace(hour=7))
    # Saturday: the window of last Sunday
    assert window_at(s, datetime(2026, 10, 24, 12))[0] == datetime(2026, 10, 18, 3)
    # A window over midnight: Saturday 23:00 to Sunday 05:00
    night = MaintenanceSettings(weekday=5, start="23:00", end="05:00")
    assert window_at(night, datetime(2026, 10, 25, 1)) == (datetime(2026, 10, 24, 23), datetime(2026, 10, 25, 5))


def test_nothing_happens_when_off_or_outside_the_window(db):
    mon = FakeMonitor()
    assert maintenance.tick(db, mon, SUNDAY_3AM) is None                    # not enabled
    _enable(db)
    assert maintenance.tick(db, mon, SUNDAY_3AM - timedelta(minutes=1)) is None
    assert mon.calls == []


def test_trim_then_scrub_one_after_the_other(db):
    _enable(db, order="trim_first")
    mon = FakeMonitor()
    run = maintenance.tick(db, mon, SUNDAY_3AM)
    assert mon.calls == ["trim"] and [s["status"] for s in run["steps"]] == ["running", "waiting"]
    maintenance.tick(db, mon, SUNDAY_3AM + timedelta(minutes=1))           # TRIM still runs: wait
    assert mon.calls == ["trim"]
    mon.trimming = False                                                    # TRIM done
    run = maintenance.tick(db, mon, SUNDAY_3AM + timedelta(minutes=20))
    assert mon.calls == ["trim", "scrub"]
    assert [s["status"] for s in run["steps"]] == ["done", "running"]
    mon.scan = {"function": "scrub", "state": "finished", "paused": False}
    run = maintenance.tick(db, mon, SUNDAY_3AM + timedelta(hours=1))
    assert [s["status"] for s in run["steps"]] == ["done", "done"]
    maintenance.tick(db, mon, SUNDAY_3AM + timedelta(hours=2))              # nothing more this window
    assert mon.calls == ["trim", "scrub"]


def test_scrub_first_and_only_the_chosen_steps(db):
    _enable(db, order="scrub_first")
    mon = FakeMonitor()
    maintenance.tick(db, mon, SUNDAY_3AM)
    assert mon.calls == ["scrub"]
    maintenance.save_settings(db, MaintenanceSettings(enabled=True, trim=False))
    db.query(maintenance.AppSetting).filter_by(key=maintenance.LAST_KEY).delete()
    db.commit()
    mon2 = FakeMonitor()
    run = maintenance.tick(db, mon2, SUNDAY_3AM + timedelta(days=7))
    assert [s["name"] for s in run["steps"]] == ["scrub"] and mon2.calls == ["scrub"]


def test_a_step_still_running_at_the_end_is_paused_and_resumed_next_week(db):
    _enable(db, order="scrub_first", trim=False)
    mon = FakeMonitor()
    maintenance.tick(db, mon, SUNDAY_3AM)
    run = maintenance.tick(db, mon, SUNDAY_3AM.replace(hour=7))             # window over
    assert mon.calls == ["scrub", "scrub -p"]
    assert run["closed"] and run["steps"][0]["status"] == "paused"
    maintenance.tick(db, mon, SUNDAY_3AM.replace(hour=9))                   # nothing more
    assert mon.calls == ["scrub", "scrub -p"]
    run = maintenance.tick(db, mon, SUNDAY_3AM + timedelta(days=7))         # `zpool scrub` resumes it
    assert mon.calls == ["scrub", "scrub -p", "scrub"]
    assert not run["closed"]


def test_waits_while_something_else_uses_the_disks(db):
    _enable(db)
    mon = FakeMonitor()
    mon.scan = {"function": "resilver", "state": "scanning", "paused": False}
    run = maintenance.tick(db, mon, SUNDAY_3AM)
    assert mon.calls == [] and run["steps"][0]["status"] == "waiting"


def test_a_scrub_started_by_hand_is_not_paused(db):
    _enable(db, trim=False)
    mon = FakeMonitor()
    mon.scan = {"function": "scrub", "state": "scanning", "paused": False}   # the admin's own scrub
    maintenance.tick(db, mon, SUNDAY_3AM)
    maintenance.tick(db, mon, SUNDAY_3AM.replace(hour=7))
    assert mon.calls == []


def test_schedule_api(client):
    r = client.get("/api/v1/server/schedule")
    assert r.status_code == 200
    assert r.json()["enabled"] is False and r.json()["next_window"] is None
    body = {"enabled": True, "weekday": 6, "start": "02:00", "end": "06:00",
            "trim": True, "scrub": True, "order": "scrub_first"}
    r = client.put("/api/v1/server/schedule", json=body)
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["order"] == "scrub_first" and out["next_window"].endswith("02:00:00")
    assert datetime.fromisoformat(out["next_window"]).weekday() == 6
    assert client.put("/api/v1/server/schedule", json={**body, "start": "25:00"}).status_code == 422
    assert client.put("/api/v1/server/schedule", json={**body, "order": "both"}).status_code == 422
