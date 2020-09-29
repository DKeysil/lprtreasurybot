from bot import dp, types
from motor_client import SingletonClient


@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
    """
    Unsubscribing user from notifications

    Args:
        message (types.Message): telegram message
    """
    db = SingletonClient.get_data_base()

    user = await db.users.find_one({
        "user_id": message.from_user.id
    })

    if user:
        result = await db.users.update_one(
            {"user_id": message.from_user.id},
            {"$set": {'subscribe': False}}
        )
        print('Unsubscribe. Update user:\n' + str(result.raw_result))
        await message.reply('Вы успешно отписались от обновлений')
    else:
        await message.reply('Вы не подписаны на обновления')
