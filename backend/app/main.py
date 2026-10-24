import os
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Query, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from app.config import settings
from app.database import init_db, get_db
from app.models import User
from app.schemas import (
    TransactionCreate, TransactionResponse,
    LoanCreate, LoanPayment, LoanResponse,
    GoalCreate, GoalDeposit, GoalResponse,
    MysteryLossCreate, DailyBalance, MonthlyAnalytics
)
import app.crud as crud
from app.exports import generate_pdf_report, generate_excel_report
from app.bot import bot, dp

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables (PostgreSQL or fallback)
    await init_db()
    
    # Start bot polling in background if token is configured
    bot_task = None
    if bot and dp:
        bot_task = asyncio.create_task(dp.start_polling(bot))
    
    yield
    
    if bot_task:
        bot_task.cancel()
        if bot:
            await bot.session.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS middleware for TMA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API ENDPOINTS ---

@app.get("/api/user/{user_id}/balance", response_model=DailyBalance)
async def get_balance(user_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_daily_balance(db, user_id)

@app.get("/api/user/{user_id}/analytics", response_model=MonthlyAnalytics)
async def get_analytics(user_id: int, year: int = None, month: int = None, db: AsyncSession = Depends(get_db)):
    return await crud.get_monthly_analytics(db, user_id, year, month)

@app.get("/api/user/{user_id}/transactions", response_model=list[TransactionResponse])
async def list_transactions(user_id: int, limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    return await crud.get_user_transactions(db, user_id, limit, offset)

@app.post("/api/transactions", response_model=TransactionResponse)
async def add_transaction(data: TransactionCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_transaction(db, data)

@app.delete("/api/transactions/{tx_id}")
async def remove_transaction(tx_id: int, user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    success = await crud.delete_transaction(db, user_id, tx_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction topilmadi")
    return {"status": "ok", "message": "O'chirildi"}

@app.get("/api/user/{user_id}/loans", response_model=list[LoanResponse])
async def list_loans(user_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_user_loans(db, user_id)

@app.post("/api/loans", response_model=LoanResponse)
async def add_loan(data: LoanCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_loan(db, data)

@app.post("/api/loans/{loan_id}/pay", response_model=LoanResponse)
async def pay_user_loan(loan_id: int, payment: LoanPayment, user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    loan = await crud.pay_loan(db, user_id, loan_id, payment)
    if not loan:
        raise HTTPException(status_code=404, detail="Kredit topilmadi")
    return loan

@app.delete("/api/loans/{loan_id}")
async def remove_loan(loan_id: int, user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    success = await crud.delete_loan(db, user_id, loan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Kredit topilmadi")
    return {"status": "ok", "message": "O'chirildi"}

@app.get("/api/user/{user_id}/goals", response_model=list[GoalResponse])
async def list_goals(user_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_user_goals(db, user_id)

@app.post("/api/goals", response_model=GoalResponse)
async def add_goal(data: GoalCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_goal(db, data)

@app.post("/api/goals/{goal_id}/deposit", response_model=GoalResponse)
async def deposit_user_goal(goal_id: int, dep: GoalDeposit, user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    goal = await crud.deposit_goal(db, user_id, goal_id, dep)
    if not goal:
        raise HTTPException(status_code=404, detail="Maqsad topilmadi")
    return goal

@app.post("/api/mystery-loss")
async def check_mystery_loss(data: MysteryLossCreate, db: AsyncSession = Depends(get_db)):
    tx = await crud.log_mystery_loss(db, data.user_id, data.expected_amount, data.actual_amount, data.note)
    if not tx:
        return {"status": "no_loss", "difference": 0, "message": "Hisob to'g'ri, yo'qotish aniqlanmadi"}
    return {
        "status": "loss_detected",
        "difference": tx.amount,
        "message": f"{tx.amount:,.0f} so'm noma'lum yo'qolgan xarajat sifatida yozildi"
    }

# File exports
@app.get("/api/export/pdf")
async def export_pdf(user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    txs = await crud.get_user_transactions(db, user_id, limit=200)
    loans = await crud.get_user_loans(db, user_id)
    analytics = await crud.get_monthly_analytics(db, user_id)
    pdf_bytes = generate_pdf_report(txs, loans, analytics)
    return Response(
        content=pdf_bytes.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=hisobot_{user_id}.pdf"}
    )

@app.get("/api/export/excel")
async def export_excel(user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    txs = await crud.get_user_transactions(db, user_id, limit=500)
    loans = await crud.get_user_loans(db, user_id)
    analytics = await crud.get_monthly_analytics(db, user_id)
    excel_bytes = generate_excel_report(txs, loans, analytics)
    return Response(
        content=excel_bytes.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=hisobot_{user_id}.xlsx"}
    )

# Static Frontend mounting
frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
