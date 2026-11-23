from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.releases import router as releases_router
from app.api.v1.downloads import router as downloads_router
from app.api.v1.admin import router as admin_router
from app.api.v1.showcase import router as showcase_router
from app.api.v1.features import router as features_router
from app.api.v1.config import router as config_router
from app.api.v1.faqs import router as faqs_router
from app.api.v1.websocket_sync import router as ws_router
from app.api.v1.security_center import router as security_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(auth_router)
api_router.include_router(releases_router)
api_router.include_router(downloads_router)
api_router.include_router(admin_router)
api_router.include_router(showcase_router)
api_router.include_router(features_router)
api_router.include_router(config_router)
api_router.include_router(faqs_router)
api_router.include_router(ws_router)
api_router.include_router(security_router)
