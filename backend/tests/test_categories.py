# uji router /categories
# Penulis: Gilang Nur Adha
import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.palsu_supabase import RT, db  # noqa: F401

client = TestClient(app, raise_server_exceptions=False)
URL = "/api/v1/categories"


def test_tanpa_token_401():
    assert client.get(f"{URL}?household_id={RT}").status_code == 401


def test_daftar_sistem_dan_milik_sendiri(db):
    res = client.get(f"{URL}?household_id={RT}&sort=name:asc")
    assert res.status_code == 200
    assert {k["id"] for k in res.json()["data"]} == {"k1", "k2"}  # k9 milik rumah tangga lain tidak ikut
    assert db.params_terakhir["categories"]["order"] == "name.asc"
    assert res.json()["meta"]["total"] == 2


def test_daftar_saring_kind(db):
    res = client.get(f"{URL}?household_id={RT}&kind=income")
    assert res.json()["data"] == []


def test_anak_boleh_membaca(db):
    db.peran[RT] = "anak"
    assert client.get(f"{URL}?household_id={RT}").status_code == 200


def test_detail_kategori_sistem(db):
    assert client.get(f"{URL}/k1").json()["data"]["is_system"] is True


def test_detail_rumah_tangga_lain_404(db):
    assert client.get(f"{URL}/k9").status_code == 404


def test_tambah_valid_is_system_false(db):
    res = client.post(URL, json={"household_id": RT, "name": "Les Musik", "kind": "expense", "color": "#123ABC"})
    assert res.status_code == 201
    assert res.json()["data"]["is_system"] is False


def test_tambah_nama_ganda_409(db):
    assert client.post(URL, json={"household_id": RT, "name": "Arisan", "kind": "expense"}).status_code == 409


def test_tambah_sama_dengan_sistem_jenis_sama_409(db):
    assert client.post(URL, json={"household_id": RT, "name": "Transportasi", "kind": "expense"}).status_code == 409


@pytest.mark.parametrize("badan", [
    {"household_id": RT, "name": "A", "kind": "hutang"},
    {"household_id": RT, "name": "A", "kind": "expense", "color": "merah"},
    {"household_id": RT, "name": "A", "kind": "expense", "is_system": True},
])
def test_tambah_tidak_valid_400(db, badan):
    assert client.post(URL, json=badan).status_code == 400


def test_tambah_oleh_anak_403(db):
    db.peran[RT] = "anak"
    assert client.post(URL, json={"household_id": RT, "name": "A", "kind": "expense"}).status_code == 403


@pytest.mark.parametrize("aksi", ["patch", "delete"])
def test_kategori_sistem_ditolak_403(db, aksi):
    res = client.patch(f"{URL}/k1", json={"name": "X"}) if aksi == "patch" else client.delete(f"{URL}/k1")
    assert res.status_code == 403
    assert db.ditulis == []


@pytest.mark.parametrize("aksi", ["patch", "delete"])
def test_anak_tidak_boleh_ubah_hapus(db, aksi):
    db.peran[RT] = "anak"
    res = client.patch(f"{URL}/k2", json={"name": "X"}) if aksi == "patch" else client.delete(f"{URL}/k2")
    assert res.status_code == 403


def test_ubah_sebagian(db):
    res = client.patch(f"{URL}/k2", json={"is_archived": True})
    assert res.status_code == 200 and res.json()["data"]["is_archived"] is True


def test_ubah_body_kosong_400(db):
    assert client.patch(f"{URL}/k2", json={}).status_code == 400


def test_ubah_kind_saat_dipakai_transaksi_409(db):
    db.tabel["transactions"] = [{"category_id": "k2"}]
    assert client.patch(f"{URL}/k2", json={"kind": "income"}).status_code == 409


def test_hapus_kategori_kosong_200(db):
    res = client.delete(f"{URL}/k2")
    assert res.status_code == 200
    assert res.json()["message"] == "baris dihapus"


def test_hapus_dipakai_transaksi_409(db):
    db.tabel["transactions"] = [{"category_id": "k2"}]
    assert client.delete(f"{URL}/k2").status_code == 409
