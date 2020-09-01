from loop import loop
from bot import dp
from aiogram import executor
from datetime import datetime
import asyncio
from bot.modules.send_treasury_update.SendTreasuryUpdate import send_treasury_update


if __name__ == "__main__":
    executor.start_polling(dp, loop=loop, skip_updates=True)
