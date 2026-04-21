"""Flujo OAuth 2.0 authorization code para Spotify (async httpx)."""

from __future__ import annotations

import base64
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import Settings
from app.services.exceptions import ConfigurationError, TokenExchangeError

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"

# Scopes mínimos para leer el perfil público / email en /v1/me
DEFAULT_SCOPES = ["user-read-email", "user-read-private"]


def _require_spotify_config(settings: Settings) -> None:
    if not settings.spotify_client_id or not settings.spotify_client_secret:
        raise ConfigurationError(
            "Faltan SPOTIFY_CLIENT_ID o SPOTIFY_CLIENT_SECRET en el entorno."
        )
    if not settings.redirect_uri:
        raise ConfigurationError("Falta REDIRECT_URI en el entorno.")


def build_authorization_url(settings: Settings, state: str) -> str:
    """Construye la URL de autorización (paso 1 del flujo OAuth)."""
    _require_spotify_config(settings)
    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.redirect_uri,
        "scope": " ".join(DEFAULT_SCOPES),
        "state": state,
        "show_dialog": "false",
    }
    return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"


def _basic_auth_header(client_id: str, client_secret: str) -> str:
    raw = f"{client_id}:{client_secret}".encode()
    return "Basic " + base64.b64encode(raw).decode()


async def exchange_code_for_tokens(
    settings: Settings,
    code: str,
    *,
    client: httpx.AsyncClient,
) -> dict[str, Any]:
    """Intercambia el authorization code por tokens (paso 2)."""
    _require_spotify_config(settings)
    headers = {
        "Authorization": _basic_auth_header(
            settings.spotify_client_id, settings.spotify_client_secret
        ),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    body = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.redirect_uri,
    }
    try:
        response = await client.post(
            SPOTIFY_TOKEN_URL, headers=headers, data=body, timeout=30.0
        )
    except httpx.RequestError as exc:
        raise TokenExchangeError(f"Error de red al contactar Spotify: {exc}") from exc

    if response.status_code != 200:
        detail = response.text[:500] if response.text else response.reason_phrase
        raise TokenExchangeError(
            f"Spotify rechazó el intercambio de token (HTTP {response.status_code}): {detail}"
        )

    data = response.json()
    if "access_token" not in data:
        raise TokenExchangeError("Respuesta de Spotify sin access_token.")
    return data
