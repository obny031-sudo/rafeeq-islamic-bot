from .start import router as start_router
from .prayer import router as prayer_router
from .quran import router as quran_router
from .adhkar import router as adhkar_router
from .settings import router as settings_router
from .features import router as features_router
from .quran_reading import router as quran_reading_router
from .hadith import router as hadith_router
from .ai_assistant import router as ai_assistant_router
from .admin import router as admin_router

__all__ = [
    "start_router",
    "prayer_router",
    "quran_router",
    "adhkar_router",
    "settings_router",
    "features_router",
    "quran_reading_router",
    "hadith_router",
    "ai_assistant_router",
    "admin_router",
]
