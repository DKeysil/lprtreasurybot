from bot import dp, types
from defs import google_sheets_values, beauty_sum
import os


@dp.message_handler(commands=['status'])
async def status(message: types.Message):
    resp = await google_sheets_values('lprtreasurybot.balance', 'A1', 'A1')

    string = 'Состояние казны: \n<b>' + beauty_sum(resp[0][0]) + '</b> ₽'
    string += f'\n\n<a href="{os.environ["DONATE_LINK"]}">Задонатить</a>'
    await message.reply(string, parse_mode='HTML', disable_web_page_preview=True)
