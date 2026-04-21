"""Flujo OAuth 2.0 authorization code para GitHub (async httpx)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import Settings
from app.services.exceptions import ConfigurationError, TokenExchangeError

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"

DEFAULT_SCOPES = ["read:user", "user:email"]


def _require_github_config(settings: Settings) -> None:
    if not settings.github_client_id or not settings.github_client_secret:
        raise ConfigurationError(
            "Faltan GITHUB_CLIENT_ID o GITHUB_CLIENT_SECRET en el entorno."
        )
    if not settings.github_redirect_uri:
        raise ConfigurationError("Falta GITHUB_REDIRECT_URI en el entorno.")


def build_authorization_url(settings: Settings, state: str) -> str:
    _require_github_config(settings)
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": " ".join(DEFAULT_SCOPES),
        "state": state,
    }
    return f"{GITHUB_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(
    settings: Settings,
    code: str,
    state: str,
    *,
    client: httpx.AsyncClient,
) -> dict[str, Any]:
    _require_github_config(settings)
    body = {
        "client_id": settings.github_client_id,
        "client_secret": settings.github_client_secret,
        "code": code,
        "redirect_uri": settings.github_redirect_uri,
        "state": state,
    }
    headers = {"Accept": "application/json"}
    try:
        response = await client.post(
            GITHUB_TOKEN_URL, data=body, headers=headers, timeout=30.0
        )
    except httpx.RequestError as exc:
        raise TokenExchangeError(f"Error de red al contactar GitHub: {exc}") from exc

    if response.status_code != 200:
        detail = response.text[:500] if response.text else response.reason_phrase
        raise TokenExchangeError(
            f"GitHub rechazó el intercambio de token (HTTP {response.status_code}): {detail}"
        )

    data = response.json()
    if data.get("error"):
        desc = data.get("error_description") or data.get("error")
        raise TokenExchangeError(f"GitHub devolvió error OAuth: {desc}")
    if "access_token" not in data:
        raise TokenExchangeError("Respuesta de GitHub sin access_token.")
    data.setdefault("token_type", "Bearer")
    return data
