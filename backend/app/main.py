from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .accounts.manager import account_manager
from .api.admin.accounts import router as admin_accounts_router
from .api.admin.analytics import router as admin_analytics_router
from .api.admin.api_keys import router as admin_api_keys_router
from .api.admin.auth import router as admin_auth_router
from .api.admin.health import router as admin_health_router
from .api.admin.logs import router as admin_logs_router
from .api.admin.models import router as admin_models_router
from .api.admin.packages import router as admin_packages_router
from .api.admin.parity import router as admin_parity_router
from .api.admin.restart import router as admin_restart_router
from .api.admin.users import router as admin_users_router
from .api.native.extensions import router as native_extensions_router
from .api.native.gems import router as native_gems_router
from .api.native.history import router as native_history_router
from .api.native.jobs import router as native_jobs_router
from .api.native.limits import router as native_limits_router
from .api.native.tasks import router as native_tasks_router
from .api.openai.chat_completions import router as openai_chat_router
from .api.openai.files import router as openai_files_router
from .config import settings
from .db.seed import seed_defaults
from .logging.structured import logger
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.request_logger import RequestLoggerMiddleware
from .models.registry import model_registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed_defaults()
    await account_manager.refresh_accounts()
    await model_registry.discover_models()
    logger.info("app.start", mode=settings.APP_MODE)
    yield
    logger.info("app.stop")


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)
    app.add_middleware(RequestLoggerMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in [
        admin_auth_router,
        admin_users_router,
        admin_accounts_router,
        admin_models_router,
        admin_analytics_router,
        admin_restart_router,
        admin_logs_router,
        admin_health_router,
        admin_api_keys_router,
        admin_packages_router,
        admin_parity_router,
        openai_chat_router,
        openai_files_router,
        native_limits_router,
        native_tasks_router,
        native_gems_router,
        native_history_router,
        native_extensions_router,
        native_jobs_router,
    ]:
        app.include_router(router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    @app.get("/ready")
    async def readiness_check():
        return {"status": "ready"}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.API_PORT)
