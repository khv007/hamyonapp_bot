from datetime import datetime, date, time
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Transaction, Loan, Goal
from app.schemas import (
    TransactionCreate, LoanCreate, LoanPayment, 
    GoalCreate, GoalDeposit, DailyBalance, MonthlyAnalytics
)

# User operations
async def get_or_create_user(session: AsyncSession, user_id: int, first_name: str = None, username: str = None) -> User:
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        user = User(id=user_id, first_name=first_name, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user

async def update_user_hourly_rate(session: AsyncSession, user_id: int, rate: float) -> User:
    user = await session.get(User, user_id)
    if user:
        user.hourly_rate = rate
        await session.commit()
        await session.refresh(user)
    return user

# Transaction operations
async def create_transaction(session: AsyncSession, data: TransactionCreate) -> Transaction:
    # Ensure user exists
    await get_or_create_user(session, data.user_id)
    
    tx = Transaction(
        user_id=data.user_id,
        type=data.type,
        category=data.category or "other",
        amount=data.amount,
        raw_expression=data.raw_expression,
        note=data.note
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    return tx

async def get_user_transactions(session: AsyncSession, user_id: int, limit: int = 50, offset: int = 0):
    stmt = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return result.scalars().all()

async def delete_transaction(session: AsyncSession, user_id: int, tx_id: int) -> bool:
    stmt = select(Transaction).where(and_(Transaction.id == tx_id, Transaction.user_id == user_id))
    result = await session.execute(stmt)
    tx = result.scalar_one_or_none()
    if tx:
        await session.delete(tx)
        await session.commit()
        return True
    return False

# Loans operations
async def create_loan(session: AsyncSession, data: LoanCreate) -> Loan:
    await get_or_create_user(session, data.user_id)
    rem = data.remaining_amount if data.remaining_amount is not None else data.total_amount
    loan = Loan(
        user_id=data.user_id,
        title=data.title,
        total_amount=data.total_amount,
        monthly_payment=data.monthly_payment,
        remaining_amount=rem,
        due_day=data.due_day or 20,
        is_active=True
    )
    session.add(loan)
    await session.commit()
    await session.refresh(loan)
    return loan

async def get_user_loans(session: AsyncSession, user_id: int):
    stmt = select(Loan).where(Loan.user_id == user_id).order_by(Loan.is_active.desc(), Loan.due_day.asc())
    result = await session.execute(stmt)
    return result.scalars().all()

async def pay_loan(session: AsyncSession, user_id: int, loan_id: int, payment: LoanPayment) -> Loan:
    stmt = select(Loan).where(and_(Loan.id == loan_id, Loan.user_id == user_id))
    result = await session.execute(stmt)
    loan = result.scalar_one_or_none()
    if not loan:
        return None
    
    loan.remaining_amount = max(0.0, loan.remaining_amount - payment.amount)
    if loan.remaining_amount == 0.0:
        loan.is_active = False

    # Also log this as a loan_payment transaction
    tx = Transaction(
        user_id=user_id,
        type="loan_payment",
        category="loan",
        amount=payment.amount,
        note=f"{loan.title} kredit to'lovi" + (f": {payment.note}" if payment.note else "")
    )
    session.add(tx)
    await session.commit()
    await session.refresh(loan)
    return loan

async def delete_loan(session: AsyncSession, user_id: int, loan_id: int) -> bool:
    stmt = select(Loan).where(and_(Loan.id == loan_id, Loan.user_id == user_id))
    result = await session.execute(stmt)
    loan = result.scalar_one_or_none()
    if loan:
        await session.delete(loan)
        await session.commit()
        return True
    return False

# Goals operations
async def create_goal(session: AsyncSession, data: GoalCreate) -> Goal:
    await get_or_create_user(session, data.user_id)
    goal = Goal(
        user_id=data.user_id,
        title=data.title,
        target_amount=data.target_amount,
        current_amount=0.0
    )
    session.add(goal)
    await session.commit()
    await session.refresh(goal)
    return goal

async def get_user_goals(session: AsyncSession, user_id: int):
    stmt = select(Goal).where(Goal.user_id == user_id).order_by(Goal.is_completed.asc(), Goal.created_at.desc())
    result = await session.execute(stmt)
    return result.scalars().all()

async def deposit_goal(session: AsyncSession, user_id: int, goal_id: int, dep: GoalDeposit) -> Goal:
    stmt = select(Goal).where(and_(Goal.id == goal_id, Goal.user_id == user_id))
    result = await session.execute(stmt)
    goal = result.scalar_one_or_none()
    if not goal:
        return None
    
    goal.current_amount += dep.amount
    if goal.current_amount >= goal.target_amount:
        goal.is_completed = True

    tx = Transaction(
        user_id=user_id,
        type="goal_deposit",
        category="savings",
        amount=dep.amount,
        note=f"{goal.title} maqsadiga jamg'arma"
    )
    session.add(tx)
    await session.commit()
    await session.refresh(goal)
    return goal

# Daily summary & calculations
async def get_daily_balance(session: AsyncSession, user_id: int) -> DailyBalance:
    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)
    
    stmt = select(Transaction).where(
        and_(
            Transaction.user_id == user_id,
            Transaction.created_at >= today_start,
            Transaction.created_at <= today_end
        )
    )
    res = await session.execute(stmt)
    today_txs = res.scalars().all()
    
    income = sum(t.amount for t in today_txs if t.type == "income")
    expenses = sum(t.amount for t in today_txs if t.type in ["expense", "loan_payment", "goal_deposit"])
    unknown_loss = sum(t.amount for t in today_txs if t.type == "unknown_loss")
    
    # Active loans daily reserve = total monthly payments / 30
    loans_stmt = select(func.sum(Loan.monthly_payment)).where(
        and_(Loan.user_id == user_id, Loan.is_active == True)
    )
    loans_res = await session.execute(loans_stmt)
    monthly_loans_sum = loans_res.scalar() or 0.0
    daily_loan_reserve = round(monthly_loans_sum / 30.0, 2)
    
    # Safe balance = today income - today expense - daily loan reserve - unknown loss
    safe_free = income - expenses - daily_loan_reserve - unknown_loss
    
    return DailyBalance(
        today_income=income,
        today_expense=expenses,
        daily_loan_reserve=daily_loan_reserve,
        safe_free_balance=safe_free,
        unknown_loss_today=unknown_loss
    )

# Mystery loss (Black hole check)
async def log_mystery_loss(session: AsyncSession, user_id: int, expected: float, actual: float, note: str = None) -> Transaction:
    diff = expected - actual
    if diff <= 0:
        return None
    
    tx = Transaction(
        user_id=user_id,
        type="unknown_loss",
        category="unknown",
        amount=diff,
        note=note or f"Cho'ntakda {expected:,.0f} bo'lishi kerak edi, lekin {actual:,.0f} qolgan (yo'qolgan: {diff:,.0f})"
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    return tx

# Monthly Analytics
async def get_monthly_analytics(session: AsyncSession, user_id: int, year: int = None, month: int = None) -> MonthlyAnalytics:
    now = datetime.now()
    y = year or now.year
    m = month or now.month
    
    # Start of month
    start_dt = datetime(y, m, 1, 0, 0, 0)
    # End of month
    if m == 12:
        end_dt = datetime(y + 1, 1, 1, 0, 0, 0)
    else:
        end_dt = datetime(y, m + 1, 1, 0, 0, 0)
        
    stmt = select(Transaction).where(
        and_(
            Transaction.user_id == user_id,
            Transaction.created_at >= start_dt,
            Transaction.created_at < end_dt
        )
    )
    res = await session.execute(stmt)
    txs = res.scalars().all()
    
    user = await session.get(User, user_id)
    hourly_rate = user.hourly_rate if user and user.hourly_rate > 0 else 25000.0
    
    tot_income = 0.0
    tot_expense = 0.0
    tot_loans = 0.0
    mystery_loss = 0.0
    small_expenses = 0.0
    categories = {}
    
    for t in txs:
        if t.type == "income":
            tot_income += t.amount
        elif t.type == "expense":
            tot_expense += t.amount
            categories[t.category] = categories.get(t.category, 0.0) + t.amount
            if t.category == "small" or t.amount <= 20000.0:
                small_expenses += t.amount
        elif t.type == "loan_payment":
            tot_loans += t.amount
            tot_expense += t.amount
        elif t.type == "unknown_loss":
            mystery_loss += t.amount
            tot_expense += t.amount
            
    # Labor hours spent: total expenses / hourly rate
    work_hours = round(tot_expense / hourly_rate, 1)
    
    month_names = [
        "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
        "Iyul", "Avgust", "Sentabr", "Oktyabr", "Noyabr", "Dekabr"
    ]
    
    return MonthlyAnalytics(
        month_name=f"{month_names[m - 1]} {y}",
        total_income=tot_income,
        total_expense=tot_expense,
        total_loans_paid=tot_loans,
        mystery_loss_total=mystery_loss,
        small_expenses_total=small_expenses,
        category_breakdown=categories,
        work_hours_spent=work_hours
    )
