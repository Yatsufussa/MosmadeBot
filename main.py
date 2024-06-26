import os
import asyncio
from common.bot_cmds_list import private
from middleware.db import DataBaseSession
from aiogram import Bot, Dispatcher, types
from dotenv import find_dotenv, load_dotenv
from handlers.admin_private import admin_router
from handlers.user_group import user_group_router
from database.engine import create_db, drop_db, SessionMaker
from handlers.user_private import user_private, register_handlers_user_private

load_dotenv(find_dotenv())

ALLOWED_UPDATES = ['message, edited_message']

bot = Bot(token=os.getenv('TOKEN'))
bot.my_admins_list = []


dp = Dispatcher()
register_handlers_user_private(bot)
dp.include_router(user_private)
dp.include_router(user_group_router)
dp.include_router(admin_router)


async def on_startup(bot):
    run_param = False
    if run_param:
        await drop_db()
    await create_db()

async def on_shutdown(bot):
    print('Bot Spit')

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.update.middleware(DataBaseSession(session_pool=SessionMaker))
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)

asyncio.run(main())