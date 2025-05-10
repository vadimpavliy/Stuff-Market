from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

import app.keyboards as kb
from app.database.requests import set_user, get_item

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await set_user(message.from_user.id)
    await message.answer('Добро пожаловать в IT Shop!',
                         reply_markup=kb.menu)


@router.callback_query(F.data == 'start')
async def callback_start(callback:  CallbackQuery):
    await callback.answer('Вы вернулись на главное меню')
    await callback.message.edit_text('Добро пожаловать в IT shop!',
                                     reply_markup=kb.menu)


@router.callback_query(F.data == 'catalog')
async def catalog(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Выберите категорию товара',
                                     reply_markup=await kb.categoriess)


@router.callback_query(F.data.startswith('category_'))
async def category(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Выберите товар по категории',
                                     reply_markup=await kb.get_items(callback.data.split('_')[1]))


@router.callback_query(F.data.startswith('item_'))
async def item_handler(callback: CallbackQuery):
    item = await get_item(callback.data.split('_')[1])
    await callback.answer()
    await callback.message.answer(f'{item.name}\n\nЦена: {item.price}',
                                  reply_markup=await kb.back_to_category(item.category))