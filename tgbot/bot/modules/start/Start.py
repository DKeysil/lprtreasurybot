from bot import dp, types
from motor_client import SingletonClient


@dp.message_handler(lambda message: message.chat.type == 'private', commands=['start'])
async def start(message: types.Message):
    db = SingletonClient.get_data_base()
    users_collection = db.users

    user = await users_collection.find_one({
        "user_id": message.from_user.id
    })

    if user:
        await message.reply('Вы уже есть в базе данных.')
    else:
        user_data = {"user_id": message.from_user.id,
                     "first_name": message.from_user.first_name,
                     "username": message.from_user.mention,
                     "subscribe": False,
                     'treasurer': False}

        result = await users_collection.insert_one(user_data)
        print('start. Insert user id = ' + str(result.inserted_id))

        await message.reply('Добро пожаловать.\nКоманда /menu открое меню команд.')
