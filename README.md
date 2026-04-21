# OAuth Api Connector

Backend **FastAPI** listo para integrar **OAuth 2.0** (flujo *authorization code*) y consumir APIs externas. Actualmente soporta **Spotify** y **GitHub**: autorización, intercambio de `code` por tokens y lectura de perfil del usuario.

## Requisitos

- Python **3.11+** (recomendado 3.12)
- App OAuth registrada en [Spotify Dashboard](https://developer.spotify.com/dashboard)
- App OAuth registrada en [GitHub Developers](https://github.com/settings/developers)

## Entorno virtual (.venv)

Desde la raíz del repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Copia las variables de entorno y edítalas:

```bash
cp .env.example .env
```

Variables obligatorias para Spotify:

| Variable | Descripción |
|----------|-------------|
| `SPOTIFY_CLIENT_ID` | Client ID de la app Spotify |
| `SPOTIFY_CLIENT_SECRET` | Client Secret |
| `REDIRECT_URI` | URL de callback (ej. `http://127.0.0.1:8000/callback/spotify`) |

Variables obligatorias para GitHub:

| Variable | Descripción |
|----------|-------------|
| `GITHUB_CLIENT_ID` | Client ID de la app OAuth de GitHub |
| `GITHUB_CLIENT_SECRET` | Client Secret |
| `GITHUB_REDIRECT_URI` | URL de callback (ej. `http://127.0.0.1:8000/callback/github`) |

Opcional:

| Variable | Descripción |
|----------|-------------|
| `FRONTEND_SUCCESS_URL` | Tras OAuth, redirección HTTP 302 a esta URL con `?session_id=...` |

## Ejecutar el servidor

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: `http://127.0.0.1:8000`
- OpenAPI (Swagger): `http://127.0.0.1:8000/docs`

## Flujo OAuth (multi-provider)

1. `GET /auth/{provider}` → JSON con `authorization_url` y `state`.
   - Providers soportados: `spotify`, `github`.
2. Abre `authorization_url` en el navegador.
3. El proveedor redirige a `GET /callback/{provider}?code=...&state=...` (la URI debe coincidir exactamente con tu `.env`).
   - Spotify usa `REDIRECT_URI`.
   - GitHub usa `GITHUB_REDIRECT_URI`.
3. Si `FRONTEND_SUCCESS_URL` no está definido, la respuesta es JSON con `session_id`. Si está definido, recibes un **302** al front con `session_id` en query.
4. `GET /data/{provider}?session_id=...` → perfil del usuario.
   - Spotify: `GET /data/spotify?session_id=...`
   - GitHub: `GET /data/github?session_id=...`

**Nota:** el almacenamiento de tokens es **en memoria** en esta versión (adecuado para desarrollo). En producción con varias réplicas o reinicios, sustituye `TokenStore` por Redis o base de datos.

## Tech stack

| Componente | Uso |
|------------|-----|
| [FastAPI](https://fastapi.tiangolo.com/) | Framework web async, validación y OpenAPI |
| [Uvicorn](https://www.uvicorn.org/) | Servidor ASGI |
| [HTTPX](https://www.python-httpx.org/) | Cliente HTTP **async** hacia Spotify/GitHub (token + API) |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Carga de `.env` en desarrollo |
| [Pydantic](https://docs.pydantic.dev/) | Incluido con FastAPI para modelos de configuración |

## Arquitectura

```
app/
  main.py           # App FastAPI, lifespan (cliente httpx), exception handlers
  core/             # Configuración y variables de entorno
  routers/          # Solo HTTP: rutas, Depends, respuestas
  services/         # OAuth, llamadas a APIs externas, almacenamiento de tokens
```

- **routers**: reciben peticiones, inyectan dependencias y delegan en **services**.
- **services**: reglas de negocio por proveedor (construcción de URL de autorización, intercambio de código, llamadas API de perfil, validación de `state`, sesiones).
- **core**: lectura centralizada de configuración (`get_settings()`).

Errores de dominio (`OAuthConnectorError` y subclases) se convierten en JSON uniforme `{ "error", "message" }` con el código HTTP adecuado (401 token/sesión, 400 flujo OAuth, 502 errores de red o respuesta del proveedor, etc.).

## Estructura del repositorio

```
oauth-api-connector/
├── app/
│   ├── main.py
│   ├── core/
│   │   └── config.py
│   ├── routers/
│   │   ├── health.py
│   │   └── oauth.py
│   └── services/
│       ├── exceptions.py
│       ├── github_api.py
│       ├── github_oauth.py
│       ├── token_store.py
│       ├── oauth_flow.py
│       ├── spotify_oauth.py
│       └── spotify_api.py
├── requirements.txt
├── .env.example
└── README.md
```

## Licencia

Ver el archivo `LICENSE` del repositorio.
