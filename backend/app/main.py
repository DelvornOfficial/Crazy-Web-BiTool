import os
import time
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func

from app.core.config import settings
from app.core.database import init_db, async_session
from app.core.security import hash_password
from app.models import Admin, AppRelease, ShowcaseVideo, AppFeature, SiteSetting
from app.api.v1 import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("nextlevelcheat.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Event Handler:
    1. Initializes database connection and schemas.
    2. Auto-seeds default superadmin credentials if database is fresh.
    3. Auto-seeds latest release metadata.
    4. Auto-seeds initial showcase videos playlist.
    5. Auto-seeds default dynamic features with short descriptions.
    6. Auto-seeds site settings (Telegram link).
    """
    logger.info("Initializing Next Level Cheat API...")
    await init_db()

    # Database auto-seed routine
    try:
        async with async_session() as session:
            # 1. Seed or Sync Superadmin directly from .env Hash
            from app.core.config import get_live_env_admin_credentials
            env_user, env_hash = get_live_env_admin_credentials()

            # Ensure hash format
            if not env_hash.startswith("$2b$") and not env_hash.startswith("$2a$"):
                env_hash = hash_password(env_hash)

            admin_stmt = select(Admin).where(Admin.username == env_user)
            admin_res = await session.execute(admin_stmt)
            existing_admin = admin_res.scalar_one_or_none()

            if not existing_admin:
                # Sync existing single admin or create fresh
                first_admin = (await session.execute(select(Admin).limit(1))).scalar_one_or_none()
                if first_admin:
                    first_admin.username = env_user
                    first_admin.hashed_password = env_hash
                    first_admin.failed_login_attempts = 0
                    first_admin.locked_until = None
                    first_admin.is_active = True
                    await session.commit()
                    logger.info(f"Existing admin converted & synced with .env: '{env_user}'")
                else:
                    initial_admin = Admin(
                        username=env_user,
                        hashed_password=env_hash,
                        role="superadmin",
                        is_active=True,
                    )
                    session.add(initial_admin)
                    await session.commit()
                    logger.info(f"Superadmin created from .env: '{env_user}'")
            else:
                existing_admin.hashed_password = env_hash
                existing_admin.failed_login_attempts = 0
                existing_admin.locked_until = None
                existing_admin.is_active = True
                await session.commit()
                logger.info(f"Superadmin '{env_user}' password hash synced strictly from .env.")

            # Superadmin synced strictly from .env
            pass
            logger.info("Startup database verification complete.")

    except Exception as e:
        logger.error(f"Error during startup data seeding: {e}", exc_info=True)

    # Startup: Load Telegram Watchdog credentials from database
    try:
        async with async_session() as session:
            tok_rec = (await session.execute(select(SiteSetting).where(SiteSetting.key == "tg_bot_token"))).scalar_one_or_none()
            chat_rec = (await session.execute(select(SiteSetting).where(SiteSetting.key == "tg_owner_chat_id"))).scalar_one_or_none()
            if tok_rec and chat_rec and tok_rec.value and chat_rec.value:
                from app.core.telegram_bot import telegram_security_bot
                await telegram_security_bot.init_credentials(tok_rec.value, chat_rec.value)
                logger.info("Telegram Security Watchdog credentials initialized.")
    except Exception as e:
        logger.warning(f"Could not load Telegram credentials on startup: {e}")

    # Launch Background Weekly Automated Backup Task (every 7 days)
    async def weekly_backup_worker():
        while True:
            await asyncio.sleep(60 * 60 * 24 * 7)  # 7 Days interval
            try:
                from app.core.telegram_bot import telegram_security_bot
                from app.core.backup_manager import create_full_system_backup_archive
                if telegram_security_bot.bot_token and telegram_security_bot.owner_chat_id:
                    zip_path, zip_name, zip_size = await create_full_system_backup_archive()
                    zip_size_mb = round(zip_size / (1024 * 1024), 2)
                    caption = (
                        f"🗓️ <b>AUTOMATED WEEKLY FULL VPS BACKUP</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"• <b>Archive:</b> <code>{zip_name}</code> ({zip_size_mb} MB)\n"
                        f"• <b>PostgreSQL SQL Dump:</b> ✅ Complete\n"
                        f"• <b>Media Uploads (APKs/Videos):</b> ✅ Included\n"
                        f"• <b>Disaster Recovery Guide:</b> ✅ RESTORE_GUIDE.md\n"
                        f"━━━━━━━━━━━━━━━━━━"
                    )
                    await telegram_security_bot.send_database_backup(zip_path, caption=caption)
            except Exception as ex:
                logger.error(f"Weekly backup worker error: {ex}")

    backup_task = asyncio.create_task(weekly_backup_worker())

    yield

    backup_task.cancel()
    logger.info("Shutting down Next Level Cheat API...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="High-Security, Anti-SQL Injection Backend API for Next Level Cheat",
    version="2.4.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


from app.core.rate_limiter import limiter
from app.api.deps import get_client_ip
from fastapi.responses import JSONResponse

# Global Anti-DDoS & L7 Flood Mitigation Middleware
@app.middleware("http")
async def ddos_protection_middleware(request: Request, call_next):
    # Only inspect API and Admin routes (static files handled fast)
    path = request.url.path
    if path.startswith("/api") or path.startswith("/admin"):
        client_ip = get_client_ip(request)
        is_blocked, retry_after, reason = limiter.check_general_rate_limit(client_ip)
        if is_blocked:
            # Trigger instant clear-text alert to Telegram Owner
            from app.core.telegram_bot import telegram_security_bot
            import asyncio
            asyncio.create_task(
                telegram_security_bot.send_security_alert(
                    title="DDoS Attack / Flood Blocked",
                    details=f"🚨 <b>L7 Rate-Limit Triggered!</b>\n"
                            f"• Reason: <code>{reason}</code>\n"
                            f"• Block Duration: <b>{retry_after}s</b>\n"
                            f"• Targeted Path: <code>{path}</code>",
                    severity="CRITICAL",
                    ip_address=client_ip
                )
            )

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": reason,
                    "retry_after_seconds": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Action": "BLOCK",
                    "X-DDoS-Shield": "ACTIVE"
                }
            )

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-DDoS-Shield"] = "ONLINE"
    return response


# Include API Endpoints
app.include_router(api_router, prefix="/api")


# Static Assets for High-Security Admin Console
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Direct Navigation Routes
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/admin")


@app.get("/admin", include_in_schema=False)
@app.get("/admin/", include_in_schema=False)
async def admin_portal():
    return RedirectResponse(url="/static/admin/index.html")


@app.get("/api/health", tags=["Health & Status"])
async def health_check():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "2.4.0",
        "timestamp": time.time(),
    }
