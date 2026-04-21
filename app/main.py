"""Punto de entrada FastAPI: lifespan (httpx), routers y manejo global de errores."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers import health_router, oauth_router
from app.services.exceptions import OAuthConnectorError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Cliente HTTP async compartido (connection pooling)
    async with httpx.AsyncClient() as client:
        app.state.http_client = client
        yield


app = FastAPI(
    title="oauth-api-connector",
    description="Integración OAuth 2.0 y conexión a APIs externas (Spotify inicial).",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(oauth_router)


@app.exception_handler(OAuthConnectorError)
async def oauth_connector_handler(
    _request: Request, exc: OAuthConnectorError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "message": exc.message},
    )
