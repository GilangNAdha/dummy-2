# fungsi bantu paginasi
from dataclasses import dataclass
from urllib.parse import urlencode

from fastapi import Query

from app.core.config import get_settings


@dataclass
class PageParams:
    page: int
    per_page: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


def page_params(
    page: int = Query(1, ge=1),
    per_page: int | None = Query(None, ge=1),
) -> PageParams:
    settings = get_settings()
    size = per_page or settings.page_size_default
    if size > settings.page_size_max:
        size = settings.page_size_max
    return PageParams(page=page, per_page=size)


def build_meta(params: PageParams, total: int) -> dict:
    return {"page": params.page, "per_page": params.per_page, "total": total}


def build_links(request_path: str, params: PageParams, total: int, extra: dict | None = None) -> dict:
    halaman_akhir = max(1, -(-total // params.per_page))

    def tautan(target: int) -> str:
        query = dict(extra or {})
        query["page"] = target
        query["per_page"] = params.per_page
        return f"{request_path}?{urlencode(query)}"

    return {
        "next": tautan(params.page + 1) if params.page < halaman_akhir else None,
        "prev": tautan(params.page - 1) if params.page > 1 else None,
    }


def list_response(items: list, params: PageParams, total: int, request_path: str, extra: dict | None = None) -> dict:
    return {
        "data": items,
        "meta": build_meta(params, total),
        "links": build_links(request_path, params, total, extra),
    }
