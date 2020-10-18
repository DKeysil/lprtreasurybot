from bot import dp, types, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from bot.modules.transactions.Transactions import transactions
from bot.modules.menu.Menu import menu
from defs import google_sheets_values


class Settings(StatesGroup):
    await_mention = State()


@dp.message_handler(lambda message: message.chat.type == 'private' and message.text == 'Транзакции')
async def transactions_menu(message: types.Message):
    """
    Let user send mention of donater or choose in menu

    Args:
        message (types.Message): telegram message
    """

    # button if user want to check his transactions
    author_mention = types.KeyboardButton(message.from_user.mention)
    funds = await google_sheets_values('lprtreasurybot.funds', 'A1', 'B99999')

    funds = [i[1].lower() for i in funds if int(i[0]) != 0]
    btn_list = [[author_mention], funds[0:3]]
    menu_keyboard_markup = types.ReplyKeyboardMarkup(btn_list)
    await Settings.await_mention.set()
    await message.answer('Пришлите ник или имя донатера.', reply_markup=menu_keyboard_markup)


@dp.message_handler(state=Settings.await_mention)
async def get_mention(message: types.Message, state: FSMContext):
    """
    Ожидает ник или имя донатера, для которого будет возвращен список транзанкций
    """
    mention = message.text

    if len(mention) > 32:
        return await message.reply('Указанное имя слишком длинное')
    mention = mention.lower()
    await state.finish()
    await menu(message)
    await transactions(message, parameter=mention)
