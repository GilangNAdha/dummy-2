# titik masuk layanan
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import profiles, reports
from app.core.config import get_settings
from app.core.errors import register_error_handlers

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="API pencatatan keuangan keluarga. Seluruh aturan bisnis berada di layanan ini.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:8]
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.request_id
    return response


register_error_handlers(app)

app.include_router(profiles.router, prefix=settings.api_prefix)
app.include_router(reports.router, prefix=settings.api_prefix)


@app.get("/health", tags=["layanan"])
async def health() -> dict:
    return {"status": "ok", "layanan": settings.app_name, "versi": app.version}
