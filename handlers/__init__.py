from .start import router as start_router
from .cabinet import router as cabinet_router
from .subscriptions import router as subscriptions_router
from .payments import router as payments_router
from .admin import router as admin_router
from .languages import router as languages_router
from .gift import router as gift_router
from .donate import router as donate_router
from .referral import router as referral_router
from .status import router as status_router

__all__ = [
    "start_router",
    "cabinet_router",
    "subscriptions_router",
    "payments_router",
    "admin_router",
    "languages_router",
    "gift_router",
    "donate_router",
    "referral_router",
    "status_router",
]
