# uji endpoint ringkasan dan laporan
import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_access_token, get_current_user
from app.main import app
from app.services import report_service as layanan

client = TestClient(app, raise_server_exceptions=False)

TRANSAKSI = [
    {"id": "t1", "type": "income", "amount": 5000000, "txn_date": "2026-09-05", "category_id": None,
     "member_id": "m1", "account_id": "a1", "merchant": "Gaji", "notes": None},
    {"id": "t2", "type": "expense", "amount": 1200000, "txn_date": "2026-09-06", "category_id": "c1",
     "member_id": "m2", "account_id": "a1", "merchant": "Pasar", "notes": "sayur dan lauk"},
    {"id": "t3", "type": "expense", "amount": 300000, "txn_date": "2026-09-07", "category_id": "c2",
     "member_id": "m1", "account_id": "a1", "merchant": "Angkutan", "notes": None},
]

ANGGOTA = [{"id": "m1", "display_name": "Ayah"}, {"id": "m2", "display_name": "Ibu"}]


def _palsu(peran: str):
    async def rest_select(table, params, token=None):
        if table == "transactions":
            return TRANSAKSI
        if table == "budgets":
            return [{"category_id": "c1", "limit_amount": 2000000}]
        if table == "goals":
            return [{"id": "g1"}]
        if table == "goal_contributions":
            return [{"amount": 500000}, {"amount": 250000}]
        if table == "categories":
            return [{"id": "c1", "name": "Makanan"}, {"id": "c2", "name": "Transportasi"}]
        if table == "household_members":
            if params.get("select") == "role,display_name":
                return [{"role": peran, "display_name": "Ayah"}] if peran != "bukan anggota" else []
            return ANGGOTA
        return []

    return rest_select


@pytest.fixture
def masuk():
    app.dependency_overrides[get_current_user] = lambda: {"sub": "11111111-1111-1111-1111-111111111111"}
    app.dependency_overrides[get_access_token] = lambda: "token-uji"
    yield
    app.dependency_overrides.clear()


def test_ringkasan_menghitung_semua_angka(monkeypatch, masuk):
    monkeypatch.setattr(layanan, "rest_select", _palsu("ayah"))
    res = client.get("/api/v1/dashboard/summary", params={"household_id": "h1", "bulan": "2026-09"})
    assert res.status_code == 200
    assert res.json()["data"] == {
        "bulan": "2026-09",
        "pemasukan": 5000000,
        "pengeluaran": 1500000,
        "selisih": 3500000,
        "batas_anggaran": 2000000,
        "anggaran_terpakai": 1200000,
        "anggaran_tersisa": 800000,
        "tabungan_terkumpul": 750000,
    }


def test_bulan_salah_format_ditolak(monkeypatch, masuk):
    monkeypatch.setattr(layanan, "rest_select", _palsu("ayah"))
    res = client.get("/api/v1/dashboard/summary", params={"household_id": "h1", "bulan": "2026-13"})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_arus_kas_menjumlah_per_bulan(monkeypatch, masuk):
    monkeypatch.setattr(layanan, "rest_select", _palsu("ayah"))
    res = client.get("/api/v1/reports/cashflow", params={"household_id": "h1", "from": "2026-09-01", "to": "2026-09-30"})
    assert res.status_code == 200
    assert res.json()["data"] == [
        {"bulan": "2026-09", "pemasukan": 5000000, "pengeluaran": 1500000, "selisih": 3500000}
    ]


def test_laporan_ditolak_untuk_anak(monkeypatch, masuk):
    monkeypatch.setattr(layanan, "rest_select", _palsu("anak"))
    res = client.get("/api/v1/reports/cashflow", params={"household_id": "h1"})
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_laporan_ditolak_untuk_bukan_anggota(monkeypatch, masuk):
    monkeypatch.setattr(layanan, "rest_select", _palsu("bukan anggota"))
    res = client.get("/api/v1/reports/categories", params={"household_id": "h1"})
    assert res.status_code == 403


def test_rekap_kategori_urut_dari_terbesar(monkeypatch, masuk):
    monkeypatch.setattr(layanan, "rest_select", _palsu("ayah"))
    res = client.get("/api/v1/reports/categories", params={"household_id": "h1"})
    assert res.status_code == 200
    assert res.json()["data"] == [
        {"category_id": "c1", "nama": "Makanan", "total": 1200000},
        {"category_id": "c2", "nama": "Transportasi", "total": 300000},
    ]


def test_rekap_anggota_urut_dari_terbesar(monkeypatch, masuk):
    monkeypatch.setattr(layanan, "rest_select", _palsu("ayah"))
    res = client.get("/api/v1/reports/members", params={"household_id": "h1"})
    assert res.status_code == 200
    assert res.json()["data"] == [
        {"member_id": "m2", "nama": "Ibu", "total": 1200000},
        {"member_id": "m1", "nama": "Ayah", "total": 300000},
    ]


def test_ekspor_csv_berisi_tajuk_dan_baris(monkeypatch, masuk):
    monkeypatch.setattr(layanan, "rest_select", _palsu("ayah"))
    res = client.get("/api/v1/reports/export.csv", params={"household_id": "h1"})
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "attachment" in res.headers["content-disposition"]
    baris = res.text.strip().split("\n")
    assert baris[0] == "tanggal,jenis,kategori,anggota,merchant,catatan,nominal"
    assert baris[1].startswith("2026-09-05,income,")
    assert "Makanan" in res.text and "Ibu" in res.text


def test_tanggal_salah_format_ditolak(monkeypatch, masuk):
    monkeypatch.setattr(layanan, "rest_select", _palsu("ayah"))
    res = client.get("/api/v1/reports/cashflow", params={"household_id": "h1", "from": "09-2026"})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"
