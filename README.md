# OAuth Api Connector

Backend **FastAPI** listo para integrar **OAuth 2.0** (flujo *authorization code*) y consumir APIs externas. El primer proveedor implementado es **Spotify**: autorización, intercambio de `code` por tokens y lectura del perfil (`/v1/me`).

## Requisitos

- Python **3.11+** (recomendado 3.12)
- Cuenta de desarrollador en [Spotify Dashboard](https://developer.spotify.com/dashboard) con una app y **Redirect URI** registrada (debe coincidir exactamente con `REDIRECT_URI` en tu `.env`)

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

## Flujo OAuth (Spotify)

1. `GET /auth/spotify` → JSON con `authorization_url` y `state`. Abre la URL en el navegador e inicia sesión en Spotify.
2. Spotify redirige a `GET /callback/spotify?code=...&state=...` (tu `REDIRECT_URI` debe ser la base de esta ruta).
3. Si `FRONTEND_SUCCESS_URL` no está definido, la respuesta es JSON con `session_id`. Si está definido, recibes un **302** al front con `session_id` en query.
4. `GET /data/spotify?session_id=...` → perfil del usuario (JSON de la Web API).

**Nota:** el almacenamiento de tokens es **en memoria** en esta versión (adecuado para desarrollo). En producción con varias réplicas o reinicios, sustituye `TokenStore` por Redis o base de datos.

## Tech stack

| Componente | Uso |
|------------|-----|
| [FastAPI](https://fastapi.tiangolo.com/) | Framework web async, validación y OpenAPI |
| [Uvicorn](https://www.uvicorn.org/) | Servidor ASGI |
| [HTTPX](https://www.python-httpx.org/) | Cliente HTTP **async** hacia Spotify (token + API) |
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
- **services**: reglas de negocio (construcción de URL de autorización, intercambio de código, llamada a `/me`, validación de `state`, sesiones).
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
