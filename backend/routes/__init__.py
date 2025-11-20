from .auth import router as auth_router
from .orders import router as orders_router
from .drivers import router as drivers_router
from .vendors import router as vendors_router
from .tracking import router as tracking_router
from .reports import router as reports_router
from .webhooks import router as webhooks_router
from .uploads import router as uploads_router
from .optimization import router as optimization_router

__all__ = [
    "auth_router",
    "orders_router",
    "drivers_router",
    "vendors_router",
    "tracking_router",
    "reports_router",
    "webhooks_router",
    "uploads_router",
    "optimization_router"
]