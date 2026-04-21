"""Llamadas a la API de GitHub con httpx async."""

from __future__ import annotations

from typing import Any

import httpx

from app.services.exceptions import ExternalAPIError
from app.services.token_store import StoredTokens

GITHUB_API_BASE = "https://api.github.com"


async def fetch_current_user_profile(
    tokens: StoredTokens,
    *,
    client: httpx.AsyncClient,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {tokens.access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"{GITHUB_API_BASE}/user"
    try:
        response = await client.get(url, headers=headers, timeout=30.0)
    except httpx.RequestError as exc:
        raise ExternalAPIError(f"Error de red al llamar a GitHub: {exc}") from exc

    if response.status_code == 401:
        raise ExternalAPIError("Token inválido o revocado en GitHub (401).", status_code=401)
    if response.status_code == 403:
        raise ExternalAPIError("GitHub denegó el acceso (403).", status_code=403)
    if response.status_code != 200:
        detail = response.text[:500] if response.text else response.reason_phrase
        raise ExternalAPIError(
            f"GitHub API error HTTP {response.status_code}: {detail}",
            status_code=502,
        )
    return response.json()
