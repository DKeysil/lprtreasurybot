from bot import dp, types


def user_info_from_message(message: types.Message):
    if message and 'from' in message:
        str_ = 'This user info\n'
        if 'first_name' in message['from']:
            str_ += f'First name: {message["from"]["first_name"]}\n'
        if 'last_name' in message['from']:
            str_ += f'Last name: {message["from"]["last_name"]}\n'
        if 'username' in message['from']:
            str_ += f'Username: @{message["from"]["username"]}\n'
        if 'id' in message['from']:
            str_ += f'id: <code>{message["from"]["id"]}</code>\n'
        if message['chat']['id'] < 0:
            str_ += f'chat id:<code>{message["chat"]["id"]}</code>\n'
        return str_
    else:
        return ' '


@dp.message_handler(commands=['get_me'])
async def menu(message: types.Message):
    return await message.answer(user_info_from_message(message), parse_mode='html')
