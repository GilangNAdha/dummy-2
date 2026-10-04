# uji fungsi bantu paginasi
from app.core.pagination import PageParams, build_links, build_meta, list_response


def test_offset_dihitung_dari_halaman():
    assert PageParams(page=3, per_page=20).offset == 40


def test_meta_memuat_halaman_dan_total():
    meta = build_meta(PageParams(page=2, per_page=10), total=137)
    assert meta == {"page": 2, "per_page": 10, "total": 137}


def test_tautan_halaman_pertama():
    links = build_links("/api/v1/transactions", PageParams(page=1, per_page=20), total=137)
    assert links["prev"] is None
    assert links["next"].startswith("/api/v1/transactions?page=2")


def test_tautan_halaman_terakhir():
    links = build_links("/api/v1/transactions", PageParams(page=7, per_page=20), total=137)
    assert links["next"] is None
    assert links["prev"].startswith("/api/v1/transactions?page=6")


def test_tautan_mempertahankan_penyaring():
    links = build_links("/api/v1/transactions", PageParams(page=1, per_page=20), total=60,
                        extra={"household_id": "abc", "type": "expense"})
    assert "household_id=abc" in links["next"]
    assert "type=expense" in links["next"]


def test_respons_daftar_memuat_tiga_bagian():
    hasil = list_response([{"id": "1"}], PageParams(page=1, per_page=20), total=1, request_path="/api/v1/profiles")
    assert set(hasil.keys()) == {"data", "meta", "links"}
    assert hasil["meta"]["total"] == 1
