import logging
import sys

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.storage import FSMContextProxy
from aiogram.utils import executor

import config
from states import Form

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger("parkun_bot")

bot = Bot(token=config.BOT_TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


def get_keyboard_with_cancel(
        button: types.InlineKeyboardButton) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    cancel = types.InlineKeyboardButton(
        text='Отмена',
        callback_data='/cancel')

    keyboard.add(button, cancel)
    return keyboard


def get_cancel_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    cancel = types.InlineKeyboardButton(
        text='Отмена',
        callback_data='/cancel')

    keyboard.add(cancel)
    return keyboard


async def send_info_to_doctor(state: FSMContext, user_id: int):
    async with state.proxy() as data:
        text_to_chat = compose_summary(data)

    await bot.send_message(config.DOCTORS_GROUP,
                           text_to_chat,
                           parse_mode='HTML')

    text_to_user = 'Ваша заявка отправлена. ' +\
        'Специалист, свяжется с вами лично.' +\
        '\n\nДержитесь, друзья, вы невероятные!'

    await bot.send_message(user_id,
                           text_to_user,
                           parse_mode='HTML')


def compose_summary(data: FSMContextProxy):
    text = '#запрос\n'

    if good_man_name := data.get('good_man_name', ''):
        text += f'\nИмя заявителя: <b>{good_man_name}</b>'

    text += f'''
Имя пострадавшего: <b>{data.get('name', '')}</b>
Возраст/ДР: <b>{data.get('age', '')}</b>
Дата травм(ы): <b>{data.get('injury_date', '')}</b>
Травмы: <b>{data.get('injury_list', '')}</b>
Где находится пострадавший: <b>{data.get('location', '')}</b>
Связь: <b>{data.get('communication', '')}</b>
'''

    if questions := data.get('questions', ''):
        text + f'\nВопрос/комментарий: <b>{questions}</b>'

    return text


async def ask_for_victim_name(user_id: int):
    text = 'Укажите имя пострадавшего' +\
        '\n' +\
        '\n Пример: <b>Иван Иванов</b>'

    anon = types.InlineKeyboardButton(
        text='Аноним',
        callback_data='/anonymous')

    keyboard = get_keyboard_with_cancel(anon)

    await bot.send_message(user_id,
                           text,
                           reply_markup=keyboard,
                           parse_mode='HTML')


async def ask_for_age(user_id: int):
    text = 'Укажите дату рождения/возраст пострадавшего' +\
        '\n' +\
        '\n Пример: <b>15.08.2000, 20 лет</b>'

    keyboard = get_cancel_keyboard()

    await bot.send_message(user_id,
                           text,
                           reply_markup=keyboard,
                           parse_mode='HTML')


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """
    logger.info('Старт бота - ' + str(message.chat.id))
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    victim = types.InlineKeyboardButton(
        text='Я пострадавший',
        callback_data='/victim')

    good_man = types.InlineKeyboardButton(
        text='Я прошу помощи для другого человека',
        callback_data='/good_man')

    keyboard.add(victim, good_man)

    text = 'Добрый день!' +\
        '\n' +\
        '\nНажмите подходящую кнопку ниже, чтобы обратиться за помощью.'

    await bot.send_message(message.chat.id, text, reply_markup=keyboard)
    await Form.initial.set()


@dp.callback_query_handler(lambda call: call.data == '/victim',
                           state=Form.initial)
async def ask_victim_info(call, state: FSMContext):
    logger.info('Нажата кнопка ввода инфы пострадавшего - ' +
                str(call.message.chat.id))

    await bot.answer_callback_query(call.id)
    await ask_for_victim_name(call.message.chat.id)
    await Form.name.set()


@dp.callback_query_handler(lambda call: call.data == '/good_man',
                           state=Form.initial)
async def ask_good_man_info(call, state: FSMContext):
    logger.info('Нажата кнопка ввода инфы хорошего человека - ' +
                str(call.message.chat.id))

    await bot.answer_callback_query(call.id)
    text = 'Укажите ваше имя' +\
        '\n' +\
        '\n Пример: <b>Петр Петров</b>'

    anon = types.InlineKeyboardButton(
        text='Аноним',
        callback_data='/anonymous')

    keyboard = get_keyboard_with_cancel(anon)

    await bot.send_message(call.message.chat.id,
                           text,
                           reply_markup=keyboard,
                           parse_mode='HTML')

    await Form.good_man_name.set()


@dp.callback_query_handler(lambda call: call.data == '/anonymous',
                           state=Form.good_man_name)
async def good_man_is_anonymous(call, state: FSMContext):
    logger.info('Хороший человек имя аноним - ' + str(call.message.chat.id))
    await bot.answer_callback_query(call.id)
    await state.update_data(good_man_name='Аноним')

    await ask_for_victim_name(call.message.chat.id)
    await Form.next()


@dp.callback_query_handler(lambda call: call.data == '/anonymous',
                           state=Form.name)
async def victim_is_anonymous(call, state: FSMContext):
    logger.info('Пострадавший имя аноним - ' + str(call.message.chat.id))
    await bot.answer_callback_query(call.id)
    await state.update_data(name='Аноним')
    await ask_for_age(call.message.chat.id)
    await Form.next()


@dp.callback_query_handler(lambda call: call.data == '/skip',
                           state=Form.questions)
async def skip_questions(call, state: FSMContext):
    logger.info('Пропуск вопроса - ' + str(call.message.chat.id))
    await bot.answer_callback_query(call.id)
    await state.update_data(questions='')
    await send_info_to_doctor(state, call.message.chat.id)
    await state.finish()
    await cmd_start(call.message)


@dp.message_handler(content_types=types.ContentType.TEXT, state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    logger.info('Пострадавший имя - ' + str(message.chat.id))
    await state.update_data(name=message.text)
    await ask_for_age(message.chat.id)
    await Form.next()


@dp.message_handler(content_types=types.ContentType.TEXT,
                    state=Form.good_man_name)
async def process_good_man_name(message: types.Message, state: FSMContext):
    logger.info('Хороший чел имя - ' + str(message.chat.id))
    await state.update_data(good_man_name=message.text)
    await ask_for_victim_name(message.chat.id)
    await Form.next()


@dp.message_handler(content_types=types.ContentType.TEXT, state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    logger.info('Возраст - ' + str(message.chat.id))
    await state.update_data(age=message.text)

    text = 'Укажите дату травмы' +\
        '\n' +\
        '\n Пример: <b>11.08.2020</b>'

    keyboard = get_cancel_keyboard()

    await bot.send_message(message.chat.id,
                           text,
                           reply_markup=keyboard,
                           parse_mode='HTML')

    await Form.next()


@dp.message_handler(content_types=types.ContentType.TEXT,
                    state=Form.injury_date)
async def process_injury_date(message: types.Message, state: FSMContext):
    logger.info('Дата травмы - ' + str(message.chat.id))
    await state.update_data(injury_date=message.text)

    text = 'Перечислите полученные травмы' +\
        '\n' +\
        '\n Пример: <b>панические атаки, закрытый перелом руки, гематомы</b>'

    keyboard = get_cancel_keyboard()

    await bot.send_message(message.chat.id,
                           text,
                           reply_markup=keyboard,
                           parse_mode='HTML')

    await Form.next()


@dp.message_handler(content_types=types.ContentType.TEXT,
                    state=Form.injury_list)
async def process_injury_list(message: types.Message, state: FSMContext):
    logger.info('Список травм - ' + str(message.chat.id))
    await state.update_data(injury_list=message.text)

    text = 'Укажите, в каком населённом пункте находится пострадавший' +\
        '\n' +\
        '\n Пример: <b>Минск</b>'

    keyboard = get_cancel_keyboard()

    await bot.send_message(message.chat.id,
                           text,
                           reply_markup=keyboard,
                           parse_mode='HTML')

    await Form.next()


@dp.message_handler(content_types=types.ContentType.TEXT,
                    state=Form.location)
async def process_location(message: types.Message, state: FSMContext):
    logger.info('Локация - ' + str(message.chat.id))
    await state.update_data(location=message.text)

    text = 'Укажите, как с вами связаться (телефон или мессенджер)' +\
        '\n' +\
        '\n Пример: <b>+375291234567</b>' +\
        '\n Пример: <b>telegram @username</b>'

    keyboard = get_cancel_keyboard()

    await bot.send_message(message.chat.id,
                           text,
                           reply_markup=keyboard,
                           parse_mode='HTML')

    await Form.next()


@dp.message_handler(content_types=types.ContentType.TEXT,
                    state=Form.communication)
async def process_communication(message: types.Message, state: FSMContext):
    logger.info('Связь - ' + str(message.chat.id))
    await state.update_data(communication=message.text)

    text = 'Укажите дополнительные вопросы или комментарии.' +\
        '\n' +\
        '\n Введите вопрос или нажмите "Пропустить".'

    skip = types.InlineKeyboardButton(
        text='Пропустить',
        callback_data='/skip')

    keyboard = get_keyboard_with_cancel(skip)

    await bot.send_message(message.chat.id,
                           text,
                           reply_markup=keyboard,
                           parse_mode='HTML')

    await state.update_data(questions='')
    await Form.next()


@dp.message_handler(content_types=types.ContentType.TEXT,
                    state=Form.questions)
async def process_questions(message: types.Message, state: FSMContext):
    logger.info('Вопросы - ' + str(message.chat.id))
    await state.update_data(questions=message.text)
    await send_info_to_doctor(state, message.chat.id)
    await state.finish()
    await cmd_start(message)


@dp.callback_query_handler(lambda call: call.data == '/cancel', state='*')
async def cancel_input(call, state: FSMContext):
    logger.info('Возврат в начальный режим - ' + str(call.from_user.id))
    await bot.answer_callback_query(call.id)
    await state.finish()
    await cmd_start(call.message)


@dp.message_handler(content_types=types.ContentTypes.ANY, state=None)
async def no_state(message: types.Message, state: FSMContext):
    logger.info('Нет стейта - ' + str(message.from_user.id))
    await cmd_start(message)


@dp.message_handler(content_types=types.ContentTypes.ANY,
                    state=Form.initial)
async def ask_for_button_press(message: types.Message, state: FSMContext):
    logger.info('Нужно нажать на кнопку - ' + str(message.from_user.id))
    await cmd_start(message)


@dp.message_handler(content_types=types.ContentType.ANY, state='*')
async def only_text_allowed(message: types.Message, state: FSMContext):
    logger.info('Посылает не текст, а что-то другое - ' +
                str(message.from_user.id))

    text = 'Допускается только ввод текста.'
    await bot.send_message(message.chat.id, text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)