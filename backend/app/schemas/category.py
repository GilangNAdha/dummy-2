# model Pydantic kategori
# Penulis: Gilang Nur Adha
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

JenisKategori = Literal["income", "expense"]
POLA_WARNA = r"^#[0-9A-Fa-f]{6}$"


class KategoriBaru(BaseModel):
    """Body POST /categories. is_system tidak bisa dikirim klien."""

    model_config = ConfigDict(extra="forbid")

    household_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=80)
    kind: JenisKategori
    icon: str | None = Field(default=None, max_length=8)
    color: str = Field(default="#94A3B8", pattern=POLA_WARNA)


class KategoriUbah(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=80)
    kind: JenisKategori | None = None
    icon: str | None = Field(default=None, max_length=8)
    color: str | None = Field(default=None, pattern=POLA_WARNA)
    is_archived: bool | None = None


class Kategori(BaseModel):
    id: str
    household_id: str | None = None
    name: str
    kind: JenisKategori
    icon: str | None = None
    color: str
    is_system: bool
    is_archived: bool
    created_at: str | None = None
    updated_at: str | None = None
