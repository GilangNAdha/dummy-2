# tiruan PostgREST sederhana untuk uji dompet dan kategori
# Penulis: Gilang Nur Adha
import pytest

from app.core.deps import get_access_token, get_current_user
from app.core.errors import AppError
from app.main import app
from app.repositories import accounts as repo_akun
from app.repositories import anggota as repo_anggota
from app.repositories import categories as repo_kategori

RT, RT_LAIN = "rt-1", "rt-2"


def _cocok(baris: dict, kunci: str, nilai: str) -> bool:
    if kunci in ("select", "order", "limit", "offset"):
        return True
    if kunci == "or":
        isi = nilai.strip("()")
        if "household_id.is.null" in isi:
            rt = isi.split("household_id.eq.")[1]
            return baris.get("household_id") in (None, rt)
        # (account_id.in.(a,b),to_account_id.in.(a,b)) atau (account_id.eq.x,to_account_id.eq.x)
        if ".in.(" in isi:
            ids = isi.split(".in.(")[1].split(")")[0].split(",")
            return baris.get("account_id") in ids or baris.get("to_account_id") in ids
        x = isi.split("account_id.eq.")[1].split(",")[0]
        return x in (baris.get("account_id"), baris.get("to_account_id"))
    op, _, v = nilai.partition(".")
    nyata = baris.get(kunci)
    if op == "eq":
        return str(nyata).lower() == v.lower() if isinstance(nyata, bool) else str(nyata) == v
    if op == "neq":
        return str(nyata) != v
    if op == "is":
        return nyata is None
    raise AssertionError(f"operator tidak dikenal {nilai}")


class Palsu:
    def __init__(self):
        self.peran = {RT: "ayah"}
        self.tabel = {
            "accounts": [
                {"id": "d1", "household_id": RT, "name": "BCA Utama", "type": "bank", "provider": "BCA",
                 "opening_balance": 1000000, "is_active": True},
                {"id": "d2", "household_id": RT, "name": "Tunai", "type": "cash", "provider": None,
                 "opening_balance": 0, "is_active": True},
                {"id": "d9", "household_id": RT_LAIN, "name": "Milik Lain", "type": "bank", "provider": None,
                 "opening_balance": 5, "is_active": True},
            ],
            "categories": [
                {"id": "k1", "household_id": None, "name": "Transportasi", "kind": "expense", "color": "#3B82F6",
                 "is_system": True, "is_archived": False},
                {"id": "k2", "household_id": RT, "name": "Arisan", "kind": "expense", "color": "#94A3B8",
                 "is_system": False, "is_archived": False},
                {"id": "k9", "household_id": RT_LAIN, "name": "Rahasia", "kind": "expense", "color": "#94A3B8",
                 "is_system": False, "is_archived": False},
            ],
            "transactions": [],
            "goal_contributions": [],
        }
        self.tanpa_transaksi = False  # tiru migrasi 0006 belum dipasang
        self.ditulis = []
        self.params_terakhir = {}

    def _cek_tabel(self, table):
        if self.tanpa_transaksi and table in ("transactions", "goal_contributions"):
            raise AppError(502, "SUPABASE_ERROR", "x", [{"status": 404}])

    async def select(self, table, params, token):
        assert token == "token-uji"
        if table == "household_members":
            rt = params["household_id"].removeprefix("eq.")
            return [{"role": self.peran[rt]}] if self.peran.get(rt) else []
        self._cek_tabel(table)
        self.params_terakhir[table] = params
        hasil = [b for b in self.tabel[table] if all(_cocok(b, k, v) for k, v in params.items())]
        off = int(params.get("offset", 0))
        return hasil[off: off + int(params.get("limit", 1000))]

    async def hitung(self, table, params, token):
        self._cek_tabel(table)
        return len([b for b in self.tabel[table] if all(_cocok(b, k, v) for k, v in params.items())])

    async def insert(self, table, payload, token):
        self.ditulis.append(("insert", table, payload))
        return [{"id": "baru", **payload}]

    async def patch(self, table, params, payload, token):
        self.ditulis.append(("patch", table, payload))
        asli = next(b for b in self.tabel[table] if b["id"] == params["id"].removeprefix("eq."))
        return [{**asli, **payload}]

    async def delete(self, table, params, token):
        self.ditulis.append(("delete", table, params))
        return []


@pytest.fixture
def db(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: {"sub": "u1"}
    app.dependency_overrides[get_access_token] = lambda: "token-uji"
    p = Palsu()
    monkeypatch.setattr(repo_anggota, "rest_select", p.select)
    for modul in (repo_akun, repo_kategori):
        monkeypatch.setattr(modul, "rest_select", p.select)
        monkeypatch.setattr(modul, "rest_hitung", p.hitung)
        monkeypatch.setattr(modul, "rest_insert", p.insert)
        monkeypatch.setattr(modul, "rest_patch", p.patch)
        monkeypatch.setattr(modul, "rest_delete", p.delete)
    yield p
    app.dependency_overrides.clear()
