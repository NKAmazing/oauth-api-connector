"""Rutas HTTP del flujo OAuth (delegan en services)."""

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Path, Query, Request
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


@router.get(
    "/auth/{provider}",
    summary="Iniciar OAuth (URL de autorización)",
    description=(
        "Genera la URL de autorización OAuth para el proveedor indicado. "
        "Providers soportados: `spotify`, `github`."
    ),
)
async def auth_start(
    provider: str = Path(..., description="Proveedor OAuth (`spotify` o `github`)."),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    return await create_authorization_request(settings, provider)


@router.get(
    "/callback/{provider}",
    summary="Callback OAuth (code → token)",
    description=(
        "Endpoint de redirección del proveedor OAuth. Recibe `code` y `state`, "
        "canjea el token y devuelve `session_id`."
    ),
)
async def auth_callback(
    request: Request,
    provider: str = Path(..., description="Proveedor OAuth (`spotify` o `github`)."),
    code: Optional[str] = Query(None, description="Authorization code devuelto por el proveedor."),
    state: Optional[str] = Query(None, description="State OAuth para validación anti-CSRF."),
    error: Optional[str] = Query(None, description="Error OAuth devuelto por el proveedor."),
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


@router.get(
    "/data/{provider}",
    summary="Datos del usuario (API del proveedor)",
    description=(
        "Obtiene datos del usuario autenticado usando el `session_id` "
        "emitido por `/callback/{provider}`."
    ),
)
async def user_data(
    provider: str = Path(..., description="Proveedor OAuth (`spotify` o `github`)."),
    session_id: str = Query(..., description="session_id devuelto por `/callback/{provider}`."),
    client: httpx.AsyncClient = Depends(get_http_client),
) -> dict:
    return await get_provider_user_data(provider, session_id, client=client)
