# model Pydantic dompet
# Penulis: Gilang Nur Adha
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt

JenisDompet = Literal["bank", "cash", "ewallet"]


class DompetBaru(BaseModel):
    """Body POST /accounts. id, created_at, updated_at, current_balance tidak boleh dikirim."""

    model_config = ConfigDict(extra="forbid")

    household_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=80)
    type: JenisDompet
    provider: str | None = Field(default=None, max_length=60)
    opening_balance: StrictInt = 0


class DompetUbah(BaseModel):
    """Body PATCH /accounts/{id}. household_id tidak boleh diganti."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=80)
    type: JenisDompet | None = None
    provider: str | None = Field(default=None, max_length=60)
    opening_balance: StrictInt | None = None
    is_active: bool | None = None


class Dompet(BaseModel):
    """Bentuk keluaran, termasuk kolom turunan current_balance."""

    id: str
    household_id: str
    name: str
    type: JenisDompet
    provider: str | None = None
    opening_balance: int
    is_active: bool
    current_balance: int
    created_at: str | None = None
    updated_at: str | None = None
