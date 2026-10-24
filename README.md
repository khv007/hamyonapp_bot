# 📱 Maosh va Xarajatlar — Aqlli Hisoblagich (Telegram Mini App)

> **Kunlik oʻzgaruvchan daromad oladiganlar, mayda xarajatlar tufayli oyiga 1–2 mln soʻm yoʻqotayotganlar va kredit toʻlovchilari uchun maxsus yaratilgan Telegram Mini App (TMA) va Moliyaviy Yordamchi.**

---

## 🌟 Asosiy Xususiyatlar va Imkoniyatlar

1. **⚡️ Smart Kalkulyator (Bosh Ekran):**
   - Oddiy telefon kalkulyatoridek tezkor raqamlar paneli (NumPad);
   - Jonli hisob-kitob qilish: `15000 + 20000` deb bevosita kiritish imkoni;
   - 1-bosish bilan xarajat toifalarini tanlash (🍔 Tushlik, 🚕 Yo'l/Benzin, ☕️ Mayda-chuyda, 🏠 Ro'zg'or va h.k.);
   - 🟢 **Kunlik Daromad** kiritish tugmasi;
   - **Jonli Kassa Paneli:** Tushum, Xarajat, Kredit zaxirasi va **Real Erkin Qoldiq**ni bir zumda koʻrsatadi.

2. **💳 Qarzlar va Kreditlar (Kunlik Zaxira Algoritmi):**
   - Bank kreditlari, Uzum Nasiya, doʻkon yoki tanishlardan qarzlar portfeli;
   - **Kunlik Zaxira:** Oylik jami kredit toʻlovini 30 kunga boʻlib, har kungi tushumdan avtomatik "tegilmasin" qilib ajratib qoʻyadi (oy oxirida toʻlov kelganda pulsiz qolmaslik uchun);
   - Qarz toʻlanganida progress chizigʻi vizual yashil boʻlib qisqaradi.

3. **📊 Aqlli Tahlil va "Qora Tuynuk" Detektori:**
   - **🕳 "Qora Tuynuk" (Nomaʼlum yoʻqolgan pullar):** Choʻntakdagi naqd pul bilan ilovadagi hisob solishtiriladi va yoʻqolgan pullar fosh qilinadi;
   - **☕️ "Latte Effekti" (Mayda xarajatlar fojiasi):** Kunlik 10–20 ming soʻmlik mayda narsalarning 1 oylik va 1 yillik zararini hisoblaydi;
   - **⏳ "Mehnat Soati":** Sarflangan barcha pullar necha soatlik mehnatingizga tengligini aytib beradi.

4. **📜 Tarix va Orzular Jamgʻarmasi (Kopilka):**
   - Barcha tranzaksiyalar tarixi, xatolarni bitta bosish bilan oʻchirish;
   - Kopilka orqali orzular (yangi telefon, kiyim, sayohat) uchun kunlik pul yigʻish.

5. **📑 PDF va 📊 Excel Eksport:**
   - **PDF:** Apple Card / premium bank statement uslubidagi toʻliq vizual, rangli infografikali oylik hisobot;
   - **Excel:** Hech qanday ortiqcha bezaklarsiz, qulay saralash va formulalar uchun sof jadvalli format.

---

## 📱 Qurilmalarga Moslashuv (Mobile-First / Mobile-Only)
- **iOS:** iPhone X dan boshlab iPhone 18 Pro Max gacha (Dynamic Island, yuqori va pastki `safe-area-inset`, tebranishlar).
- **Android:** Android 14 va undan yuqori zamonaviy smartfonlar.
- **Telegram Haptic Feedback:** Kalkulyator tugmalari bosilganda telefonda yoqimli tebranish (taktil aloqa).

---

## 🛠 Texnologiyalar (Stack)
- **Frontend:** HTML5, Modern Vanilla CSS (Glassmorphism, Dark Mode), Vanilla JavaScript, Telegram WebApp SDK.
- **Backend:** Python 3.15, FastAPI, Uvicorn, aiogram 3.
- **Maʼlumotlar Bazasi:** **PostgreSQL** (`asyncpg` orqali) va avtomatik SQLite fallback (mahalliy ishlab chiqish uchun).
- **Hisobot Generatorlari:** ReportLab (PDF), OpenPyXL (Excel).

---

## 🚀 Oʻrnatish va Ishga Tushirish

### 1. Sozlamalar (`.env`)
Loyihaning ildiz papkasidagi `.env` faylini oching:
```env
# PostgreSQL ulanishi (Supabase, Neon, yoki mahalliy PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/maosh_xarajatlar

# Telegram Bot Token (Telegramdagi @BotFather dan olinadi)
TELEGRAM_BOT_TOKEN=7123456789:AAExampleBotTokenHere

# WebApp URL (Server manzili)
WEBAPP_URL=http://localhost:8000
```

### 2. Serverni Ishga Tushirish
Quyidagi buyruq orqali serverni ishga tushiring:
```powershell
C:\Python315\python.exe -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

Brauzerda yoki Telegram WebApp orqali ochish:
```
http://localhost:8000
```

---

## 🤖 Telegram Botdan Foydalanish
1. Botga `/start` yuboriladi -> **"📱 Aqlli Hisoblagichni Ochish"** tugmasi orqali Mini App ochiladi.
2. Botga `/hisobot` yuboriladi -> PDF yoki Excel fayli toʻgʻridan-toʻgʻri chatga yuboriladi.
3. Bot har kuni kechqurun 21:30 da kassani yopish va hisob-kitob qilish uchun eslatma beradi.
