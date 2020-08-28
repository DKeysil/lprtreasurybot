from bot import dp, types
from defs import rating_string, update_data
import time
import re
import os


async def get_string(message: types.Message) -> str:

    try:
        # Проверка сообщения на соответствие с стандартом "month.year"
        pattern = r'((0[1-9]|1[0-2])\.([0-9]\d))'
        _time = re.search(pattern, message.get_args().split(' ')[0]).group()
    except AttributeError:
        _time = ''
    print(_time)
    try:
        # Если будет найдена передаваемая пользователем дата, то она будет передана
        _time = time.strptime(_time, "%m.%y")
        month = time.strftime('%m', _time)
        year = time.strftime('%y', _time)
        string = await rating_string(month=month, year=year)
    except ValueError:
        string = await rating_string()

    string += f'\n<a href="{os.environ["DONATE_LINK"]}">Задонатить</a>'
    return string


@dp.message_handler(commands=['rating'])
async def rating(message: types.Message):

    string = await get_string(message)

    # Если донаты есть, то строка существует
    if string:
        _message = await message.reply(string, parse_mode='HTML', disable_web_page_preview=True)

        await update_data()  # Апдейт данных из таблицы
        # если информация неактуальна, то сообщение будет изменено
        _string = await get_string(message)
        if string == _string:
            return None

        await _message.edit_text(_string, parse_mode='HTML', disable_web_page_preview=True)
        return None

    _message = await message.reply('Донатов за этот месяц еще не поступало :(')

    await update_data()
    _string = await get_string(message)
    if string == _string:
        return None

    await _message.edit_text(_string, parse_mode='HTML', disable_web_page_preview=True)
