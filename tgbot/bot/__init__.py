from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import os
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from motor_client import SingletonClient

API_TOKEN = os.environ['BOT_API_KEY']

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class ChatCheckerMiddleware(BaseMiddleware):

    def __init__(self):
        super(ChatCheckerMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        if message.get_command() == '/get_me':
            return

        db = SingletonClient.get_data_base()
        allowed_chats = []

        settings = await db.settings.find_one({
            "id": 0
        })
        if settings:
            if settings.get('allowed_chats'):
                allowed_chats += settings.get('allowed_chats')

                if os.environ.get('ALLOWED_CHATS'):
                    environ_chats = list(map(int, os.environ['ALLOWED_CHATS'].split(',')))
                    allowed_chats += environ_chats

                treasurers_cursor = db.users.find({
                    "treasurer": True
                })

                treasurers = await treasurers_cursor.to_list(length=await db.users.count_documents({}))
                for treasurer in treasurers:
                    allowed_chats.append(treasurer.get('user_id'))

                if message.chat.id not in allowed_chats:
                    raise CancelHandler()


dp.middleware.setup(ChatCheckerMiddleware())

from bot import modules
