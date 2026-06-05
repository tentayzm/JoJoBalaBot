"""Main bot entry point."""
import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import Config
from handlers import setup_handlers
from middlewares.logging_middleware import LoggingMiddleware
from health_server import start_health_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)


async def self_ping():
    """هر 4 دقیقه یکبار به خودش پینگ میزنه تا Render نخوابونه"""
    import aiohttp
    while True:
        await asyncio.sleep(240)  # 4 دقیقه
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://jojobalabot-10.onrender.com/health") as resp:
                    if resp.status == 200:
                        logger.info("✅ Self-ping successful")
                    else:
                        logger.warning(f"⚠️ Self-ping failed with status {resp.status}")
        except Exception as e:
            logger.error(f"❌ Self-ping error: {e}")


async def main() -> None:
    """Main bot function."""
    try:
        # Load configuration
        config = Config.from_env()
        logger.info("Configuration loaded successfully")
        
        # Initialize bot
        bot = Bot(
            token=config.telegram_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Initialize dispatcher
        dp = Dispatcher()
        
        # Register middleware
        dp.message.middleware(LoggingMiddleware())
        
        # Setup handlers
        main_router = setup_handlers()
        dp.include_router(main_router)
        
        logger.info("Bot handlers and middleware registered")
        
        # Start health check server (for external monitoring)
        asyncio.create_task(start_health_server())
        logger.info("Health check server started on port 8080")
        
        # Start self-ping (to keep the bot awake)
        asyncio.create_task(self_ping())
        logger.info("Self-ping task started (every 4 minutes)")
        
        # Start polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
