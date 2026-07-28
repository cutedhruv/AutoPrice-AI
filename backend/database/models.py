"""Database models for AutoPrice AI"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, default="")
    image_url = Column(String(500), default="")
    our_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    competitor_price = Column(Float, nullable=False)
    stock = Column(Integer, default=100)
    demand_score = Column(Float, default=0.5)  # 0-1 scale
    rating = Column(Float, default=4.0)
    reviews_count = Column(Integer, default=0)
    brand = Column(String(100), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, nullable=False)
    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    competitor_price = Column(Float, nullable=False)
    reason = Column(Text, default="")
    agent_name = Column(String(100), default="")
    profit_margin = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(100), nullable=False)
    action = Column(String(200), nullable=False)
    details = Column(Text, default="")
    status = Column(String(50), default="completed")  # running, completed, error
    product_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(200), nullable=False)
    decision_type = Column(String(100), nullable=False)  # price_increase, price_decrease, no_change
    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    competitor_price = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    confidence = Column(Float, default=0.8)
    profit_impact = Column(Float, default=0.0)
    agent_chain = Column(Text, default="")  # JSON list of agents involved
    timestamp = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, nullable=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="info")  # info, warning, success, error
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
