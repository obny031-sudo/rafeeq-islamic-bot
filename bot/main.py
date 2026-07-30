import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage

from config.settings import settings
from config.database import init_db, AsyncSessionLocal
from utils.database import get_db
from utils.redis_client import redis_client
from utils.shared_cache import shared_cache
from utils.seed_data import seed_adhkar_content
from middleware import ErrorHandlingMiddleware, UserMiddleware
from middleware.rate_limit import rate_limit_middleware
from middleware.maintenance import MaintenanceMiddleware
from bot.core import plugin_manager
from bot.core.health_check import init_health_check_service, HealthStatus
from bot.plugins.prayer import PrayerPlugin
from bot.plugins.quran import QuranPlugin
from bot.plugins.adhkar import AdhkarPlugin
from services.scheduler_service import scheduler_service
from utils.logger import get_logger

logger = get_logger("rafeeq")


async def run_startup_health_checks(bot: Bot) -> bool:
    """Validate DB, Redis, and Telegram API before polling."""
    await shared_cache.connect()
    health_service = init_health_check_service(bot, AsyncSessionLocal, shared_cache)
    health = await health_service.check_all()

    for name, component in health["components"].items():
        status = component["status"]
        emoji = "✅" if status == HealthStatus.HEALTHY.value else "❌"
        logger.info("%s %s: %s", emoji, name, component["message"])

    if health["overall_status"] != HealthStatus.HEALTHY.value:
        logger.warning("Startup health check degraded — bot will continue with available services")
    return health["overall_status"] == HealthStatus.HEALTHY.value


async def main():
    """Main bot entry point with plugin architecture."""
    settings.validate()
    logger.info("Starting Rafeeq Islamic Telegram Super App v%s", settings.APP_VERSION)

    await init_db()
    logger.info("Database initialized successfully")

    async with AsyncSessionLocal() as session:
        seeded = await seed_adhkar_content(session)
        await session.commit()
        if seeded:
            logger.info("Seeded %s adhkar records into PostgreSQL", seeded)

    await redis_client.connect()
    logger.info("Redis connected successfully")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )

    storage = RedisStorage(redis=redis_client.client)
    dp = Dispatcher(storage=storage)

    plugin_manager.register_plugin(PrayerPlugin())
    plugin_manager.register_plugin(QuranPlugin())
    plugin_manager.register_plugin(AdhkarPlugin())

    await plugin_manager.initialize_all(bot, dp)
    logger.info("Initialized %s plugins", len(plugin_manager.get_enabled_plugins()))

    from handlers.start import router as start_router
    from handlers.settings import router as settings_router
    from handlers.features import router as features_router
    from handlers.quran_reading import router as quran_reading_router
    from handlers.quran import router as quran_router
    from handlers.prayer import router as prayer_router
    from handlers.adhkar import router as adhkar_router
    from handlers.hadith import router as hadith_router
    from handlers.ai_assistant import router as ai_assistant_router
    from handlers.admin import router as admin_router
    from handlers.navigation import router as navigation_router
    from handlers.tasbeeh import router as tasbeeh_router
    from handlers.low_data import router as low_data_router
    from handlers.mood_adhkar import router as mood_adhkar_router
    from handlers.language import router as language_router
    from handlers.tafseer import router as tafseer_router
    from handlers.location_prayer import router as location_prayer_router
    from handlers.adhkar_timings import router as adhkar_timings_router
    from handlers.daily_broadcasts import router as daily_broadcasts_router
    from handlers.friday_reminder import router as friday_reminder_router

    # Register routers in order of priority
    # Start router must be first to handle /start command
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(navigation_router)
    dp.include_router(tasbeeh_router)
    dp.include_router(low_data_router)
    dp.include_router(mood_adhkar_router)
    dp.include_router(language_router)
    dp.include_router(tafseer_router)
    dp.include_router(location_prayer_router)
    dp.include_router(adhkar_timings_router)
    dp.include_router(daily_broadcasts_router)
    dp.include_router(friday_reminder_router)
    dp.include_router(settings_router)
    dp.include_router(features_router)
    dp.include_router(quran_reading_router)
    dp.include_router(quran_router)
    dp.include_router(prayer_router)
    dp.include_router(adhkar_router)
    dp.include_router(hadith_router)
    dp.include_router(ai_assistant_router)

    async def db_middleware(handler, event, data):
        """Inject database session and auto-commit on success."""
        async for session in get_db():
            data["db"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise

    dp.update.middleware(db_middleware)
    dp.update.middleware(UserMiddleware())
    dp.update.middleware(rate_limit_middleware)
    dp.update.outer_middleware(MaintenanceMiddleware())
    dp.update.outer_middleware(ErrorHandlingMiddleware())

    await run_startup_health_checks(bot)

    # Set up chat menu button for web app
    try:
        from aiogram.types import MenuButtonWebApp, WebAppInfo
        web_app_url = "https://rafeeq-islamic-bot-ten.vercel.app"
        
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="📱 افتح التطبيق",
                web_app=WebAppInfo(url=web_app_url)
            )
        )
        logger.info("Chat menu button configured for web app")
    except Exception as e:
        logger.warning(f"Failed to set chat menu button: {e}")

    scheduler_service.set_bot(bot)
    await scheduler_service.start()
    logger.info("Scheduler started successfully")

    logger.info("Bot started successfully")
    try:
        await dp.start_polling(bot)
    finally:
        await scheduler_service.shutdown()
        await plugin_manager.shutdown_all()
        await bot.session.close()
        await shared_cache.disconnect()
        await redis_client.disconnect()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
