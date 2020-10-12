from bot import dp, types
from defs import google_sheets_values, beauty_sum
from motor_client import SingletonClient
import os
from calendar import monthrange
from datetime import datetime
import time


@dp.message_handler(commands=['status'])
async def status(message: types.Message):
    resp = await google_sheets_values('lprtreasurybot.balance', 'A1', 'A1')

    string = 'Состояние казны: \n<b>' + beauty_sum(resp[0][0]) + '</b> ₽\n\n'
    db = SingletonClient.get_data_base()

    month = time.strftime("%m")
    year = '20' + time.strftime("%y")
    cursor = db.transactions.find({
        "date": {
            "$gte": str(datetime.strptime("01 {} {}".format(month, year), "%d %m %Y")),
            "$lte": str(
                datetime.strptime("{} {} {}".format(
                    monthrange(int(year), int(month))[1],
                    month,
                    year), "%d %m %Y")
            )
        }
    })
    _transactions = await cursor.to_list(length=await db.transactions.count_documents({}))
    donates_sum = sum([value['total'] for value in _transactions if (value['total'] > 0 and
                                                                     value['comment'] != 'Техническая')])
    string += f'Сумма донатов за текущий месяц \n<b>' + beauty_sum(donates_sum) + '</b> ₽'
    string += f'\n\n<a href="{os.environ["DONATE_LINK"]}">Задонатить</a>'
    await message.reply(string, parse_mode='HTML', disable_web_page_preview=True)
