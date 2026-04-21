"""Endpoints de comprobación de servicio."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/", summary="Health check")
async def root() -> dict[str, str]:
    return {"status": "ok"}
