
from typing import List

import os
import time
import re

import aiohttp
from datetime import datetime
from calendar import monthrange
from PIL import Image, ImageDraw, ImageFont

from motor_client import SingletonClient
from loop import loop
from bot import types
from loguru import logger

GOOGLE_SHEETS_API_KEY = os.environ['GOOGLE_SHEETS_API_KEY']
GOOGLE_SHEETS_SPREADSHEET_ID = os.environ['GOOGLE_SHEETS_SPREADSHEET_ID']

GOOGLE_SHEETS_BASE_URL = 'https://sheets.googleapis.com/v4/spreadsheets'


async def google_sheets_values(
        sheet: str,
        start: str = 'A1',
        stop: str = 'ZZ99999',
        value_render_option: str = 'UNFORMATTED_VALUE',
        date_time_render_option: str = 'FORMATTED_STRING',
) -> dict:

    range_ = '!'.join([
        sheet,
        ':'.join([start, stop, ]),
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
            logger.info('google sheets values response: {}'.format(str(json)))
            return json.get('values', [])


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

    string += f'\n<a href="{os.environ["DONATE_LINK"]}">Задонатить</a>'
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
    # Временное решение, надо нормально проверять и экспетить ошибку с неправильным данными
    just_sum = int(just_sum)
    goal = int(goal)

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
    draw.text((22, 68), fund_name, fill='#ffffff', font=font_title)

    draw.text((22, 185), beauty_sum(just_sum),
              fill='#ffffff', font=font_digitals)
    draw.text((355, 185), beauty_sum(goal) + '₽',
              fill='#ffffff', font=font_digitals)

    # Отрисовка прогресс бара
    width = 16 + int(just_sum / goal * 467)

    draw.rectangle([16, 141, width, 168], fill='#c1a66f')

    img.save(out_file)
    return out_file


def normalize_fund_title(fund_title: str) -> str:
    if not fund_title.startswith('#'):
        return '#' + fund_title.lower()
    return fund_title


async def choose_default_fund(
        preffered_default_funds: List[str] = ['#офис', '#выборы']
) -> str:
    """
    Выбирает фонд по умолчанию.
    Первый из `preffered_default_funds` или, если он не находится, то произвольный.
    """
    db = SingletonClient.get_data_base()

    preffered_settings_fund = await db.settings.find_one({'id': 0})
    if preffered_settings_fund:
        preffered_default_funds = [
            preffered_settings_fund.get('preffered_fund')]

    funds = await google_sheets_values('lprtreasurybot.funds', 'B1', 'B99999')
    funds = {fund[0] for fund in funds}

    for preffered_default_fund in preffered_default_funds:
        if preffered_default_fund in funds:
            return preffered_default_fund

    return funds.pop()


async def fund_sum(fund_title: str) -> [int, int]:
    """
    Парсит количество денег в фонде
    :param fund_title:
    :return:
    """
    fund_title = normalize_fund_title(fund_title)

    fund_goals = await google_sheets_values('lprtreasurybot.fund_goals', 'A1', 'C99999')

    for [balance, fund, goal] in fund_goals:
        if fund == fund_title:
            return [balance, goal]

    funds = await google_sheets_values('lprtreasurybot.funds', 'A1', 'B99999')

    for [balance, fund] in funds:
        if fund == fund_title:
            return [balance, 0]


async def rating_string(
        month: str = time.strftime("%m"),
        year: str = time.strftime("%y"),
        to_month: str = None,
        to_year: str = None,
        fund: str = None) -> str:

    """
    builds rating string which contains list of donaters

    Args:
        month (datetime): initial month
        year (datetime): initial year
        to_month (datetime): end month
        to_year (datetime): end year
        fund (str): fund name

    Returns:
        str: message which ready to send to user
    """

    if to_month is None and to_year is None:
        to_month, to_year = month, year
    year = '20' + year
    to_year = '20' + to_year

    # Сделать импорт нужных данных из монго
    db = SingletonClient.get_data_base()
    collection = db.transactions
    if fund:
        cursor = collection.find({
            "fund": normalize_fund_title(fund)
        })

    else:
        cursor = collection.find({
            "date": {
                "$gte": str(datetime.strptime("01 {} {}".format(month, year), "%d %m %Y")),
                "$lte": str(
                    datetime.strptime("{} {} {}".format(
                        monthrange(int(to_year), int(to_month))[1],
                        to_month,
                        to_year), "%d %m %Y")
                )
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

    logger.info(dct)
    list_d = list(dct.items())
    list_d.sort(key=lambda j: j[1], reverse=True)
    list_d = list_d[:10]

    string = 'Топ 10 жертвователей '
    string += f'фонда {fund}' if fund else ''
    string += f'за {month}.{year}' if fund is None else ''
    string += f'-{to_month}.{to_year}' if (to_month !=
                                           month or to_year != year) else ''

    string += ':\n'

    for i in range(len(list_d)):
        if list_d[i][0].startswith('@'):
            string += '{}) <a href="https://t.me/{nickname}">{mention}</a> - <b>{sum}</b> ₽\n'.format(
                i + 1, nickname=list_d[i][0][1:], mention=list_d[i][0], sum=beauty_sum(list_d[i][1]))
        else:
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
            "fund": fund.lower(),
            "comment": comment,
            "date": str(datetime.strptime(date, "%d.%m.%Y")),
            "total": total,
            "currency": currency,
            "taxFree": tax_free == "TRUE",
            "treasuryBalance": treasury_balance,
            "timestamp": datetime.strptime(date, "%d.%m.%Y").timestamp()
        }

        db_rows.append(db_row)

    db = SingletonClient.get_data_base()

    # Удаляются все данные из коллекции
    delete_result = await db.transactions.delete_many({})
    logger.info('Update data. Delete transactions:\n' + str(delete_result.raw_result))

    # Таблица заполняется обновленным данными
    insert_result = await db.transactions.insert_many(db_rows)
    logger.info('Update data. Insert transactions = ' +
          str(insert_result.inserted_ids))
