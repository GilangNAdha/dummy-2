# uji kerangka layanan
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_request_id_diteruskan():
    res = client.get("/health", headers={"X-Request-Id": "abc12345"})
    assert res.headers["X-Request-Id"] == "abc12345"


def test_request_id_dibuat_bila_kosong():
    res = client.get("/health")
    assert len(res.headers["X-Request-Id"]) == 8


def test_halaman_tidak_dikenal_memakai_bentuk_error_standar():
    res = client.get("/tidak_ada")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"
    assert "request_id" in res.json()["error"]
