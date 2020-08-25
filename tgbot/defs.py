
import os
import time
import re

import aiohttp
from datetime import datetime
from calendar import monthrange
from PIL import Image, ImageDraw, ImageFont

from motor_client import SingletonClient
from loop import loop

GOOGLE_SHEETS_API_KEY = os.environ['GOOGLE_SHEETS_API_KEY']

GOOGLE_SHEETS_BASE_URL = 'https://sheets.googleapis.com/v4/spreadsheets'
GOOGLE_SHEETS_SPREADSHEET_ID = '1sRwkcvvYqPrHFpnEdkiEjkhd-j7obFX3KF4NI0AUu6Y'


async def google_sheets_values(
        sheet: str,
        start: str = 'A1',
        stop: str = 'ZZ99999',
        value_render_option: str = 'UNFORMATTED_VALUE',
        date_time_render_option: str = 'FORMATTED_STRING',
) -> dict:
    
    range_ = '!'.join([
        sheet,
        ':'.join([start, stop,]),
    ])

    url = '/'.join([
        GOOGLE_SHEETS_BASE_URL,
        GOOGLE_SHEETS_SPREADSHEET_ID,
        'values',
        range_,
    ])

    params = {
        'key': GOOGLE_SHEETS_API_KEY,
        'valueRenderOption': value_render_option,
        'dateTimeRenderOption': date_time_render_option,
    }

    async with aiohttp.ClientSession(loop=loop) as session:
        async with session.get(url, params=params) as response:
            json = await response.json()
            return json['values']


def parse_command(text):
    pattern = r'\A/\w+'  # Для паттерна используется pythex.org
    try:
        formated = re.search(pattern, text).group()
    except AttributeError:
        formated = None
    return formated


def beauty_sum(just_sum: int) -> str:
    """
    Превращает число в красивую строку
    :param just_sum:
    :return:
    """
    temp_sum = str(int(float(just_sum)))
    beautiful_sum = ''
    for _ in range(round(len(temp_sum) / 3 + 0.49)):
        beautiful_sum = temp_sum[-3:] + ' ' + beautiful_sum
        temp_sum = temp_sum[0:-3]
    return beautiful_sum


def fund_string(just_sum: int, fund_name: str, goal=0) -> str:
    """
    Собирает сообщение о фонде
    :param just_sum:
    :param fund_name:
    :param goal:
    :return:
    """
    string = 'Состояние фонда <b>{}</b>: \n<b>{}</b> ₽\n'.format(
        fund_name, beauty_sum(just_sum))
    if goal != 0:
        string += 'Осталось собрать: \n<b>{}</b> ₽\nПрогресс: [{}{}]'.format(beauty_sum(goal - just_sum),
                                                                             int(just_sum //
                                                                                 (goal / 10)) * '●',
                                                                             int(10 - just_sum // (goal / 10)) * '○')
    return string


def get_fund_image(just_sum: int, fund_name: str, goal: int) -> str:
    """
    Создает изображение фонда и возвращает путь к нему

    Args:
        just_sum (int): [description]
        fund_name (str): [description]
        goal (int): [description]

    Returns:
        str: Путь к изображению
    """

    in_file = 'assets/fund_default.jpg'
    out_file_name = (fund_name + '-' + beauty_sum(just_sum).replace(' ', '') +
                     '-' + beauty_sum(goal).replace(' ', '') + '.png')
    out_file = f'assets/fund_default-{out_file_name}'

    if os.path.isfile(out_file):
        return out_file

        # Загрузка изображения
    img = Image.open(in_file)
    draw = ImageDraw.Draw(img)

    # Загрузка шрифтов
    font_title = ImageFont.truetype('assets/fonts/Gilroy-Bold.ttf', 57)
    font_digitals = ImageFont.truetype('assets/fonts/Gilroy-Extrabold.ttf', 31)

    # Отрисовка шрифтов
    fund_name = fund_name[0].upper() + fund_name[1:]
    draw.text((22, 40), fund_name, fill='#ffffff', font=font_title)

    draw.text((22, 157), beauty_sum(just_sum),
              fill='#ffffff', font=font_digitals)
    draw.text((355, 157), beauty_sum(goal) + '₽',
              fill='#ffffff', font=font_digitals)

    # Отрисовка прогресс бара
    width = 16 + int(just_sum / goal * 467)

    draw.rectangle([16, 113, width, 139], fill='#c1a66f')

    img.save(out_file)
    return out_file


async def fund_sum(fund_title: str) -> [int, int]:
    """
    Парсит количество денег в фонде
    :param fund_title:
    :return:
    """
    fund_title = '#' + fund_title

    fund_goals = await google_sheets_values('lprtreasurybot.fund_goals', 'A1', 'C99999')

    for [balance, fund, goal] in fund_goals:
        if fund == fund_title:
            return [balance, goal]

    funds = await google_sheets_values('lprtreasurybot.funds', 'A1', 'B99999')

    for [balance, fund] in funds:
        if fund == fund_title:
            return [balance, 0]

async def rating_string(month=time.strftime("%m"), year=time.strftime("%y")) -> str:
    """
    Метод возвращает строку, которая содержит топ 5 донатеров
    :return:
    """

    year = '20' + year

    # Сделать импорт нужных данных из монго
    db = SingletonClient.get_data_base()
    collection = db.transactions

    cursor = collection.find({
        "date": {
            "$gte": str(datetime.strptime("01 {} {}".format(month, year), "%d %m %Y")),
            "$lte": str(
                datetime.strptime("{} {} {}".format(monthrange(int(year), int(month))[1], month, year), "%d %m %Y"))
        }
    })

    contributions = await cursor.to_list(length=await collection.count_documents({}))

    dct = {}

    if contributions:
        for i in contributions:
            if i['total'] > 0 and i['comment'] != 'Техническая':
                if dct.get(i['from']):
                    dct[i['from']] += i['total']
                else:
                    dct.update({i['from']: i['total']})
    else:
        return None

    print(dct)
    list_d = list(dct.items())
    list_d.sort(key=lambda j: j[1], reverse=True)
    list_d = list_d[:10]

    string = f'Топ 10 жертвователей за {month}.{year}:\n'

    for i in range(len(list_d)):
        string += '{}) {} - <b>{}</b> ₽\n'.format(
            i + 1, list_d[i][0], beauty_sum(list_d[i][1]))

    return string


async def update_data():
    sheet_rows = await google_sheets_values('lprtreasurybot.transactions', 'A1', 'J99999')

    db_rows = []
    for row in sheet_rows:
        if len(row) != 10:
            continue

        [
            from_,
            total_currency,
            currency_name,
            fund,
            comment,
            date,
            total,
            currency,
            tax_free,
            treasury_balance,
        ] = row

        if not (bool(from_) and bool(date) and bool(total)):
            continue

        db_row = {
            "from": from_.lower(),
            "total_currency": total_currency,
            "currency_name": currency_name,
            "fund": fund,
            "comment": comment,
            "date": str(datetime.strptime(date, "%d.%m.%Y")),
            "total": total,
            "currency": currency,
            "taxFree": tax_free == "TRUE",
            "treasuryBalance": treasury_balance,
        }

        db_rows.append(db_row)

    db = SingletonClient.get_data_base()

    # Удаляются все данные из коллекции
    delete_result = await db.transactions.delete_many({})
    print('Update data. Delete transactions:\n' + str(delete_result.raw_result))

    # Таблица заполняется обновленным данными
    insert_result = await db.transactions.insert_many(db_rows)
    print('Update data. Insert transactions = ' +
          str(insert_result.inserted_ids))
