from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types
import sqlite3 as sq

token = ''
storage = MemoryStorage()
admin_id= 290662407


base = sq.connect('spisok.db')
cur = base.cursor()
print('db connected OK!')
base.execute('CREATE TABLE IF NOT EXISTS spisok (city TEXT ,phone TEXT)')
base.commit()

bot = Bot(token=token)
dp = Dispatcher(bot, storage=storage)
b1 = KeyboardButton('/список')
b2 = KeyboardButton('/добавить')
b3 = KeyboardButton('/удалить')
b4 = KeyboardButton('/города')
kb_admin  = ReplyKeyboardMarkup(resize_keyboard=True)
kb_admin.add(b1).add(b2).add(b3)
kb_user= ReplyKeyboardMarkup(resize_keyboard=True)
kb_user.add(b4)



@dp.message_handler(commands=['start'])
async def commands_start(message: types.Message):
    await message.answer(f'приветствую тебя, @{message.from_user.id}.нажми /help чтобы узнать что я могу',reply_markup=kb_user)


@dp.message_handler(commands=['help'])
async def commands_help(message: types.Message):
    await message.answer(
        f'а я бот справочник и могу тебе показать телефоны и города рекламных агенств для этого сейчас появится клавиаутура для ввода команд',
        reply_markup=kb_admin)

#добавление города
class FSMAdmin(StatesGroup):
    city = State()
    phone = State()
    dcity = State()

@dp.message_handler(commands='Добавить', state=None)
async def add(message: types.Message):
    if message.from_user.id!=admin_id:
        #await bot.answer_callback_query(callback_query_id=cmd.id, text="нет доступа", show_alert=True)
        await bot.send_message(message.from_user.id,'доступ запрещен')
    else:
        await FSMAdmin.city.set()
        await message.reply('Введи название города')



@dp.message_handler( state=FSMAdmin.city)
async def add_city(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['city'] = message.text.lower()
        await FSMAdmin.next()
        await message.reply('Введите телефон')


@dp.message_handler(state=FSMAdmin.phone)
async def add_phone(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone'] = message.text
    async with state.proxy() as data:
        city = data['city']
        phone = data['phone']
    cur.execute('INSERT INTO spisok VALUES(?,?);',(city,phone))
    base.commit()
    await message.reply(f'вы добавили город: {city} и номер {phone}')
    await state.finish()
#Удаление города
class FSMAdmin1(StatesGroup):
    city = State()
@dp.message_handler(commands="удалить", state=None)
async def dl(message: types.Message):
    await FSMAdmin1.city.set()
    await message.reply('Введи название города')

@dp.message_handler(state=FSMAdmin1.city)
async def del_city(message:types.Message, state=FSMContext):
    async with state.proxy() as data:
        data["city"]=message.text
    async with state.proxy() as data:
        dcity = data['city']
    cur.execute('DELETE FROM spisok WHERE city=?',(dcity,))
    base.commit()
    await message.reply(f'вы удалили запись: {dcity}')
    await state.finish()

#выведение списка с телефонами
@dp.message_handler(commands="список")
async def sql_read(message):
    for ret in cur.execute('SELECT* FROM spisok').fetchall():
        await bot.send_message(message.from_user.id,f'{ret[0]} {ret[1]}')
#выведение списка
@dp.message_handler(commands="города")
async def sql_read(message):
    for ret in cur.execute('SELECT city FROM spisok').fetchall():
        await bot.send_message(message.from_user.id,f'{ret[0]}')

#поиск города
@dp.message_handler()
async def find_city(message: types.Message):
    cur.execute('SELECT* FROM spisok WHERE city=?',(message.text.lower(),))
    if cur.fetchone() is None:
        await bot.send_message(message.from_user.id,'нет такого города')
    else:
        for cit in cur.execute('SELECT*FROM spisok WHERE city=?',(message.text.lower(),)).fetchone():
            await bot.send_message(message.from_user.id,cit)




@dp.message_handler()
async def echo_send(message: types.Message):
    await message.answer(message.text)


executor.start_polling(dp, skip_updates=True)
