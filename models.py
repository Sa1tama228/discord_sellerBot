from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())

class Orders(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    client_price = Column(Float, nullable=False)
    client_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    item_to_give = Column(String, nullable=False)
    status = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())


class UnapprovedOrders(Base):
    __tablename__ = 'unapproved_orders'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    client_price = Column(Float, nullable=False)
    client_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    item_to_give = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())
