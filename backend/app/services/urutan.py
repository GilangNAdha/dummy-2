# terjemahan parameter sort=kolom:arah ke sintaks order PostgREST
# Penulis: Gilang Nur Adha
from app.core.errors import AppError


def ke_order(sort: str | None, kolom_boleh: set[str], bawaan: str) -> str:
    if not sort:
        return bawaan
    kolom, _, arah = sort.partition(":")
    arah = arah or "asc"
    if kolom not in kolom_boleh or arah not in ("asc", "desc"):
        raise AppError(
            400, "VALIDATION_ERROR", "Parameter sort tidak dikenal.",
            [{"field": "sort", "issue": f"pakai kolom:asc|desc, kolom: {', '.join(sorted(kolom_boleh))}"}],
        )
    return f"{kolom}.{arah}"
