from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "pool" in body


def test_the_access_log_keeps_changes_errors_and_boots_only():
    import logging

    from app.main import QuietAccessLog

    def rec(method, path, status):
        return logging.LogRecord("uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d',
                                 ("192.168.0.253:5000", method, path, "1.1", status), None)
    keep = QuietAccessLog().filter
    assert not keep(rec("GET", "/api/v1/machines", 200))
    assert not keep(rec("GET", "/api/v1/machines/traffic", 200))
    assert not keep(rec("POST", "/api/v1/agent/heartbeat", 200))
    assert keep(rec("POST", "/api/v1/machines/3/power", 200))
    assert keep(rec("GET", "/api/v1/machines", 401))
    assert keep(rec("POST", "/api/v1/agent/heartbeat", 404))          # an unknown PC
    assert keep(rec("GET", "/api/v1/boot/ipxe?mac=18:c0:4d:4f:ae:dc", 200))
    assert keep(logging.LogRecord("uvicorn.access", logging.INFO, "", 0, "odd", None, None))
