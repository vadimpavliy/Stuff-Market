import json

from typing import List, Tuple

from app.database.models import User, Category, Item, Basket, Order
from app.database.models import async_session

from sqlalchemy import select, update, delete


async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()


async def set_item(data):
    async with async_session() as session:
        session.add(Item(**data))
        await session.commit()


async def set_basket(tg_id, item_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        session.add(Basket(user=user.id, item=item_id))
        await session.commit()


async def get_basket(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return []

        result = await session.execute(
            select(Basket, Item)
            .join(Item, Basket.item == Item.id)
            .where(Basket.user == user.id)
        )
        return result.all()


async def get_users():
    async with async_session() as session:
        users = await session.scalars(select(User))
        return users


async def get_categories():
    async with async_session() as session:
        categories = await session.scalars(select(Category))
        return categories


async def get_items_by_category(category_id: int):
    async with async_session() as session:
        items = await session.scalars(select(Item).where(Item.category == category_id))
        return items


async def get_item_by_id(item_id: int):
    async with async_session() as session:
        item = await session.scalar(select(Item).where(Item.id == item_id))
        return item


async def delete_basket(basket_id: int):
    async with async_session() as session:
        await session.execute(
            delete(Basket).where(Basket.id == basket_id)
        )
        await session.commit()


async def create_order(user_id: int, items: List[Tuple[int, int]], total: int, payment_id: str) -> Order:
    async with async_session() as session:
        # Преобразуем товары в JSON строку
        items_json = json.dumps([{"item_id": item.id, "price": item.price} for basket, item in items])

        order = Order(
            user=user_id,
            items=items_json,
            total=total,
            payment_id=payment_id,
            status='pending'
        )

        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order


async def update_order_status(payment_id: str, status: str):
    async with async_session() as session:
        order = await session.execute(select(Order).where(Order.payment_id == payment_id))
        order = order.scalar_one_or_none()

        if order:
            order.status = status
            await session.commit()
    async with async_session() as session:
        order = await session.execute(select(Order).where(Order.payment_id == payment_id))
        order = order.scalar_one_or_none()

        if order:
            await session.execute(delete(Basket).where(Basket.user == order.user))
            await session.commit()


async def clear_basket(user_id: int):
    async with async_session() as session:
        await session.execute(delete(Basket).where(Basket.user == user_id))
        await session.commit()


async def check_order(order_id):
    async with async_session() as session:
        return await session.get(Order, order_id)
