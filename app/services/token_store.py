"""Almacenamiento en memoria de tokens por sesión (sustituir por Redis/DB en producción)."""

from __future__ import annotations

import asyncio
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass
class StoredTokens:
    provider: str
    access_token: str
    refresh_token: Optional[str]
    expires_at: Optional[datetime]
    token_type: str = "Bearer"


class TokenStore:
    """Store mínimo async-safe para demos; en producción usar almacenamiento persistente."""

    def __init__(self) -> None:
        self._pending_state: dict[str, bool] = {}
        self._sessions: dict[str, StoredTokens] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def new_state() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def new_session_id() -> str:
        return secrets.token_urlsafe(32)

    async def register_pending_state(self, state: str) -> None:
        async with self._lock:
            self._pending_state[state] = True

    async def consume_state(self, state: str) -> bool:
        async with self._lock:
            return self._pending_state.pop(state, False)

    async def save_session(self, session_id: str, tokens: StoredTokens) -> None:
        async with self._lock:
            self._sessions[session_id] = tokens

    async def get_session(self, session_id: str) -> Optional[StoredTokens]:
        async with self._lock:
            return self._sessions.get(session_id)

    async def delete_session(self, session_id: str) -> None:
        async with self._lock:
            self._sessions.pop(session_id, None)


def expires_at_from_ttl(seconds: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)


# Instancia compartida de la app (inyectable en tests)
token_store = TokenStore()
