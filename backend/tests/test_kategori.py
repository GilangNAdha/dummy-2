# uji endpoint kategori (categories)
#
# Perhatian khusus pada aturan kategori sistem: terbaca semua rumah tangga,
# tidak bisa diubah atau dihapus siapa pun lewat API, dan server yang memaksa
# is_system = false pada POST.
import pytest
from fastapi.testclient import TestClient

from app.api.v1 import categories
from app.core import peran as modul_peran
from app.core.deps import get_access_token, get_current_user
from app.core.supabase_client import KODE_UNIK, KonflikData
from app.main import app

client = TestClient(app, raise_server_exceptions=False)

HID = "9f2c0000-0000-4000-8000-000000000001"
KID = "c1c2e3d4-0000-4000-8000-000000000001"
SID = "c9c9c9c9-0000-4000-8000-000000000009"
PENGGUNA = "11111111-1111-1111-1111-111111111111"

KATEGORI = {
    "id": KID,
    "household_id": HID,
    "name": "Jajan",
    "kind": "expense",
    "icon": "🍬",
    "color": "#F59E0B",
    "is_system": False,
    "is_archived": False,
    "created_at": "2026-10-04T00:00:00Z",
    "updated_at": "2026-10-04T00:00:00Z",
}

SISTEM = {
    "id": SID,
    "household_id": None,
    "name": "Lainnya",
    "kind": "income",
    "icon": "📦",
    "color": "#94A3B8",
    "is_system": True,
    "is_archived": False,
    "created_at": "2026-10-01T00:00:00Z",
    "updated_at": "2026-10-01T00:00:00Z",
}


@pytest.fixture
def masuk():
    app.dependency_overrides[get_current_user] = lambda: {"sub": PENGGUNA}
    app.dependency_overrides[get_access_token] = lambda: "token-uji"
    yield
    app.dependency_overrides.clear()


class BasisPalsu:
    def __init__(self, peran="ayah", baris=None, total=None, konflik=None, hasil_tulis=None, nama_terpakai=False):
        self.peran = peran
        self.baris = [dict(KATEGORI), dict(SISTEM)] if baris is None else baris
        self.total = len(self.baris) if total is None else total
        self.konflik = konflik
        self.hasil_tulis = hasil_tulis
        self.nama_terpakai = nama_terpakai
        self.panggilan = []

    def pasang(self, monkeypatch):
        monkeypatch.setattr(categories, "rest_select", self.select)
        monkeypatch.setattr(categories, "rest_hitung", self.hitung)
        monkeypatch.setattr(categories, "rest_insert", self.insert)
        monkeypatch.setattr(categories, "rest_patch", self.patch)
        monkeypatch.setattr(categories, "rest_delete", self.delete)
        monkeypatch.setattr(modul_peran, "rest_select", self.select)
        return self

    async def select(self, table, params, token=None):
        self.panggilan.append(("select", table, params))
        if table == "household_members":
            return [{"role": self.peran, "display_name": "Ayah"}] if self.peran else []
        if table == "categories":
            if params.get("id", "").startswith("eq."):
                target = params["id"][3:]
                return [b for b in self.baris if b["id"] == target]
            if params.get("id", "").startswith("neq."):
                tersisa = [b for b in self.baris if b["id"] != params["id"][4:]]
                return tersisa[:1] if self.nama_terpakai else []
            if "name" in params:  # pemeriksaan nama ganda
                return [dict(SISTEM)] if self.nama_terpakai else []
            return self.baris
        return []

    async def hitung(self, table, params, token=None):
        self.panggilan.append(("hitung", table, params))
        return self.total

    async def insert(self, table, payload, token=None):
        self.panggilan.append(("insert", table, payload))
        if self.konflik:
            raise self.konflik
        return self.hasil_tulis if self.hasil_tulis is not None else [{**KATEGORI, **payload, "id": KID}]

    async def patch(self, table, params, payload, token=None):
        self.panggilan.append(("patch", table, payload))
        if self.konflik:
            raise self.konflik
        if self.hasil_tulis is not None:
            return self.hasil_tulis
        return [{**KATEGORI, **payload}]

    async def delete(self, table, params, token=None):
        self.panggilan.append(("delete", table, params))
        if self.konflik:
            raise self.konflik
        return self.hasil_tulis if self.hasil_tulis is not None else [dict(KATEGORI)]


# ----------------------------------------------------------------- daftar
def test_daftar_tanpa_token_ditolak():
    res = client.get("/api/v1/categories", params={"household_id": HID})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHENTICATED"


def test_daftar_tanpa_household_id_ditolak(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.get("/api/v1/categories")
    assert res.status_code == 400
    assert res.json()["error"]["details"][0]["field"] == "household_id"


def test_daftar_memuat_kategori_sistem(masuk, monkeypatch):
    basis = BasisPalsu().pasang(monkeypatch)
    res = client.get("/api/v1/categories", params={"household_id": HID})
    assert res.status_code == 200
    nama = [k["name"] for k in res.json()["data"]]
    assert "Jajan" in nama and "Lainnya" in nama
    # permintaan ke PostgREST memakai or=(household_id.eq...,household_id.is.null)
    penyaring = basis.panggilan[1][2]
    assert penyaring["or"] == f"(household_id.eq.{HID},household_id.is.null)"


def test_daftar_menyaring_jenis_dan_arsip(masuk, monkeypatch):
    basis = BasisPalsu().pasang(monkeypatch)
    res = client.get("/api/v1/categories", params={"household_id": HID, "kind": "expense", "is_archived": False})
    assert res.status_code == 200
    penyaring = basis.panggilan[1][2]
    assert penyaring["kind"] == "eq.expense"
    assert penyaring["is_archived"] == "eq.false"


def test_sort_tak_dikenal_ditolak(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.get("/api/v1/categories", params={"household_id": HID, "sort": "is_system:asc"})
    assert res.status_code == 400


# ----------------------------------------------------------------- detail
def test_detail_kategori_rumah_tangga(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.get(f"/api/v1/categories/{KID}")
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Jajan"


def test_detail_kategori_sistem_terbaca(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.get(f"/api/v1/categories/{SID}")
    assert res.status_code == 200
    assert res.json()["data"]["is_system"] is True


def test_detail_tidak_ada_menjawab_404(masuk, monkeypatch):
    BasisPalsu(baris=[]).pasang(monkeypatch)
    res = client.get(f"/api/v1/categories/{KID}")
    assert res.status_code == 404


# ----------------------------------------------------------------- tambah
def test_tambah_kategori_berhasil_memaksa_is_system_false(masuk, monkeypatch):
    basis = BasisPalsu().pasang(monkeypatch)
    res = client.post(
        "/api/v1/categories",
        json={"household_id": HID, "name": "Jajan Anak", "kind": "expense", "icon": "🍬", "color": "#10B981"},
    )
    assert res.status_code == 201
    _, tabel, payload = basis.panggilan[-1]
    assert tabel == "categories"
    assert payload["is_system"] is False


def test_tambah_kategori_is_system_dari_klien_ditolak_400(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.post(
        "/api/v1/categories",
        json={"household_id": HID, "name": "Sistem Palsu", "kind": "expense", "is_system": True},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_tambah_kategori_warna_bukan_heksadesimal_ditolak_400(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.post(
        "/api/v1/categories",
        json={"household_id": HID, "name": "Warna Salah", "kind": "expense", "color": "merah"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["details"][0]["field"] == "color"


def test_tambah_kategori_kind_tak_dikenal_ditolak_400(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.post("/api/v1/categories", json={"household_id": HID, "name": "Salah", "kind": "transfer"})
    assert res.status_code == 400


def test_tambah_kategori_nama_sama_dengan_kategori_sistem_ditolak_409(masuk, monkeypatch):
    BasisPalsu(nama_terpakai=True).pasang(monkeypatch)
    res = client.post("/api/v1/categories", json={"household_id": HID, "name": "Lainnya", "kind": "income"})
    assert res.status_code == 409
    assert res.json()["error"]["message"] == "Nama kategori sudah dipakai."


def test_tambah_kategori_nama_ganda_di_basis_data_menjawab_409(masuk, monkeypatch):
    BasisPalsu(konflik=KonflikData(KODE_UNIK)).pasang(monkeypatch)
    res = client.post("/api/v1/categories", json={"household_id": HID, "name": "Jajan", "kind": "expense"})
    assert res.status_code == 409


def test_tambah_kategori_oleh_anak_ditolak_403(masuk, monkeypatch):
    BasisPalsu(peran="anak").pasang(monkeypatch)
    res = client.post("/api/v1/categories", json={"household_id": HID, "name": "Jajan Anak", "kind": "expense"})
    assert res.status_code == 403


# ----------------------------------------------------------------- ubah
def test_ubah_kategori_sebagian_berhasil(masuk, monkeypatch):
    basis = BasisPalsu().pasang(monkeypatch)
    res = client.patch(f"/api/v1/categories/{KID}", json={"is_archived": True})
    assert res.status_code == 200
    assert basis.panggilan[-1][2] == {"is_archived": True}


def test_ubah_kategori_badan_kosong_ditolak_400(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.patch(f"/api/v1/categories/{KID}", json={})
    assert res.status_code == 400


def test_ubah_kategori_sistem_ditolak_403(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.patch(f"/api/v1/categories/{SID}", json={"name": "Diretas"})
    assert res.status_code == 403
    assert res.json()["error"]["message"] == "Kategori sistem tidak boleh diubah."


def test_ubah_kategori_tidak_ada_menjawab_404(masuk, monkeypatch):
    BasisPalsu(baris=[]).pasang(monkeypatch)
    res = client.patch(f"/api/v1/categories/{KID}", json={"name": "Tidak Ada"})
    assert res.status_code == 404


def test_ubah_kategori_nama_ganda_menjawab_409(masuk, monkeypatch):
    BasisPalsu(nama_terpakai=True).pasang(monkeypatch)
    res = client.patch(f"/api/v1/categories/{KID}", json={"name": "Lainnya"})
    assert res.status_code == 409


def test_ubah_kategori_oleh_anak_ditolak_403(masuk, monkeypatch):
    BasisPalsu(peran="anak").pasang(monkeypatch)
    res = client.patch(f"/api/v1/categories/{KID}", json={"name": "Ditolak"})
    assert res.status_code == 403


# ----------------------------------------------------------------- hapus
def test_hapus_kategori_sah_menjawab_200(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.delete(f"/api/v1/categories/{KID}")
    assert res.status_code == 200
    assert res.json() == {"data": None, "message": "baris dihapus"}


def test_hapus_kategori_sistem_ditolak_403(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.delete(f"/api/v1/categories/{SID}")
    assert res.status_code == 403
    assert res.json()["error"]["message"] == "Kategori sistem tidak boleh dihapus."


def test_hapus_kategori_tidak_ada_menjawab_404(masuk, monkeypatch):
    BasisPalsu(baris=[]).pasang(monkeypatch)
    res = client.delete(f"/api/v1/categories/{KID}")
    assert res.status_code == 404


def test_hapus_kategori_oleh_anak_ditolak_403(masuk, monkeypatch):
    BasisPalsu(peran="anak").pasang(monkeypatch)
    res = client.delete(f"/api/v1/categories/{KID}")
    assert res.status_code == 403


# ------------------------------------------------- jalur galat yang tersisa
def test_ubah_kategori_hasil_kosong_menjawab_404(masuk, monkeypatch):
    BasisPalsu(hasil_tulis=[]).pasang(monkeypatch)
    res = client.patch(f"/api/v1/categories/{KID}", json={"color": "#000000"})
    assert res.status_code == 404


def test_hapus_kategori_hasil_kosong_menjawab_404(masuk, monkeypatch):
    BasisPalsu(hasil_tulis=[]).pasang(monkeypatch)
    res = client.delete(f"/api/v1/categories/{KID}")
    assert res.status_code == 404


def test_ubah_kategori_bentrok_basis_data_menjawab_409(masuk, monkeypatch):
    BasisPalsu(konflik=KonflikData(KODE_UNIK)).pasang(monkeypatch)
    res = client.patch(f"/api/v1/categories/{KID}", json={"is_archived": True})
    assert res.status_code == 409


def test_hapus_kategori_bentrok_basis_data_menjawab_409(masuk, monkeypatch):
    BasisPalsu(konflik=KonflikData(KODE_UNIK)).pasang(monkeypatch)
    res = client.delete(f"/api/v1/categories/{KID}")
    assert res.status_code == 409


def test_daftar_menyaring_kategori_sistem_saja(masuk, monkeypatch):
    basis = BasisPalsu(total=60).pasang(monkeypatch)
    res = client.get("/api/v1/categories", params={"household_id": HID, "is_system": True, "sort": "name:asc"})
    assert res.status_code == 200
    penyaring = basis.panggilan[1][2]
    assert penyaring["is_system"] == "eq.true"
    assert "is_system=true" in res.json()["links"]["next"]
    assert penyaring["order"] == "name.asc"


def test_tambah_kategori_berhasil_bila_nama_belum_dipakai(masuk, monkeypatch):
    basis = BasisPalsu(nama_terpakai=False).pasang(monkeypatch)
    res = client.post(
        "/api/v1/categories",
        json={"household_id": HID, "name": "Kebutuhan Anak", "kind": "expense", "color": "#3B82F6"},
    )
    assert res.status_code == 201
    assert any(p[0] == "select" and p[1] == "categories" for p in basis.panggilan)
