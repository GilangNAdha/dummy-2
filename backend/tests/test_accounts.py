# uji router /accounts dan service saldo berjalan
# Penulis: Gilang Nur Adha
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.account_service import hitung_saldo
from tests.palsu_supabase import RT, db  # noqa: F401

client = TestClient(app, raise_server_exceptions=False)
URL = "/api/v1/accounts"


# ---------- service saldo (tanpa HTTP) ----------
D = [{"id": "a", "opening_balance": 1000}, {"id": "b", "opening_balance": 500}]


def test_saldo_hanya_saldo_awal():
    assert hitung_saldo(D, []) == {"a": 1000, "b": 500}


def test_pemasukan_menambah_pengeluaran_mengurangi():
    t = [{"account_id": "a", "type": "income", "amount": 300}, {"account_id": "a", "type": "expense", "amount": 100}]
    assert hitung_saldo(D, t)["a"] == 1200


def test_transfer_memindahkan_tanpa_mengubah_total():
    t = [{"account_id": "a", "to_account_id": "b", "type": "transfer", "amount": 400}]
    hasil = hitung_saldo(D, t)
    assert hasil == {"a": 600, "b": 900}
    assert sum(hasil.values()) == 1500


def test_transaksi_terhapus_diabaikan():
    t = [{"account_id": "a", "type": "expense", "amount": 999, "deleted_at": "2026-10-01T00:00:00Z"}]
    assert hitung_saldo(D, t)["a"] == 1000


def test_hasil_bilangan_bulat():
    hasil = hitung_saldo([{"id": "a", "opening_balance": 0}], [{"account_id": "a", "type": "income", "amount": 7}])
    assert hasil["a"] == 7 and isinstance(hasil["a"], int)


# ---------- autentikasi dan baca ----------
def test_tanpa_token_401():
    res = client.get(f"{URL}?household_id={RT}")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHENTICATED"


def test_daftar_bentuk_dan_current_balance(db):
    db.tabel["transactions"] = [
        {"household_id": RT, "account_id": "d1", "to_account_id": None, "type": "expense", "amount": 250000},
        {"household_id": RT, "account_id": "d1", "to_account_id": "d2", "type": "transfer", "amount": 100000},
    ]
    res = client.get(f"{URL}?household_id={RT}&sort=name:asc")
    assert res.status_code == 200
    isi = res.json()
    assert set(isi) == {"data", "meta", "links"}
    assert isi["meta"] == {"page": 1, "per_page": 20, "total": 2}
    saldo = {d["name"]: d["current_balance"] for d in isi["data"]}
    assert saldo == {"BCA Utama": 650000, "Tunai": 100000}
    assert "X-Request-Id" in res.headers
    assert db.params_terakhir["accounts"]["order"] == "name.asc"
    # satu query transaksi untuk semua dompet, transaksi terhapus disaring
    q = db.params_terakhir["transactions"]
    assert q["deleted_at"] == "is.null" and "d1,d2" in q["or"]


def test_saringan_household_selalu_diterapkan(db):
    res = client.get(f"{URL}?household_id={RT}")
    assert db.params_terakhir["accounts"]["household_id"] == f"eq.{RT}"
    assert all(d["household_id"] == RT for d in res.json()["data"])


def test_urutan_bawaan_created_at_menurun(db):
    client.get(f"{URL}?household_id={RT}")
    assert db.params_terakhir["accounts"]["order"] == "created_at.desc"


def test_paginasi_dibatasi_100(db):
    res = client.get(f"{URL}?household_id={RT}&per_page=500")
    assert res.json()["meta"]["per_page"] == 100


def test_saring_jenis_dan_aktif(db):
    res = client.get(f"{URL}?household_id={RT}&type=cash&is_active=true")
    assert [d["name"] for d in res.json()["data"]] == ["Tunai"]


def test_sort_tidak_dikenal_400(db):
    assert client.get(f"{URL}?household_id={RT}&sort=pin:asc").status_code == 400


def test_tabel_transaksi_belum_ada_saldo_awal(db):
    db.tanpa_transaksi = True
    res = client.get(f"{URL}/d1")
    assert res.json()["data"]["current_balance"] == 1000000


def test_bukan_anggota_daftar_403(db):
    assert client.get(f"{URL}?household_id=rt-2").status_code == 403


def test_detail_rumah_tangga_lain_404(db):
    res = client.get(f"{URL}/d9")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


def test_anak_boleh_membaca(db):
    db.peran[RT] = "anak"
    assert client.get(f"{URL}/d1").status_code == 200


# ---------- tambah ----------
def test_tambah_valid_201(db):
    res = client.post(URL, json={"household_id": RT, "name": " GoPay ", "type": "ewallet", "provider": "GoPay",
                                 "opening_balance": 320000})
    assert res.status_code == 201
    assert res.json()["data"]["name"] == "GoPay"
    assert res.json()["data"]["current_balance"] == 320000


def test_tambah_nama_ganda_409(db):
    res = client.post(URL, json={"household_id": RT, "name": "BCA Utama", "type": "bank"})
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "CONFLICT"


@pytest.mark.parametrize("badan", [
    {"household_id": RT, "name": "X", "type": "kripto"},
    {"household_id": RT, "name": "", "type": "bank"},
    {"household_id": RT, "name": "X"},
    {"household_id": RT, "name": "X", "type": "bank", "opening_balance": 1000.5},
    {"household_id": RT, "name": "X", "type": "bank", "current_balance": 1},
    {"household_id": RT, "name": "X", "type": "bank", "nomor_rekening": "123"},
])
def test_tambah_tidak_valid_400(db, badan):
    res = client.post(URL, json=badan)
    assert res.status_code == 400
    assert res.json()["error"]["details"]


def test_tambah_oleh_anak_403(db):
    db.peran[RT] = "anak"
    assert client.post(URL, json={"household_id": RT, "name": "OVO", "type": "ewallet"}).status_code == 403
    assert db.ditulis == []


# ---------- ubah ----------
def test_ubah_sebagian(db):
    res = client.patch(f"{URL}/d1", json={"is_active": False})
    assert res.status_code == 200
    assert db.ditulis == [("patch", "accounts", {"is_active": False})]
    assert "current_balance" in res.json()["data"]


def test_ubah_body_kosong_400(db):
    assert client.patch(f"{URL}/d1", json={}).status_code == 400


def test_ubah_nama_jadi_null_400(db):
    assert client.patch(f"{URL}/d1", json={"name": None}).status_code == 400


def test_ubah_ganti_household_ditolak(db):
    assert client.patch(f"{URL}/d1", json={"household_id": "rt-2"}).status_code == 400


def test_ubah_nama_ke_nama_lain_409(db):
    assert client.patch(f"{URL}/d1", json={"name": "Tunai"}).status_code == 409


def test_ubah_nama_sendiri_boleh(db):
    assert client.patch(f"{URL}/d1", json={"name": "BCA Utama"}).status_code == 200


def test_ubah_oleh_anak_403(db):
    db.peran[RT] = "anak"
    assert client.patch(f"{URL}/d1", json={"name": "Baru"}).status_code == 403


# ---------- hapus ----------
def test_hapus_dompet_kosong_200(db):
    res = client.delete(f"{URL}/d2")
    assert res.status_code == 200
    assert res.json() == {"data": None, "message": "baris dihapus"}


def test_hapus_dipakai_transaksi_409(db):
    db.tabel["transactions"] = [{"account_id": "x", "to_account_id": "d2", "type": "transfer", "amount": 1}]
    assert client.delete(f"{URL}/d2").status_code == 409


def test_hapus_dipakai_setoran_tujuan_409(db):
    db.tabel["goal_contributions"] = [{"account_id": "d2"}]
    assert client.delete(f"{URL}/d2").status_code == 409


def test_hapus_oleh_anak_403(db):
    db.peran[RT] = "anak"
    assert client.delete(f"{URL}/d2").status_code == 403


def test_ibu_tidak_boleh_hapus_dompet_bersaldo(db):
    db.peran[RT] = "ibu"
    assert client.delete(f"{URL}/d1").status_code == 403
    assert client.delete(f"{URL}/d2").status_code == 200


def test_hapus_rumah_tangga_lain_404(db):
    assert client.delete(f"{URL}/d9").status_code == 404
