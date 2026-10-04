# uji endpoint dompet (accounts)
#
# Cara menguji mengikuti tests/test_profil.py: dependensi autentikasi ditimpa
# lewat app.dependency_overrides, lalu fungsi akses basis data diganti fungsi
# palsu. Yang diuji perilaku router, bukan jaringan.
import pytest
from fastapi.testclient import TestClient

from app.api.v1 import accounts
from app.core import peran as modul_peran
from app.core.deps import get_access_token, get_current_user
from app.core.supabase_client import KODE_KUNCI_ASING, KODE_UNIK, KonflikData
from app.main import app

client = TestClient(app, raise_server_exceptions=False)

HID = "9f2c0000-0000-4000-8000-000000000001"
AID = "a1c2e3d4-0000-4000-8000-000000000001"
PENGGUNA = "11111111-1111-1111-1111-111111111111"

BARIS = {
    "id": AID,
    "household_id": HID,
    "name": "BCA Utama",
    "type": "bank",
    "provider": "BCA",
    "opening_balance": 5000000,
    "is_active": True,
    "created_at": "2026-10-04T00:00:00Z",
    "updated_at": "2026-10-04T00:00:00Z",
}


@pytest.fixture
def masuk():
    app.dependency_overrides[get_current_user] = lambda: {"sub": PENGGUNA}
    app.dependency_overrides[get_access_token] = lambda: "token-uji"
    yield
    app.dependency_overrides.clear()


class BasisPalsu:
    """Pengganti fungsi akses basis data. Mencatat panggilan agar bisa diperiksa."""

    def __init__(self, peran="ayah", baris=None, total=1, konflik=None, hasil_tulis=None):
        self.peran = peran
        self.baris = [dict(BARIS)] if baris is None else baris
        self.total = total
        self.konflik = konflik
        self.hasil_tulis = hasil_tulis
        self.panggilan = []

    def pasang(self, monkeypatch):
        monkeypatch.setattr(accounts, "rest_select", self.select)
        monkeypatch.setattr(accounts, "rest_hitung", self.hitung)
        monkeypatch.setattr(accounts, "rest_insert", self.insert)
        monkeypatch.setattr(accounts, "rest_patch", self.patch)
        monkeypatch.setattr(accounts, "rest_delete", self.delete)
        monkeypatch.setattr(modul_peran, "rest_select", self.select)
        return self

    async def select(self, table, params, token=None):
        self.panggilan.append(("select", table, params))
        if table == "household_members":
            return [{"role": self.peran, "display_name": "Ayah"}] if self.peran else []
        if table == "accounts":
            if params.get("id", "").startswith("eq."):
                target = params["id"][3:]
                return [b for b in self.baris if b["id"] == target]
            return self.baris
        return []

    async def hitung(self, table, params, token=None):
        self.panggilan.append(("hitung", table, params))
        return self.total

    async def insert(self, table, payload, token=None):
        self.panggilan.append(("insert", table, payload))
        if self.konflik:
            raise self.konflik
        return self.hasil_tulis if self.hasil_tulis is not None else [{**BARIS, **payload, "id": AID}]

    async def patch(self, table, params, payload, token=None):
        self.panggilan.append(("patch", table, payload))
        if self.konflik:
            raise self.konflik
        if self.hasil_tulis is not None:
            return self.hasil_tulis
        return [{**BARIS, **payload}]

    async def delete(self, table, params, token=None):
        self.panggilan.append(("delete", table, params))
        if self.konflik:
            raise self.konflik
        return self.hasil_tulis if self.hasil_tulis is not None else [dict(BARIS)]


# ------------------------------------------------------------- daftar dompet
def test_daftar_tanpa_token_ditolak():
    res = client.get("/api/v1/accounts", params={"household_id": HID})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHENTICATED"


def test_daftar_tanpa_household_id_ditolak(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.get("/api/v1/accounts")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"
    assert res.json()["error"]["details"][0]["field"] == "household_id"


def test_daftar_berhasil_memuat_data_meta_dan_links(masuk, monkeypatch):
    basis = BasisPalsu(total=1).pasang(monkeypatch)
    res = client.get("/api/v1/accounts", params={"household_id": HID})
    assert res.status_code == 200
    isi = res.json()
    assert isi["data"][0]["name"] == "BCA Utama"
    assert isi["meta"] == {"page": 1, "per_page": 20, "total": 1}
    assert "next" in isi["links"] and "prev" in isi["links"]
    assert "X-Request-Id" in res.headers
    # query selalu menyaring household_id
    assert basis.panggilan[0][2]["household_id"] == f"eq.{HID}"


def test_penyaring_terbawa_ke_tautan(masuk, monkeypatch):
    BasisPalsu(total=60).pasang(monkeypatch)
    res = client.get("/api/v1/accounts", params={"household_id": HID, "type": "bank", "is_active": True})
    assert res.status_code == 200
    tautan = res.json()["links"]["next"]
    assert f"household_id={HID}" in tautan
    assert "type=bank" in tautan
    assert "is_active=true" in tautan


def test_per_page_dibatasi_seratus(masuk, monkeypatch):
    basis = BasisPalsu().pasang(monkeypatch)
    res = client.get("/api/v1/accounts", params={"household_id": HID, "per_page": 500})
    assert res.status_code == 200
    assert res.json()["meta"]["per_page"] == 100
    assert basis.panggilan[1][2]["limit"] == 100


def test_sort_kolom_tak_dikenal_ditolak(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.get("/api/v1/accounts", params={"household_id": HID, "sort": "provider:asc"})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_sort_sah_dipakai_di_query(masuk, monkeypatch):
    basis = BasisPalsu().pasang(monkeypatch)
    res = client.get("/api/v1/accounts", params={"household_id": HID, "sort": "name:asc"})
    assert res.status_code == 200
    assert basis.panggilan[1][2]["order"] == "name.asc"


# ------------------------------------------------------------- detail dompet
def test_detail_dompet_ada(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.get(f"/api/v1/accounts/{AID}")
    assert res.status_code == 200
    assert res.json()["data"]["id"] == AID


def test_detail_dompet_tidak_ada_menjawab_404(masuk, monkeypatch):
    BasisPalsu(baris=[]).pasang(monkeypatch)
    res = client.get(f"/api/v1/accounts/{AID}")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------- tambah dompet
def test_tambah_dompet_sah_menjawab_201(masuk, monkeypatch):
    basis = BasisPalsu().pasang(monkeypatch)
    res = client.post(
        "/api/v1/accounts",
        json={"household_id": HID, "name": "DANA", "type": "ewallet", "provider": "DANA", "opening_balance": 100000},
    )
    assert res.status_code == 201
    assert res.json()["data"]["name"] == "DANA"
    _, tabel, payload = basis.panggilan[-1]
    assert tabel == "accounts" and payload["opening_balance"] == 100000


@pytest.mark.parametrize(
    "isi",
    [
        {"household_id": HID, "name": "", "type": "bank"},
        {"household_id": HID, "name": "Dompet", "type": "kredit"},
        {"household_id": HID, "name": "Dompet", "type": "bank", "opening_balance": -1},
        {"household_id": HID, "name": "Dompet", "type": "bank", "opening_balance": 1000.5},
    ],
)
def test_tambah_dompet_tidak_valid_ditolak_400(masuk, monkeypatch, isi):
    BasisPalsu().pasang(monkeypatch)
    res = client.post("/api/v1/accounts", json=isi)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"
    assert res.json()["error"]["details"]


def test_tambah_dompet_nama_ganda_menjawab_409(masuk, monkeypatch):
    BasisPalsu(konflik=KonflikData(KODE_UNIK)).pasang(monkeypatch)
    res = client.post("/api/v1/accounts", json={"household_id": HID, "name": "BCA Utama", "type": "bank"})
    assert res.status_code == 409
    assert res.json()["error"]["message"] == "Nama dompet sudah dipakai."


def test_tambah_dompet_oleh_anak_ditolak_403(masuk, monkeypatch):
    BasisPalsu(peran="anak").pasang(monkeypatch)
    res = client.post("/api/v1/accounts", json={"household_id": HID, "name": "Dompet Anak", "type": "cash"})
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_tambah_dompet_oleh_bukan_anggota_ditolak_403(masuk, monkeypatch):
    BasisPalsu(peran=None).pasang(monkeypatch)
    res = client.post("/api/v1/accounts", json={"household_id": HID, "name": "Dompet Lain", "type": "cash"})
    assert res.status_code == 403
    assert res.json()["error"]["message"] == "Kamu bukan anggota rumah tangga itu."


# ----------------------------------------------------------------- ubah dompet
def test_ubah_dompet_sebagian_berhasil(masuk, monkeypatch):
    basis = BasisPalsu().pasang(monkeypatch)
    res = client.patch(f"/api/v1/accounts/{AID}", json={"name": "BCA Baru"})
    assert res.status_code == 200
    assert basis.panggilan[-1][2] == {"name": "BCA Baru"}


def test_ubah_dompet_badan_kosong_ditolak_400(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.patch(f"/api/v1/accounts/{AID}", json={})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_ubah_dompet_household_id_dikirim_ditolak_400(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.patch(f"/api/v1/accounts/{AID}", json={"household_id": HID})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_ubah_dompet_tidak_ada_menjawab_404(masuk, monkeypatch):
    BasisPalsu(baris=[]).pasang(monkeypatch)
    res = client.patch(f"/api/v1/accounts/{AID}", json={"name": "Tidak Ada"})
    assert res.status_code == 404


def test_ubah_dompet_nama_ganda_menjawab_409(masuk, monkeypatch):
    BasisPalsu(konflik=KonflikData(KODE_UNIK)).pasang(monkeypatch)
    res = client.patch(f"/api/v1/accounts/{AID}", json={"name": "Tunai"})
    assert res.status_code == 409
    assert res.json()["error"]["message"] == "Nama dompet sudah dipakai."


def test_ubah_dompet_oleh_anak_ditolak_403(masuk, monkeypatch):
    BasisPalsu(peran="anak").pasang(monkeypatch)
    res = client.patch(f"/api/v1/accounts/{AID}", json={"name": "Ditolak"})
    assert res.status_code == 403


# ---------------------------------------------------------------- hapus dompet
def test_hapus_dompet_sah_menjawab_200(masuk, monkeypatch):
    BasisPalsu().pasang(monkeypatch)
    res = client.delete(f"/api/v1/accounts/{AID}")
    assert res.status_code == 200
    assert res.json() == {"data": None, "message": "baris dihapus"}


def test_hapus_dompet_yang_dipakai_transaksi_menjawab_409(masuk, monkeypatch):
    BasisPalsu(konflik=KonflikData(KODE_KUNCI_ASING)).pasang(monkeypatch)
    res = client.delete(f"/api/v1/accounts/{AID}")
    assert res.status_code == 409
    assert res.json()["error"]["message"] == "Dompet masih dipakai transaksi."


def test_hapus_dompet_tidak_ada_menjawab_404(masuk, monkeypatch):
    BasisPalsu(baris=[]).pasang(monkeypatch)
    res = client.delete(f"/api/v1/accounts/{AID}")
    assert res.status_code == 404


def test_hapus_dompet_oleh_anak_ditolak_403(masuk, monkeypatch):
    BasisPalsu(peran="anak").pasang(monkeypatch)
    res = client.delete(f"/api/v1/accounts/{AID}")
    assert res.status_code == 403


# ------------------------------------------------- jalur galat yang tersisa
def test_ubah_dompet_hasil_kosong_menjawab_404(masuk, monkeypatch):
    """RLS menyaring baris saat PATCH: PostgREST mengembalikan daftar kosong."""
    BasisPalsu(hasil_tulis=[]).pasang(monkeypatch)
    res = client.patch(f"/api/v1/accounts/{AID}", json={"name": "Tidak Terlihat"})
    assert res.status_code == 404


def test_hapus_dompet_hasil_kosong_menjawab_404(masuk, monkeypatch):
    BasisPalsu(hasil_tulis=[]).pasang(monkeypatch)
    res = client.delete(f"/api/v1/accounts/{AID}")
    assert res.status_code == 404


def test_daftar_dompet_diarsipkan_dan_penyaring_is_active_false(masuk, monkeypatch):
    basis = BasisPalsu(total=60).pasang(monkeypatch)
    res = client.get("/api/v1/accounts", params={"household_id": HID, "is_active": False, "sort": "opening_balance:desc"})
    assert res.status_code == 200
    penyaring = basis.panggilan[1][2]
    assert penyaring["is_active"] == "eq.false"
    assert penyaring["order"] == "opening_balance.desc"
    assert "sort=opening_balance%3Adesc" in res.json()["links"]["next"]
