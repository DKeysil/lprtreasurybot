from bot import dp, types
from motor_client import SingletonClient


@dp.message_handler(lambda message: message.chat.type == 'private', commands=['menu'])
async def menu(message: types.Message):
    """
    Sends menu to user. Works only in private.

    Args:
        message (types.Message): telegram message
    """
    fund_button = types.KeyboardButton('/fund')
    funds_button = types.KeyboardButton('/funds')
    rating_button = types.KeyboardButton('/rating')
    status_button = types.KeyboardButton('/status')
    subscribe_button = types.KeyboardButton('/subscribe')
    unsubscribe_button = types.KeyboardButton('/unsubscribe')
    transcations_button = types.KeyboardButton('Транзакции')
    
    btn_list = [
        [fund_button, funds_button, rating_button],
        [status_button, subscribe_button, unsubscribe_button],
        [transcations_button]
    ]

    db = SingletonClient.get_data_base()
    users_collection = db.users

    user = await users_collection.find_one({
        "user_id": message.from_user.id
    })
    if user:
        if user.get('treasurer'):
            settings_button = types.KeyboardButton('/settings')
            btn_list.append([settings_button])

    menu_keyboard_markup = types.ReplyKeyboardMarkup(btn_list)
    await message.answer('Вам открыт доступ к меню бота.', reply_markup=menu_keyboard_markup)
