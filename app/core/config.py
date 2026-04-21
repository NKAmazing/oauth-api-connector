"""Carga de variables de entorno (python-dotenv) y configuración tipada."""

from functools import lru_cache
import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel


class Settings(BaseModel):
    """Configuración leída del entorno tras load_dotenv()."""

    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = ""
    frontend_success_url: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    fe = os.getenv("FRONTEND_SUCCESS_URL")
    return Settings(
        spotify_client_id=(os.getenv("SPOTIFY_CLIENT_ID") or "").strip(),
        spotify_client_secret=(os.getenv("SPOTIFY_CLIENT_SECRET") or "").strip(),
        spotify_redirect_uri=(os.getenv("REDIRECT_URI") or "").strip(),
        github_client_id=(os.getenv("GITHUB_CLIENT_ID") or "").strip(),
        github_client_secret=(os.getenv("GITHUB_CLIENT_SECRET") or "").strip(),
        github_redirect_uri=(os.getenv("GITHUB_REDIRECT_URI") or "").strip(),
        frontend_success_url=fe.strip() if fe else None,
    )
