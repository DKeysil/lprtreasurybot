from bot import dp, types
from motor_client import SingletonClient
from datetime import datetime
from defs import beauty_sum
from datetime import datetime
from defs import update_data
from defs import get_mention


@dp.message_handler(commands=['t'])
async def transactions(message: types.Message, mention=None):
    """
    Создает сообщение со списком транзакций конкретного пользователя.
    Уточнить пользователя из таблицы можно вторым параметром (/t username)
    """

    if not mention:
        mention = await get_mention(message)

    await update_data()
    _transactions, transactions_sum = await get_transcations(0, mention)
    if transactions is None:
        return await message.reply('Транзакции этого пользователя не найдены')

    string = f"Транзакции пользователя {mention}:\n"
    string += f'Общая сумма донатов - <code>{beauty_sum(transactions_sum)}</code>₽\n\n'
    string += get_transcations_string(_transactions)

    markup = types.InlineKeyboardMarkup()

    """
    callback_data:
    1) t - название модуля
    2) l, r, n - left, right, none
    3) int - номер страницы
    4) имя пользователя для поиска в таблице
    """

    left_button = types.InlineKeyboardButton(
        text='❌', callback_data=f't,l,0,{mention}')

    right_list = await get_transcations(1, mention)
    if right_list:
        right_button = types.InlineKeyboardButton(
            text='➡️', callback_data=f't,r,1,{mention}'
        )

        markup.row(left_button, right_button)
        _message = await message.answer(string, reply_markup=markup, parse_mode='HTML')
    else:
        _message = await message.answer(string, parse_mode='HTML')


@dp.callback_query_handler(lambda callback_query: callback_query.data.split(',')[0] == 't')
async def handle_t_callback_query(callback_query: types.CallbackQuery):
    """
    Обработчик нажатия на кнопку под сообщением со списком транзакций.
    Лямбда проверяет, чтобы обрабатывалось только y кнопки

    Args:
        callback_query (types.CallbackQuery): Документация на сайте телеграма
    """
    if callback_query.data.split(',')[1] == 'n':
        return await callback_query.answer(text='Там больше ничего нет...')
    split_data = callback_query.data.split(',')

    page = int(split_data[2])
    mention = split_data[3]

    _transactions, transactions_sum = await get_transcations(page, mention)
    string = f"Транзакции пользователя {mention}:\n"
    string += f'Общая сумма донатов - <code>{beauty_sum(transactions_sum)}</code>₽\n'
    string += get_transcations_string(_transactions)

    markup = types.InlineKeyboardMarkup()

    # Проверяет, есть ли транзакции на предыдущих страницах.
    left_list = await get_transcations(page - 1, mention)
    if left_list:
        left_button = types.InlineKeyboardButton(
            text='⬅️', callback_data=f't,l,{page-1},{mention}')
    else:
        left_button = types.InlineKeyboardButton(
            text='❌', callback_data=f't,n,{page},{mention}')

    # Проверяет, есть ли транзакции на следующих страницах.
    right_list = await get_transcations(page + 1, mention)
    if right_list:
        right_button = types.InlineKeyboardButton(
            text='➡️', callback_data=f't,r,{page+1},{mention}')
    else:
        right_button = types.InlineKeyboardButton(
            text='❌', callback_data=f't,n,{page},{mention}')

    markup.row(left_button, right_button)

    _message = await callback_query.message.edit_text(string, reply_markup=markup, parse_mode='HTML')
    await callback_query.answer()


async def get_transcations(page: int, mention) -> (list, int):
    """
    Сахар для получения списка транзакций

    Args:
        page (int): Номер страницы из callback data
        mention ([type]): ник пользователя. По нему идет поиск в бд

    Returns:
        list[{'total': int, 'fund': str}]: Возвращает список транзакций соответствующий странице
    """
    db = SingletonClient.get_data_base()

    # Поиск ника с собачкой перед ником. Такой ник означает донат, а не трату.
    if mention[0] != '@':
        cursor = db.transactions.find({
            "from": '@' + mention
        })

        # Если ника с собачкой в базе нет, то поиск производится по введенному нику.
        if await cursor.to_list(length=1):
            mention = '@' + mention

    cursor = db.transactions.find({
        "from": mention
    }).sort('date', -1)

    _transactions = await cursor.to_list(length=await db.transactions.count_documents({}))
    transactions_sum = sum([value['total'] for value in _transactions if value['total'] > 0])
    try:
        return _transactions[page * 10: page * 10 + 10], transactions_sum
    except IndexError:
        return [], 0


def get_transcations_string(_transactions: list) -> str:
    """
    Генерирует строку из входящего списка транзакций

    Args:
        _transactions (list): Список транзакций из метода get_transactions

    Returns:
        str: Возвращает список донатов в строковом формате
    """
    string = ""
    for data in _transactions:
        date = datetime.strptime(data['date'][0:10], '%Y-%m-%d')
        string += f'{date.strftime("%d.%m.%Y")} <code>{beauty_sum(data["total"]).strip(): >6}</code> ₽ {data["fund"]}\n'

    return string
