from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.api.admin.auth import router as admin_auth_router
from backend.app.api.admin.users import router as admin_users_router
from backend.app.api.admin.accounts import router as admin_accounts_router
from backend.app.api.admin.models import router as admin_models_router
from backend.app.api.admin.analytics import router as admin_analytics_router
from backend.app.api.admin.restart import router as admin_restart_router
from backend.app.api.admin.logs import router as admin_logs_router
from backend.app.api.admin.health import router as admin_health_router
from backend.app.api.admin.api_keys import router as admin_api_keys_router
from backend.app.api.admin.packages import router as admin_packages_router
from backend.app.api.admin.parity import router as admin_parity_router
from backend.app.api.openai.chat_completions import router as openai_chat_router
from backend.app.api.openai.files import router as openai_files_router
from backend.app.api.native.limits import router as native_limits_router
from backend.app.api.native.tasks import router as native_tasks_router
from backend.app.api.native.gems import router as native_gems_router
from backend.app.api.native.history import router as native_history_router
from backend.app.api.native.extensions import router as native_extensions_router
from backend.app.accounts.manager import account_manager
from backend.app.models.registry import model_registry
from backend.app.logging.structured import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up", app_name=settings.APP_NAME)
    try:
        await account_manager.refresh_accounts()
    except Exception as e:
        logger.error("Failed to initialize accounts on startup", error=str(e))
    # Always seed / refresh the model registry on startup
    try:
        await model_registry.discover_models()
    except Exception as e:
        logger.error("Failed to seed model registry on startup", error=str(e))
    yield
    logger.info("Shutting down", app_name=settings.APP_NAME)


from backend.app.middleware.request_logger import RequestLoggerMiddleware
from backend.app.middleware.rate_limit import RateLimitMiddleware

def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)

    # Middlewares
    app.add_middleware(RequestLoggerMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(admin_auth_router)
    app.include_router(admin_users_router)
    app.include_router(admin_accounts_router)
    app.include_router(admin_models_router)
    app.include_router(admin_analytics_router)
    app.include_router(admin_restart_router)
    app.include_router(admin_logs_router)
    app.include_router(admin_health_router)
    app.include_router(admin_api_keys_router)
    app.include_router(admin_packages_router)
    app.include_router(admin_parity_router)
    app.include_router(openai_chat_router)
    app.include_router(openai_files_router)
    app.include_router(native_limits_router)
    app.include_router(native_tasks_router)
    app.include_router(native_gems_router)
    app.include_router(native_history_router)
    app.include_router(native_extensions_router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    @app.get("/ready")
    async def readiness_check():
        # TODO: Add check for DB, Redis, and Upstream providers
        return {"status": "ready"}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.API_PORT)
