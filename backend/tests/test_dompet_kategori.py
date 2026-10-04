# uji endpoint dompet (/accounts) dan kategori (/categories)
# Penulis: Gilang Nur Adha
import pytest
from fastapi.testclient import TestClient

from app.api.v1 import accounts, categories
from app.core import peran
from app.core.deps import get_access_token, get_current_user
from app.main import app

client = TestClient(app, raise_server_exceptions=False)
RT = "rt-1"
DOMPET = {"id": "d1", "household_id": RT, "name": "BCA Utama", "type": "bank", "icon": "🏦",
          "opening_balance": 8500000, "is_archived": False}
SISTEM = {"id": "k1", "household_id": None, "name": "Transportasi", "kind": "expense", "is_system": True}
KELUARGA = {"id": "k2", "household_id": RT, "name": "Arisan", "kind": "expense", "is_system": False}


class Palsu:
    """Tiruan PostgREST sederhana, mencatat panggilan tulis."""

    def __init__(self, role="ayah"):
        self.role = role
        self.ganda = False
        self.ditulis = []

    async def select(self, table, params, token):
        if table == "household_members":
            return [{"role": self.role}] if self.role else []
        if params.get("select") == "id":  # cek nama ganda
            return [{"id": "lain"}] if self.ganda else []
        data = {"d1": DOMPET, "k1": SISTEM, "k2": KELUARGA}
        if "id" in params:
            baris = data.get(params["id"].removeprefix("eq."))
            return [baris] if baris else []
        return [DOMPET] if table == "accounts" else [SISTEM, KELUARGA]

    async def hitung(self, table, params, token):
        return 1 if table == "accounts" else 2

    async def insert(self, table, payload, token):
        self.ditulis.append(("insert", table, payload))
        return [{"id": "baru", **payload}]

    async def patch(self, table, params, payload, token):
        self.ditulis.append(("patch", table, payload))
        return [{**DOMPET, **payload}]

    async def delete(self, table, params, token):
        self.ditulis.append(("delete", table, params))
        return []


@pytest.fixture
def db(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: {"sub": "u1"}
    app.dependency_overrides[get_access_token] = lambda: "token-uji"
    p = Palsu()
    monkeypatch.setattr(peran, "rest_select", p.select)
    for modul in (accounts, categories):
        monkeypatch.setattr(modul, "rest_select", p.select)
        monkeypatch.setattr(modul, "rest_hitung", p.hitung)
        monkeypatch.setattr(modul, "rest_insert", p.insert)
        monkeypatch.setattr(modul, "rest_patch", p.patch)
        monkeypatch.setattr(modul, "rest_delete", p.delete)
    yield p
    app.dependency_overrides.clear()


# ---------- autentikasi ----------
@pytest.mark.parametrize("url", ["/api/v1/accounts?household_id=rt-1", "/api/v1/categories?household_id=rt-1"])
def test_tanpa_token_401(url):
    assert client.get(url).status_code == 401


# ---------- dompet ----------
def test_daftar_dompet(db):
    res = client.get(f"/api/v1/accounts?household_id={RT}")
    assert res.status_code == 200
    isi = res.json()
    assert isi["data"][0]["name"] == "BCA Utama"
    assert isi["meta"] == {"page": 1, "per_page": 20, "total": 1}
    assert "X-Request-Id" in res.headers


def test_bukan_anggota_403(db):
    db.role = None
    res = client.get(f"/api/v1/accounts?household_id={RT}")
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_tambah_dompet(db):
    res = client.post("/api/v1/accounts", json={"household_id": RT, "name": " GoPay ", "type": "ewallet"})
    assert res.status_code == 201
    assert db.ditulis[0][2]["name"] == "GoPay"


@pytest.mark.parametrize("peran_ok", ["ayah", "ibu"])
def test_ayah_ibu_boleh_menulis(db, peran_ok):
    db.role = peran_ok
    assert client.patch("/api/v1/accounts/d1", json={"is_archived": True}).status_code == 200


def test_anak_tidak_boleh_menulis(db):
    db.role = "anak"
    assert client.post("/api/v1/accounts", json={"household_id": RT, "name": "OVO"}).status_code == 403
    assert client.delete("/api/v1/accounts/d1").status_code == 403
    assert db.ditulis == []


def test_anak_boleh_membaca(db):
    db.role = "anak"
    assert client.get("/api/v1/accounts/d1").status_code == 200


def test_nama_dompet_ganda_409(db):
    db.ganda = True
    res = client.post("/api/v1/accounts", json={"household_id": RT, "name": "BCA Utama"})
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "CONFLICT"


@pytest.mark.parametrize("badan", [
    {"household_id": RT, "name": "X", "opening_balance": 1000.5},   # uang harus bilangan bulat
    {"household_id": RT, "name": "X", "opening_balance": -1},       # tidak boleh negatif
    {"household_id": RT, "name": "X", "type": "kripto"},            # jenis tidak dikenal
    {"household_id": RT, "name": ""},                               # nama kosong
    {"household_id": RT, "name": "X", "nomor_rekening": "123"},     # kolom asing ditolak
])
def test_validasi_dompet_400(db, badan):
    res = client.post("/api/v1/accounts", json=badan)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_ubah_tanpa_kolom_400(db):
    assert client.patch("/api/v1/accounts/d1", json={}).status_code == 400


def test_dompet_tidak_ada_404(db):
    assert client.get("/api/v1/accounts/zzz").status_code == 404


def test_hapus_dompet_204(db):
    assert client.delete("/api/v1/accounts/d1").status_code == 204
    assert db.ditulis[0][0] == "delete"


# ---------- kategori ----------
def test_daftar_kategori_termasuk_sistem(db):
    res = client.get(f"/api/v1/categories?household_id={RT}&kind=expense")
    assert res.status_code == 200
    assert [k["id"] for k in res.json()["data"]] == ["k1", "k2"]
    assert "kind=expense" in (res.json()["links"]["next"] or "kind=expense")


def test_tambah_kategori(db):
    res = client.post("/api/v1/categories", json={"household_id": RT, "name": "Arisan", "color": "#123ABC"})
    assert res.status_code == 201
    assert db.ditulis[0][2]["is_system"] is False


def test_warna_salah_400(db):
    res = client.post("/api/v1/categories", json={"household_id": RT, "name": "A", "color": "merah"})
    assert res.status_code == 400


def test_nama_kategori_ganda_409(db):
    db.ganda = True
    assert client.post("/api/v1/categories", json={"household_id": RT, "name": "Arisan"}).status_code == 409


@pytest.mark.parametrize("aksi", ["patch", "delete"])
def test_kategori_sistem_selalu_403(db, aksi):
    if aksi == "patch":
        res = client.patch("/api/v1/categories/k1", json={"name": "Ubah"})
    else:
        res = client.delete("/api/v1/categories/k1")
    assert res.status_code == 403
    assert db.ditulis == []


def test_anak_tidak_boleh_ubah_kategori(db):
    db.role = "anak"
    assert client.patch("/api/v1/categories/k2", json={"name": "Baru"}).status_code == 403


def test_induk_diri_sendiri_400(db):
    assert client.patch("/api/v1/categories/k2", json={"parent_id": "k2"}).status_code == 400


def test_ubah_dan_hapus_kategori_keluarga(db):
    assert client.patch("/api/v1/categories/k2", json={"icon": "🎁"}).status_code == 200
    assert client.delete("/api/v1/categories/k2").status_code == 204


def test_detail_kategori_sistem(db):
    assert client.get("/api/v1/categories/k1").json()["data"]["is_system"] is True
