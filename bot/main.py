import asyncio
from bot.loader import bot, dp 
from bot.handlers import start, admin, seller
from bot.middlewares.db import DBMiddleware
from bot.middlewares.UserMiddleware import UserMiddleware
from database import init_models

def setup_handlers():
    dp.update.outer_middleware(DBMiddleware())
    dp.update.outer_middleware(UserMiddleware())
    
    dp.include_router(start.router)
    dp.include_router(admin.admin_router)
    dp.include_router(seller.seller_router)

async def main():
    await init_models()
    setup_handlers()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())