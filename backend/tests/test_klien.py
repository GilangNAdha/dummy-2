# uji penolong klien Supabase
import json

import pytest

from app.core.errors import AppError
from app.core.supabase_client import _cek, _jumlah_dari_range


class JawabanPalsu:
    def __init__(self, status_code=200, isi=b"[]", headers=None):
        self.status_code = status_code
        self.content = isi
        self.headers = headers or {}

    def json(self):
        return json.loads(self.content)


def test_jawaban_penolakan_izin_menjadi_403():
    with pytest.raises(AppError) as galat:
        _cek(JawabanPalsu(status_code=403, isi=b'{"message":"new row violates row-level security policy"}'))
    assert galat.value.status_code == 403
    assert galat.value.code == "FORBIDDEN"


def test_jawaban_galat_lain_menjadi_502():
    with pytest.raises(AppError) as galat:
        _cek(JawabanPalsu(status_code=500, isi=b"{}"))
    assert galat.value.status_code == 502
    assert galat.value.code == "SUPABASE_ERROR"


def test_isi_kosong_dibaca_sebagai_daftar_kosong():
    assert _cek(JawabanPalsu(status_code=204, isi=b"")) == []


def test_jumlah_dibaca_dari_header_content_range():
    assert _jumlah_dari_range(JawabanPalsu(headers={"content-range": "0-19/137"})) == 137
    assert _jumlah_dari_range(JawabanPalsu(headers={"content-range": "*/0"})) == 0
    assert _jumlah_dari_range(JawabanPalsu()) == 0
