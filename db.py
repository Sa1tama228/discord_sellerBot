from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Users, Orders, UnapprovedOrders
from sqlalchemy.future import select
from plugins import load

config = load()

engine = create_async_engine("sqlite+aiosqlite:///db.db", echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_user(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(Users).filter_by(id=user_id))
        return result.scalars().first()

async def create_user(user_id: int, username: str):
    async with async_session() as session:
        new_user = Users(id=user_id, username=username)
        session.add(new_user)
        await session.commit()

async def create_order(user_id: int, title: str, description: str, price: float, item_to_give: str):
    async with async_session() as session:
        new_order = Orders(client_id=user_id, title=title, description=description, client_price=price, item_to_give=item_to_give)
        session.add(new_order)
        await session.commit()

async def get_all_orders():
    async with async_session() as session:
        result = await session.execute(select(Orders))
        return result.scalars().all()

async def get_user_orders(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(Orders).filter_by(client_id=user_id))
        orders = result.scalars().all()
        print(f"DEBUG: orders fetched for user {user_id}: {orders}")  # Строка для отладки
        return orders

async def get_order_by_id(order_id: int):
    async with async_session() as session:
        result = await session.execute(select(Orders).filter_by(id=order_id))
        return result.scalars().first()


async def create_unapproved_order(user_id: int, title: str, description: str, price: float, item_to_give: str):
    async with async_session() as session:
        new_order = UnapprovedOrders(
            client_id=user_id,
            title=title,
            description=description,
            client_price=price,
            item_to_give=item_to_give
        )
        session.add(new_order)
        await session.commit()

        await session.refresh(new_order)
        return new_order

async def approve_order(order_id: int):
    async with async_session() as session:
        order = await session.get(UnapprovedOrders, order_id)
        if order:
            approved_order = Orders(
                title=order.title,
                description=order.description,
                client_price=order.client_price,
                client_id=order.client_id,
                item_to_give=order.item_to_give
            )
            session.add(approved_order)
            await session.delete(order)
            await session.commit()

async def reject_order(order_id: int):
    async with async_session() as session:
        order = await session.get(UnapprovedOrders, order_id)
        if order:
            await session.delete(order)
            await session.commit()

async def get_all_unapproved_orders():
    async with async_session() as session:
        result = await session.execute(select(UnapprovedOrders))
        return result.scalars().all()
