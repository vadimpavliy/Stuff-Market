from datetime import datetime

import base64
import hashlib

import aiohttp
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import CommandStart

import app.keyboards as kb
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.requests import (
    set_user,
    set_basket,
    get_basket,
    get_item_by_id,
    delete_basket,
    create_order,
)
from config import SHOP_ID, SECRET_KEY

router = Router()


async def create_payment(amount, description):
    url = "https://api.yookassa.ru/v3/payments"

    # Формируем Basic Auth
    auth_string = f"{SHOP_ID}:{SECRET_KEY}"
    auth_bytes = auth_string.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    idempotence_key = hashlib.sha256(f"{amount}{description}{datetime.now()}".encode()).hexdigest()[:64]
    headers = {
        "Authorization": f"Basic {base64_auth}",
        "Idempotence-Key": idempotence_key,
        "Content-Type": "application/json"
    }

    payload = {
        "amount": {
            "value": f"{amount:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/murzik_market_bot"
        },
        "capture": False,
        "description": description[:128]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()

                if response.status == 200:
                    return data
                else:
                    error_msg = data.get('description', 'Неизвестная ошибка')
                    raise Exception(f"Ошибка ЮKassa: {error_msg} (код: {data.get('code', 'unknown')})")

    except Exception as e:
        raise Exception(f"Ошибка при выполнении запроса: {str(e)}")


@router.message(CommandStart())
@router.callback_query(F.data == 'to_main')
async def cmd_start(message: Message | CallbackQuery):
    if isinstance(message, Message):
        await set_user(message.from_user.id)
        await message.answer("Добро пожаловать в интернет магазин!",
                             reply_markup=kb.main)
    else:
        await message.answer('Вы вернулись на главную')
        await message.message.answer("Добро пожаловать в интернет магазин!",
                                     reply_markup=kb.main)


@router.callback_query(F.data == 'catalog')
async def catalog(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text(text='Выберите категорию.',
                                     reply_markup=await kb.categories())


@router.callback_query(F.data.startswith('category_'))
async def category(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Выберите товар',
                                     reply_markup=await kb.items(callback.data.split('_')[1]))


@router.callback_query(F.data.startswith('item_'))
async def item_(callback: CallbackQuery):
    item = await get_item_by_id(callback.data.split('_')[1])
    await callback.answer('')
    await callback.message.answer_photo(photo=item.photo,
                                        caption=f'{item.name}\n\n{item.description}\n\nЦена: {item.price} рублей',
                                        reply_markup=await kb.basket(item.id))


@router.callback_query(F.data.startswith('order_'))
async def basket(callback: CallbackQuery):
    await set_basket(callback.from_user.id, callback.data.split('_')[1])
    await callback.answer('Товар добавлен в корзину')


@router.callback_query(F.data == 'mybasket')
async def mybasket(callback: CallbackQuery):
    await callback.answer('')
    basket_items = await get_basket(callback.from_user.id)

    if not basket_items:
        await callback.message.answer('🛒 Ваша корзина пуста')
        return

    total_amount = 0

    for basket, item in basket_items:
        await callback.message.answer_photo(
            photo=item.photo,
            caption=f'📦 {item.name}\n\n{item.description}\n\n💰 Цена: {item.price} руб.',
            reply_markup=await kb.delete_from_basket(basket.id)
        )
        total_amount += item.price

    await callback.message.answer(
        f"💳 Итого к оплате: {total_amount} руб.",
        reply_markup=await kb.pay_button()
    )


@router.callback_query(F.data == 'pay')
async def process_payment(callback: CallbackQuery):
    try:
        await callback.answer('Подготовка платежа...')
        basket_items = await get_basket(callback.from_user.id)

        if not basket_items:
            await callback.message.answer("Ваша корзина пуста!")
            return

        total_amount = sum(item.price for basket, item in basket_items)
        description = "Оплата товаров в корзине"

        # Создаем платеж
        payment = await create_payment(total_amount, description)

        if payment and 'confirmation' in payment:
            payment_url = payment['confirmation']['confirmation_url']
            payment_id = payment['id']

            await create_order(
                user_id=callback.from_user.id,
                items=basket_items,
                total=total_amount,
                payment_id=payment_id
            )

            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(
                text="Перейти к оплате",
                url=payment_url
            ))
            builder.add(InlineKeyboardButton(
                text="Я оплатил",
                callback_data="payment_confirmed"
            ))

            await callback.message.answer(
                f"Сумма к оплате: {total_amount} рублей\n"
                "Нажмите кнопку ниже для перехода к оплате или подтвердите, что вы оплатили:",
                reply_markup=builder.as_markup()
            )
        else:
            await callback.message.answer("Ошибка при создании платежа")

    except Exception as e:
        await callback.message.answer("Произошла ошибка при обработке платежа")
        print(f"Payment error: {str(e)}")


@router.callback_query(F.data == 'payment_confirmed')
async def confirm_payment(callback: CallbackQuery):
    await callback.answer("Спасибо за подтверждение!")
    await callback.message.answer("Спасибо за покупку!\nМенеджер свяжется с вами.")

    await delete_basket_for_user(callback.from_user.id)


async def delete_basket_for_user(user_id: int):
    basket_items = await get_basket(user_id)
    for basket, item in basket_items:
        await delete_basket(basket.id)


@router.callback_query(F.data.startswith('delete_'))
async def delete_from_basket(callback: CallbackQuery):
    basket_id = int(callback.data.split('_')[1])
    await delete_basket(basket_id)
    await callback.message.delete()
    await callback.answer('Товар удален из корзины')
