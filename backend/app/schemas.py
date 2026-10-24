from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

# User Schemas
class UserBase(BaseModel):
    id: int
    first_name: Optional[str] = None
    username: Optional[str] = None
    hourly_rate: Optional[float] = 25000.0

class UserResponse(UserBase):
    created_at: datetime
    class Config:
        from_attributes = True

# Transaction Schemas
class TransactionCreate(BaseModel):
    user_id: int
    type: str = Field(..., description="'income', 'expense', 'unknown_loss', 'loan_payment', 'goal_deposit'")
    category: Optional[str] = "other"  # 'food', 'transport', 'small', 'home', 'habits', 'other'
    amount: float = Field(..., gt=0)
    raw_expression: Optional[str] = None
    note: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    type: str
    category: str
    amount: float
    raw_expression: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Loan Schemas
class LoanCreate(BaseModel):
    user_id: int
    title: str
    total_amount: float
    monthly_payment: float
    remaining_amount: Optional[float] = None
    due_day: Optional[int] = 20

class LoanPayment(BaseModel):
    amount: float
    note: Optional[str] = None

class LoanResponse(BaseModel):
    id: int
    user_id: int
    title: str
    total_amount: float
    monthly_payment: float
    remaining_amount: float
    due_day: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Goal Schemas
class GoalCreate(BaseModel):
    user_id: int
    title: str
    target_amount: float

class GoalDeposit(BaseModel):
    amount: float

class GoalResponse(BaseModel):
    id: int
    user_id: int
    title: str
    target_amount: float
    current_amount: float
    is_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Mystery Loss / Black Hole Check
class MysteryLossCreate(BaseModel):
    user_id: int
    expected_amount: float
    actual_amount: float
    note: Optional[str] = "Hisobdagi va cho'ntakdagi pul farqi"

# Dashboard & Analytics
class DailyBalance(BaseModel):
    today_income: float
    today_expense: float
    daily_loan_reserve: float
    safe_free_balance: float
    unknown_loss_today: float

class MonthlyAnalytics(BaseModel):
    month_name: str
    total_income: float
    total_expense: float
    total_loans_paid: float
    mystery_loss_total: float
    small_expenses_total: float
    category_breakdown: Dict[str, float]
    work_hours_spent: float  # Total expenses converted into labor hours
