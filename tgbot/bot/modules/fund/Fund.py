from bot import dp, types
from defs import parse_command, normalize_fund_title, choose_default_fund, fund_sum, fund_string, get_fund_image


async def send_fund(message, fund_total, fund_title, fund_goal):
    fund_title = fund_title[1:]

    if fund_goal == 0:
        await message.reply(fund_string(fund_total, fund_title, fund_goal), parse_mode='HTML', disable_web_page_preview=True)
    else:
        image_path = get_fund_image(fund_total, fund_title, fund_goal)
        await message.reply_photo(types.InputFile(image_path), parse_mode='HTML')


@dp.message_handler(commands=['fund'])
async def fund(message: types.Message):
    text_parts = message.text.split()

    fund = None
    if len(text_parts) == 1:
        fund_title = await choose_default_fund()
        fund = await fund_sum(fund_title)
    else:
        fund_title = normalize_fund_title(text_parts[1])
        fund = await fund_sum(fund_title)

    if fund:
        fund_total, fund_goal = fund
        await send_fund(message, fund_total, fund_title, fund_goal)
    else:
        await message.reply('Фонд не найден', parse_mode='HTML')
