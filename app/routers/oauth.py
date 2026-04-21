"""Rutas HTTP del flujo OAuth (delegan en services)."""

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.config import Settings, get_settings
from app.services.oauth_flow import (
    complete_authorization,
    create_authorization_request,
    get_provider_user_data,
)

router = APIRouter(tags=["oauth"])


async def get_http_client(request: Request) -> httpx.AsyncClient:
    """Cliente httpx reutilizado por request (lifespan)."""
    return request.app.state.http_client


@router.get("/auth/{provider}", summary="Iniciar OAuth (URL de autorización)")
async def auth_start(
    provider: str,
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    return await create_authorization_request(settings, provider)


@router.get("/callback/{provider}", summary="Callback OAuth (code → token)")
async def auth_callback(
    provider: str,
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    settings: Settings = Depends(get_settings),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    session_id = await complete_authorization(
        settings, provider, code, state, error, client=client
    )
    # Si hay URL de front, redirige con session_id para flujo navegador
    if settings.frontend_success_url:
        base = settings.frontend_success_url.rstrip("/")
        return RedirectResponse(url=f"{base}?session_id={session_id}", status_code=302)
    return JSONResponse(
        {
            "status": "authorized",
            "provider": provider,
            "session_id": session_id,
            "hint": "Usa GET /data/{provider}?session_id=... con este session_id.",
        }
    )


@router.get("/data/{provider}", summary="Datos del usuario (API del proveedor)")
async def user_data(
    provider: str,
    session_id: str = Query(..., description="session_id devuelto por /callback"),
    client: httpx.AsyncClient = Depends(get_http_client),
) -> dict:
    return await get_provider_user_data(provider, session_id, client=client)
