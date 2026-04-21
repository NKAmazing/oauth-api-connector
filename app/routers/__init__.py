from app.routers.health import router as health_router
from app.routers.oauth import router as oauth_router

__all__ = ["health_router", "oauth_router"]
