from bot import dp
from bot import types
from bot import FSMContext
from bot.modules.menu.Menu import menu
from loguru import logger


@dp.message_handler(lambda message: message.chat.type == 'private', state='*', commands=['cancel'])
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    await menu(message)
    if current_state is None:
        return
    logger.info('handler cancelled')
    await state.finish()
