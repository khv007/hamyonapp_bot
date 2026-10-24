import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    WebAppInfo, BufferedInputFile
)
from app.config import settings
from app.database import get_session
from app.crud import (
    get_or_create_user, get_daily_balance, 
    get_monthly_analytics, get_user_transactions, get_user_loans
)
from app.exports import generate_pdf_report, generate_excel_report

logger = logging.getLogger(__name__)

bot = None
dp = None

if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

def get_webapp_keyboard():
    url = settings.WEBAPP_URL
    buttons = []
    if url.startswith("https://"):
        buttons.append([InlineKeyboardButton(text="📱 Aqlli Hisoblagichni Ochish", web_app=WebAppInfo(url=url))])
    else:
        buttons.append([InlineKeyboardButton(text="📱 Hisoblagichni Ochish", url="https://t.me/hamyonapp_bot")])
        
    buttons.append([
        InlineKeyboardButton(text="📑 PDF Hisobot", callback_data="export_pdf"),
        InlineKeyboardButton(text="📊 Excel Hisobot", callback_data="export_excel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

if dp:
    @dp.message(CommandStart())
    async def cmd_start(message: types.Message):
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        username = message.from_user.username
        
        async with get_session() as session:
            await get_or_create_user(session, user_id, first_name, username)
            balance = await get_daily_balance(session, user_id)
            
        welcome_text = (
            f"Assalomu alaykum, <b>{first_name}</b>!\n\n"
            f"💼 <b>'Maosh va Xarajatlar'</b> aqlli hisoblagichiga xush kelibsiz.\n\n"
            f"Bugungi kassa holati:\n"
            f"🟢 Tushum: <b>+{balance.today_income:,.0f} so'm</b>\n"
            f"🔴 Xarajat: <b>-{balance.today_expense:,.0f} so'm</b>\n"
            f"🛡 Kredit zaxirasi: <b>-{balance.daily_loan_reserve:,.0f} so'm</b>\n"
            f"🟡 Erkin qoldiq: <b>{balance.safe_free_balance:,.0f} so'm</b>\n\n"
            f"Quyidagi tugmani bosing va 3 soniyada xarajatlarni hisoblang:"
        )
        await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_webapp_keyboard())

    @dp.message(Command("hisobot"))
    async def cmd_report(message: types.Message):
        user_id = message.from_user.id
        async with get_session() as session:
            analytics = await get_monthly_analytics(session, user_id)
            
        txt = (
            f"📊 <b>{analytics.month_name} oyi hisoboti:</b>\n\n"
            f"🟢 Jami daromad: <b>+{analytics.total_income:,.0f} so'm</b>\n"
            f"🔴 Jami xarajat: <b>-{analytics.total_expense:,.0f} so'm</b>\n"
            f"🕳 Yo'qolgan (Qora tuynuk): <b>{analytics.mystery_loss_total:,.0f} so'm</b>\n"
            f"☕️ Mayda xarajatlar: <b>{analytics.small_expenses_total:,.0f} so'm</b>\n"
            f"⏳ Sarflangan mehnat: <b>{analytics.work_hours_spent} soat</b>\n\n"
            f"Fayl ko'rinishida yuklab olish uchun tugmalardan birini tanlang:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📑 PDF (Chiroyli dizayn)", callback_data="export_pdf"),
                InlineKeyboardButton(text="📊 Excel (Jadval)", callback_data="export_excel")
            ]
        ])
        await message.answer(txt, parse_mode="HTML", reply_markup=kb)

    @dp.callback_query(F.data == "export_pdf")
    async def cb_export_pdf(call: types.CallbackQuery):
        await call.answer("PDF tayyorlanmoqda...")
        user_id = call.from_user.id
        
        async with get_session() as session:
            txs = await get_user_transactions(session, user_id, limit=200)
            loans = await get_user_loans(session, user_id)
            analytics = await get_monthly_analytics(session, user_id)
            
            pdf_bytes = generate_pdf_report(txs, loans, analytics)
            
        file = BufferedInputFile(pdf_bytes.getvalue(), filename=f"hisobot_{user_id}.pdf")
        await call.message.answer_document(
            file, 
            caption=f"📑 <b>{analytics.month_name}</b> uchun to'liq vizual moliyaviy hisobotingiz tayyor!",
            parse_mode="HTML"
        )

    @dp.callback_query(F.data == "export_excel")
    async def cb_export_excel(call: types.CallbackQuery):
        await call.answer("Excel tayyorlanmoqda...")
        user_id = call.from_user.id
        
        async with get_session() as session:
            txs = await get_user_transactions(session, user_id, limit=500)
            loans = await get_user_loans(session, user_id)
            analytics = await get_monthly_analytics(session, user_id)
            
            excel_bytes = generate_excel_report(txs, loans, analytics)
            
        file = BufferedInputFile(excel_bytes.getvalue(), filename=f"hisobot_{user_id}.xlsx")
        await call.message.answer_document(
            file, 
            caption=f"📊 <b>{analytics.month_name}</b> uchun toza Excel jadvallari tayyor!",
            parse_mode="HTML"
        )

async def send_evening_reminder(user_id: int):
    """Sends 21:30 daily check-in reminder to close the day's cash drawer."""
    if not bot:
        return
    try:
        async with get_session() as session:
            balance = await get_daily_balance(session, user_id)
        msg = (
            f"🌙 <b>Kun yakuni eslatmasi!</b>\n\n"
            f"Bugun yana biror xarajat bo'ldimi?\n"
            f"Hozirgi qoldiq: <b>{balance.safe_free_balance:,.0f} so'm</b>.\n\n"
            f"Kassani yopish va cho'ntakdagi pulni solishtirish uchun hisoblagichni oching:"
        )
        await bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=get_webapp_keyboard())
    except Exception as e:
        logger.error(f"Failed to send reminder to {user_id}: {e}")
