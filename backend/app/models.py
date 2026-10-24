from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)  # Telegram User ID
    first_name = Column(String(128), nullable=True)
    username = Column(String(128), nullable=True)
    hourly_rate = Column(Float, default=25000.0)  # Average 1 hour labor value in UZS
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    loans = relationship("Loan", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True, nullable=False)
    
    # 'income', 'expense', 'unknown_loss' (qora tuynuk), 'loan_payment', 'goal_deposit'
    type = Column(String(32), nullable=False, index=True)
    
    # 'food' (tushlik), 'transport' (yo'l), 'small' (mayda-chuyda), 'home' (uy/ro'zg'or), 'other', etc.
    category = Column(String(64), default="other")
    
    amount = Column(Float, nullable=False)
    raw_expression = Column(String(128), nullable=True)  # e.g., "15000+20000"
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="transactions")

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True, nullable=False)
    
    title = Column(String(128), nullable=False)  # e.g. "Uzum Nasiya (Telefon)", "Bank Mikroqarz"
    total_amount = Column(Float, nullable=False)
    monthly_payment = Column(Float, nullable=False)  # Oylik to'lov
    remaining_amount = Column(Float, nullable=False)  # Qolgan qarz
    due_day = Column(Integer, default=20)  # Har oyning qaysi sanasida to'lanadi (1-31)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="loans")

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True, nullable=False)
    
    title = Column(String(128), nullable=False)  # e.g. "Yangi telefon", "Qishki kiyim"
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="goals")
