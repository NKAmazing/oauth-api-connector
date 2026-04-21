# OAuth API Connector

**FastAPI** backend for **OAuth 2.0** integration (authorization code flow) and external API connections. It currently supports **Spotify** and **GitHub**: user authorization, `code` exchange for tokens, and profile data retrieval.

## Requirements

- Python **3.11+** (3.12 recommended)
- OAuth app registered in [Spotify Dashboard](https://developer.spotify.com/dashboard)
- OAuth app registered in [GitHub Developers](https://github.com/settings/developers)

## Virtual Environment (.venv)

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Copy and edit the environment variables:

```bash
cp .env.example .env
```

Required variables for Spotify:

| Variable | Description |
|----------|-------------|
| `SPOTIFY_CLIENT_ID` | Spotify app Client ID |
| `SPOTIFY_CLIENT_SECRET` | Client Secret |
| `REDIRECT_URI` | Callback URL (e.g. `http://127.0.0.1:8000/callback/spotify`) |

Required variables for GitHub:

| Variable | Description |
|----------|-------------|
| `GITHUB_CLIENT_ID` | GitHub OAuth app Client ID |
| `GITHUB_CLIENT_SECRET` | Client Secret |
| `GITHUB_REDIRECT_URI` | Callback URL (e.g. `http://127.0.0.1:8000/callback/github`) |

Optional:

| Variable | Description |
|----------|-------------|
| `FRONTEND_SUCCESS_URL` | After OAuth, send HTTP 302 redirect to this URL with `?session_id=...` |

## Run the Server

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: `http://127.0.0.1:8000`
- OpenAPI (Swagger): `http://127.0.0.1:8000/docs`

## OAuth Flow (Multi-Provider)

1. `GET /auth/{provider}` -> JSON with `authorization_url` and `state`.
   - Supported providers: `spotify`, `github`.
2. Open `authorization_url` in the browser.
3. The provider redirects to `GET /callback/{provider}?code=...&state=...` (the URI must exactly match your `.env` value).
   - Spotify uses `REDIRECT_URI`.
   - GitHub uses `GITHUB_REDIRECT_URI`.
4. If `FRONTEND_SUCCESS_URL` is not set, the callback returns JSON with `session_id`. If it is set, the API responds with **302** to the frontend and appends `session_id` in query params.
5. `GET /data/{provider}?session_id=...` -> user profile data.
   - Spotify: `GET /data/spotify?session_id=...`
   - GitHub: `GET /data/github?session_id=...`

**Note:** token/session storage is currently **in-memory** (good for development). In production with multiple replicas or restarts, replace `TokenStore` with Redis or a database.

## Tech Stack

| Component | Usage |
|------------|-----|
| [FastAPI](https://fastapi.tiangolo.com/) | Async web framework, validation, and OpenAPI |
| [Uvicorn](https://www.uvicorn.org/) | ASGI server |
| [HTTPX](https://www.python-httpx.org/) | **Async** HTTP client for Spotify/GitHub (token + API calls) |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Load `.env` in development |
| [Pydantic](https://docs.pydantic.dev/) | Used by FastAPI for settings models |

## Architecture

```
app/
  main.py           # FastAPI app, lifespan (shared httpx client), exception handlers
  core/             # Configuration and environment variables
  routers/          # HTTP layer only: routes, Depends, responses
  services/         # OAuth logic, external API calls, token storage
```

- **routers**: receive requests, inject dependencies, and delegate to **services**.
- **services**: provider-specific business logic (authorization URL, code exchange, profile API calls, `state` validation, sessions).
- **core**: centralized configuration loading (`get_settings()`).

Domain errors (`OAuthConnectorError` and subclasses) are mapped to a consistent JSON format `{ "error", "message" }` with appropriate HTTP status codes (401 token/session, 400 OAuth flow, 502 provider/network failures, etc.).

## Repository Structure

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

## License

See the `LICENSE` file in this repository.
