from bot import dp, types
from motor_client import SingletonClient
from loguru import logger


@dp.message_handler(commands=['subscribe'])
async def subscribe(message: types.Message):
    """
    Subscribing user to notifications

    Args:
        message (types.Message): telegram message
    """
    db = SingletonClient.get_data_base()

    user = await db.users.find_one({
        "user_id": message.from_user.id
    })
    logger.info(user)

    if user is None:
        # if user not in DB creates user and subscribe him to notifications
        user_data = {"user_id": message.from_user.id,
                     "first_name": message.from_user.first_name,
                     "username": message.from_user.mention,
                     "subscribe": True}

        result = await db.users.insert_one(user_data)
        logger.info('Subscribe. Insert user id = ' + str(result.inserted_id))

        await message.reply('Вы успешно подписались на обновления')
    elif user.get('subscribe'):
        await message.reply('Вы уже подписаны на обновления')
    elif user.get('subscribe') == False:
        # if user doesn't subscribed change "subscribe" column
        result = await db.users.update_one(
            {"user_id": message.from_user.id},
            {"$set": {'subscribe': True}}
        )
        logger.info('Subscribe. Update user:\n' + str(result.raw_result))
        await message.reply('Вы успешно подписались на обновления')
    else:
        result = await db.users.update_one(
            {"user_id": message.from_user.id},
            {"$set": {'subscribe': True}}
        )
        logger.info('Subscribe. Update user:\n' + str(result.raw_result))
        await message.reply('Вы успешно подписались на обновления')
        
