from bot import dp, types, FSMContext
from motor_client import SingletonClient
from aiogram.dispatcher.filters.state import State, StatesGroup
from defs import google_sheets_values
from bot.modules.menu.Menu import menu


class Settings(StatesGroup):
    settings_menu = State()
    preffered_fund = State()
    allowed_chats = State()


@dp.message_handler(lambda message: message.chat.type == 'private', commands=['settings'])
async def settings(message: types.Message):
    """
    Sends settings menu only for treasurer

    Args:
        message (types.Message): telegram message
    """
    db = SingletonClient.get_data_base()
    users_collection = db.users

    user = await users_collection.find_one({
        "user_id": message.from_user.id
    })

    if user.get('treasurer'):
        await Settings.settings_menu.set()

        preffered_fund_button = types.KeyboardButton('Предпочтительный фонд')
        allowed_chats = types.KeyboardButton('Разрешенные чаты')
        back_button = types.KeyboardButton('Назад')
        btn_list = [
            [preffered_fund_button, allowed_chats],
            [back_button]
        ]
        settings_keyboard_markup = types.ReplyKeyboardMarkup(btn_list)
        await message.answer('Меню настроек:', reply_markup=settings_keyboard_markup)


@dp.message_handler(lambda message: message.text == 'Предпочтительный фонд', state=[Settings.settings_menu, Settings.preffered_fund])
async def preffered_fund(message: types.Message, state: FSMContext):
    """
    Logic to choose preffered fund.

    Args:
        message (types.Message): telegram message
        state (FSMContext): state memory
    """
    await Settings.preffered_fund.set()
    string = 'Список доступных фондов. Выберите один или пришлите сообщением:\n'

    funds = await google_sheets_values('lprtreasurybot.funds', 'A1', 'B99999')

    funds = [i[1] for i in funds if int(i[0]) != 0]
    funds_buttons = []
    cnt = 0
    for fund in funds:
        # makes 3xn keyboard markup
        try:
            funds_buttons[cnt//3].append(types.KeyboardButton(fund))
        except IndexError:
            funds_buttons.append([types.KeyboardButton(fund)])
        cnt += 1

    funds_reply_keyboard = types.ReplyKeyboardMarkup(funds_buttons)
    string += '\n'.join(funds)
    await message.answer(string, reply_markup=funds_reply_keyboard)


@dp.message_handler(state=Settings.preffered_fund)
async def set_preffered_fund(message: types.Message, state: FSMContext):
    """
    Set preffered fund in DB

    Args:
        message (types.Message): telegram message
        state (FSMContext): state memory

    Returns:
        [type]: calls settings menu
    """
    if len(message.text) < 32:
        fund_name = message.text
    else:
        return await message.answer('Неправильное название фонда')

    db = SingletonClient.get_data_base()

    result = await db.settings.update_one({"id": 0}, {"$set": {"preffered_fund": fund_name}})
    logger.info('set_preffered_fund. update preffered fund:\n' + str(result.raw_result))

    if result.modified_count != 1:
        result = await db.settings.insert_one({"id": 0, "preffered_fund": fund_name})
        logger.info('set_preffered_fund. insert preffered fund id:\n' +
              str(result.inserted_id))

    await message.answer('Предпочтительный фонд был успешно изменен на {}'.format(fund_name), parse_mode='HTML')

    return await settings(message)


@dp.message_handler(lambda message: message.text == 'Назад', state=Settings.settings_menu)
async def back_action(message: types.Message, state: FSMContext):
    """
    back logic. finishing finite state machine part and calls menu

    Args:
        message (types.Message): telegram message
        state (FSMContext): state memory
    """
    await state.finish()
    await menu(message)


@dp.message_handler(lambda message: message.text == 'Разрешенные чаты', state=[Settings.settings_menu, Settings.allowed_chats])
async def allowed_chats(message: types.Message, state: FSMContext):
    """
    Logic to set allowed chats.

    Args:
        message (types.Message): telegram message
        state (FSMContext): state memory
    """
    await Settings.allowed_chats.set()

    db = SingletonClient.get_data_base()
    chats = []

    _settings = await db.settings.find_one({
        "id": 0
    })
    if _settings:
        if _settings.get('allowed_chats'):
            chats += [str(i) for i in _settings.get('allowed_chats')]

    string = ''
    if chats:
        string += 'Сейчас для использования доступны эти чаты:\n\n'
        string += ', '.join(chats)
    remove_keyboard = types.ReplyKeyboardRemove()
    if string:
        await message.answer(string, reply_markup=remove_keyboard)

    string = 'Пришлите полный список доступных чатов, разделенные через запятую.\n'
    string += 'Например:\n379542159, 246256258, -1001430465521'
    string += '\nЧтобы разрешить все чаты пришлите: -'

    await message.answer(string, reply_markup=remove_keyboard)


@dp.message_handler(state=Settings.allowed_chats)
async def set_allowed_chats(message: types.Message, state: FSMContext):
    """
    Set allowed chats in DB

    Args:
        message (types.Message): telegram message
        state (FSMContext): state memory

    Returns:
        [type]: calls settings menu
    """
    db = SingletonClient.get_data_base()

    if message.text == '-':
        result = await db.settings.update_one({"id": 0}, {"$set": {"allowed_chats": []}})
        logger.info('allowed_chats. update allowed chats:\n' + str(result.raw_result))

        if result.modified_count != 1:
            result = await db.settings.insert_one({"id": 0, "allowed_chats": []})
            logger.info('allowed_chats. insert allowed chats id:\n' +
                  str(result.inserted_id))
        await message.answer('Теперь бот доступен из любого чата.')
        return await settings(message)

    try:
        chats = list(map(int, message.text.split(', ')))
    except ValueError:
        chats = []
        logger.info('allowed_chats. ValueError while parse funds list')

    if chats:
        result = await db.settings.update_one({"id": 0}, {"$set": {"allowed_chats": chats}})
        logger.info('allowed_chats. update allowed chats:\n' + str(result.raw_result))

        if result.modified_count != 1:
            result = await db.settings.insert_one({"id": 0, "allowed_chats": chats})
            logger.info('allowed_chats. insert allowed chats id:\n' +
                  str(result.inserted_id))
        await message.answer('Для бота были установлены доступные чаты.')
        return await settings(message)

    return await message.answer('Неправильный формат данных. Если вы хотите из этого меню, напишите /cancel.')
