from bot import dp, types
from defs import google_sheets_values, beauty_sum


@dp.message_handler(commands=['funds'])
async def funds(message: types.Message):
    _funds = await google_sheets_values('lprtreasurybot.funds', 'A1', 'B99999')

    _funds = [[i[0], i[1][1:]] for i in _funds if int(i[0]) != 0]

    string = ''

    for row in _funds:
        string += f'<code>{beauty_sum(row[0]).strip(): >6}</code> ₽ - <b>{row[1]}</b>\n'
    
    await message.reply(f'Список фондов: \n{string}', parse_mode='HTML')
