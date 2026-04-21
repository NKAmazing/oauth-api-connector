"""Llamadas a la Web API de Spotify con httpx async."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.services.exceptions import ExternalAPIError
from app.services.token_store import StoredTokens

SPOTIFY_API_BASE = "https://api.spotify.com/v1"


def _is_token_expired(tokens: StoredTokens) -> bool:
    if tokens.expires_at is None:
        return False
    # margen de 60s para evitar carreras con reloj
    return datetime.now(timezone.utc) >= (tokens.expires_at - timedelta(seconds=60))


async def fetch_current_user_profile(
    tokens: StoredTokens,
    *,
    client: httpx.AsyncClient,
) -> dict[str, Any]:
    """GET /me — requiere access_token válido."""
    if _is_token_expired(tokens):
        raise ExternalAPIError(
            "El access token expiró o está a punto de expirar. "
            "Implementa refresh token o repite el flujo OAuth.",
            status_code=401,
        )
    headers = {"Authorization": f"{tokens.token_type} {tokens.access_token}"}
    url = f"{SPOTIFY_API_BASE}/me"
    try:
        response = await client.get(url, headers=headers, timeout=30.0)
    except httpx.RequestError as exc:
        raise ExternalAPIError(f"Error de red al llamar a Spotify: {exc}") from exc

    if response.status_code == 401:
        raise ExternalAPIError("Token inválido o revocado (401).", status_code=401)
    if response.status_code == 403:
        raise ExternalAPIError("Spotify denegó el acceso (403). Revisa scopes.", status_code=403)
    if response.status_code != 200:
        detail = response.text[:500] if response.text else response.reason_phrase
        raise ExternalAPIError(
            f"Spotify API error HTTP {response.status_code}: {detail}",
            status_code=502,
        )
    return response.json()
