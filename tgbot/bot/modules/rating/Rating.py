from bot import dp, types
from defs import rating_string, update_data
import time
import re
import os


async def get_string(message: types.Message) -> str:
    """
    Trying to find argument in message and get string from def/rating_string(), 
    if it doesn't exist just get string from def/rating_string()

    Args:
        message (types.Message): telegram message

    Returns:
        str: string which contains list of top donaters
    """

    try:
        argument = message.get_args().split(' ')[0]
        # Проверка сообщения на соответствие с стандартом "month.year"
        pattern = r'((0[1-9]|1[0-2])\.([0-9]\d))'
        # Проверка сообщения на соответствие с стандартом "month.year-month.year"
        range_pattern = r'((0[1-9]|1[0-2])\.([0-9]\d))\-((0[1-9]|1[0-2])\.([0-9]\d))'
        _time = re.search(pattern, argument).group()
        _range_time = re.search(range_pattern, argument).group().split('-')[1]
    except AttributeError:
        _time = ''

    # Проверка сообщения на запрос фонда (Не начинается с цифры)
    fund_pattern = r'^\D*'
    fund = re.search(fund_pattern, argument).group()
    if fund:
        string = await rating_string(fund=fund)
    else:
        try:
            # Если будет найдена передаваемая пользователем дата, то она будет передана
            _time = time.strptime(_time, "%m.%y")
            month = time.strftime('%m', _time)
            year = time.strftime('%y', _time)
            if _range_time:
                _range_time = time.strptime(_range_time, "%m.%y")
                to_month = time.strftime('%m', _range_time)
                to_year = time.strftime('%y', _range_time)
                string = await rating_string(month=month, year=year, to_month=to_month, to_year=to_year)
            else:
                string = await rating_string(month=month, year=year)
        except ValueError:
            # if user doesn't pass time argument call rating_string() with default arguments
            string = await rating_string()

    if string:
        string += f'\n<a href="{os.environ["DONATE_LINK"]}">Задонатить</a>'
    else:
        # Если строка рейтинга пустая вернуть none
        return None

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
