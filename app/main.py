from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.logging_config import logger
from app.settings import settings
from app.db.engine import async_engine
from app.api.v1.subscriptions import router as subscriptions_router
from app.admin.views import SubscriptionAdmin, PlanAdmin
from app.deps.auth import require_admin


logger.info("Starting Subscription Service")


class RequireAdminBackend(AuthenticationBackend):
    async def authenticate(self, request: Request) -> bool:
        try:
            await require_admin(request)
            return True
        except Exception:
            logger.warning("Admin authentication failed for request %s", request)
            return False


app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    subscriptions_router,
    prefix="/api/v1",
)

admin = Admin(
    app=app,
    engine=async_engine.sync_engine,
    authentication_backend=RequireAdminBackend(secret_key=settings.secret_key),
)
admin.add_view(PlanAdmin)
admin.add_view(SubscriptionAdmin)

@app.get("/health", tags=["health"])
async def health() -> dict:
    logger.info("Health check requested")
    return {"status": "ok"}
