"""Orquestación del flujo OAuth por proveedor (lógica fuera de los routers)."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings
from app.services.exceptions import (
    InvalidSessionError,
    OAuthFlowError,
    UnsupportedProviderError,
)
from app.services.spotify_api import fetch_current_user_profile
from app.services.spotify_oauth import build_authorization_url, exchange_code_for_tokens
from app.services.token_store import StoredTokens, expires_at_from_ttl, token_store

SUPPORTED_PROVIDERS = frozenset({"spotify"})


def ensure_provider(provider: str) -> None:
    if provider not in SUPPORTED_PROVIDERS:
        raise UnsupportedProviderError(provider)


async def create_authorization_request(settings: Settings, provider: str) -> dict[str, str]:
    """Paso 1: URL de autorización + state persistido (anti-CSRF)."""
    ensure_provider(provider)
    state = token_store.new_state()
    await token_store.register_pending_state(state)
    if provider == "spotify":
        url = build_authorization_url(settings, state)
    else:
        raise UnsupportedProviderError(provider)
    return {"authorization_url": url, "state": state}


async def complete_authorization(
    settings: Settings,
    provider: str,
    code: str | None,
    state: str | None,
    error: str | None,
    *,
    client: httpx.AsyncClient,
) -> str:
    """Paso 2: valida state, intercambia code y devuelve session_id."""
    ensure_provider(provider)
    if error:
        raise OAuthFlowError(f"Spotify devolvió error OAuth: {error}")
    if not code or not state:
        raise OAuthFlowError("Faltan parámetros code o state en el callback.")
    if not await token_store.consume_state(state):
        raise OAuthFlowError("State inválido o ya utilizado (posible CSRF o doble callback).")

    if provider == "spotify":
        raw = await exchange_code_for_tokens(settings, code, client=client)
    else:
        raise UnsupportedProviderError(provider)

    expires_in = raw.get("expires_in")
    expires_at = expires_at_from_ttl(int(expires_in)) if expires_in is not None else None
    tokens = StoredTokens(
        access_token=raw["access_token"],
        refresh_token=raw.get("refresh_token"),
        expires_at=expires_at,
        token_type=raw.get("token_type") or "Bearer",
    )
    session_id = token_store.new_session_id()
    await token_store.save_session(session_id, tokens)
    return session_id


async def get_provider_user_data(
    provider: str,
    session_id: str,
    *,
    client: httpx.AsyncClient,
) -> dict[str, Any]:
    """Paso 3: datos del usuario usando el token almacenado."""
    ensure_provider(provider)
    tokens = await token_store.get_session(session_id)
    if tokens is None:
        raise InvalidSessionError()
    if provider == "spotify":
        return await fetch_current_user_profile(tokens, client=client)
    raise UnsupportedProviderError(provider)
