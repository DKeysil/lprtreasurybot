from bot import dp, types
from defs import google_sheets_values, beauty_sum


@dp.message_handler(commands=['status'])
async def status(message: types.Message):
    resp = await google_sheets_values("Состояние в рублях", "A2", "A2")

    string = 'Состояние казны: \n<b>' + beauty_sum(resp_json[0][0]) + '</b> ₽'
    await message.reply(string, parse_mode='HTML')
