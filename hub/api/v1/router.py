from fastapi import APIRouter
from hub.api.v1.endpoints import portfolio

router = APIRouter()
router.include_router(portfolio.router, tags=["portfolio"])

