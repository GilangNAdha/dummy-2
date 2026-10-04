# uji endpoint profil
import pytest
from fastapi.testclient import TestClient

from app.api.v1 import profiles
from app.core.deps import get_access_token, get_current_user
from app.main import app

client = TestClient(app, raise_server_exceptions=False)

BARIS = {
    "id": "b3c1a7e2",
    "email": "budi@gmail.com",
    "full_name": "Budi Santoso",
    "avatar_emoji": "",
    "created_at": "2026-09-20T01:00:00Z",
}


def test_tanpa_token_ditolak():
    res = client.get("/api/v1/profiles/me")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHENTICATED"


def test_ubah_tanpa_token_ditolak():
    res = client.patch("/api/v1/profiles/me", json={"full_name": "Budi"})
    assert res.status_code == 401


@pytest.fixture
def masuk():
    app.dependency_overrides[get_current_user] = lambda: {"sub": "b3c1a7e2"}
    app.dependency_overrides[get_access_token] = lambda: "token-uji"
    yield
    app.dependency_overrides.clear()


def test_baca_profil(monkeypatch, masuk):
    async def palsu(table, params, token):
        assert table == "profiles"
        assert params["id"] == "eq.b3c1a7e2"
        assert token == "token-uji"
        return [BARIS]

    monkeypatch.setattr(profiles, "rest_select", palsu)
    res = client.get("/api/v1/profiles/me")
    assert res.status_code == 200
    assert res.json()["data"]["full_name"] == "Budi Santoso"


def test_profil_kosong_menjawab_404(monkeypatch, masuk):
    async def palsu(table, params, token):
        return []

    monkeypatch.setattr(profiles, "rest_select", palsu)
    res = client.get("/api/v1/profiles/me")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


def test_ubah_profil(monkeypatch, masuk):
    async def palsu(table, params, payload, token):
        assert payload == {"full_name": "Budi Santoso"}
        return [{**BARIS, "full_name": "Budi Santoso"}]

    monkeypatch.setattr(profiles, "rest_patch", palsu)
    res = client.patch("/api/v1/profiles/me", json={"full_name": "Budi Santoso"})
    assert res.status_code == 200
    assert res.json()["data"]["full_name"] == "Budi Santoso"


def test_badan_kosong_ditolak(masuk):
    res = client.patch("/api/v1/profiles/me", json={})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_nama_terlalu_pendek_ditolak(masuk):
    res = client.patch("/api/v1/profiles/me", json={"full_name": "B"})
    assert res.status_code == 400
    assert res.json()["error"]["details"][0]["field"] == "full_name"
