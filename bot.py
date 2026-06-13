import os
import sqlite3
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from groq import Groq

# ==================== تنظیمات ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = 8065571732  # 🔴 ایدی خودت رو بذار اینجا

client = Groq(api_key=GROQ_API_KEY)
DB_PATH = "users_data.db"

# ==================== راه‌اندازی دیتابیس ====================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # جدول اطلاعات کاربران
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        business_name TEXT,
        birth_date TEXT,
        phone TEXT,
        address TEXT,
        referral_source TEXT,
        register_date TEXT
    )''')
    
    # جدول پاسخ پرسشنامه
    c.execute('''CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        q1 TEXT,
        q2 TEXT,
        q3 TEXT,
        q4 TEXT,
        q5 TEXT,
        q6 TEXT,
        q7 TEXT,
        submit_date TEXT
    )''')
    
    # جدول وضعیت کاربر
    c.execute('''CREATE TABLE IF NOT EXISTS status (
        user_id INTEGER PRIMARY KEY,
        step INTEGER DEFAULT 0,
        temp TEXT
    )''')
    
    conn.commit()
    conn.close()
    print("✅ دیتابیس آماده شد")

# ==================== توابع دیتابیس ====================
def save_user(user_id, data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO users 
        (user_id, first_name, last_name, business_name, birth_date, phone, address, referral_source, register_date)
        VALUES (?,?,?,?,?,?,?,?,?)''',
        (user_id, data.get('first_name',''), data.get('last_name',''), data.get('business_name',''),
         data.get('birth_date',''), data.get('phone',''), data.get('address',''), 
         data.get('referral_source',''), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def save_answers(user_id, answers):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO answers 
        (user_id, q1, q2, q3, q4, q5, q6, q7, submit_date)
        VALUES (?,?,?,?,?,?,?,?,?)''',
        (user_id, answers.get('q1',''), answers.get('q2',''), answers.get('q3',''),
         answers.get('q4',''), answers.get('q5',''), answers.get('q6',''), answers.get('q7',''),
         datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_status(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT step, temp FROM status WHERE user_id = ?', (user_id,))
    r = c.fetchone()
    conn.close()
    if r:
        return {'step': r[0], 'temp': r[1] if r[1] else '{}'}
    return {'step': 0, 'temp': '{}'}

def set_status(user_id, step, temp=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO status (user_id, step, temp) VALUES (?,?,?)', 
              (user_id, step, temp if temp else '{}'))
    conn.commit()
    conn.close()

def is_registered(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
    r = c.fetchone()
    conn.close()
    return r is not None

# ==================== متن سوالات ====================
REG_QUESTIONS = [
    ("first_name", "نام خود را وارد کنید:"),
    ("last_name", "نام خانوادگی خود را وارد کنید:"),
    ("business_name", "نام کسب و کار خود را وارد کنید:"),
    ("birth_date", "تاریخ تولد (مثال: 1370/05/15):"),
    ("phone", "شماره تماس موبایل:"),
    ("address", "آدرس شعب:"),
    ("referral_source", "راه معرفی (چطور با ما آشنا شدید؟):")
]

SURVEY_QUESTIONS = [
    ("q1", "1️⃣ درباره کسب و کار خود بنویسید:"),
    ("q2", "2️⃣ چه محصولاتی دارید و مزیت شما نسبت به دیگران چیست؟"),
    ("q3", "3️⃣ چه زیرساخت‌های مجازی دارید؟ (سایت، اینستاگرام، ...)"),
    ("q4", "4️⃣ چه نیروهایی دارید؟ (تعداد و تخصص)"),
    ("q5", "5️⃣ بالاترین فروش ماهیانه شما چقدر بوده؟"),
    ("q6", "6️⃣ مهمترین مشکل فعلی شما چیست؟"),
    ("q7", "7️⃣ در چه زمینه‌ای نیاز به مشاوره دارید؟")
]

# ==================== دکمه ====================
reg_btn = ReplyKeyboardMarkup([[KeyboardButton("📝 ثبت‌نام")]], resize_keyboard=True)

# ==================== توابع اصلی ====================
async def start(update: Update, ctx):
    uid = update.effective_user.id
    
    if is_registered(uid):
        await update.message.reply_text("✅ قبلاً ثبت‌نام کردی! سوالت رو بپرس.")
        return
    
    try:
        with open('images/welcome.jpg', 'rb') as f:
            await update.message.reply_photo(f, caption="سلام سلام\nشهبازی هستم، مریم 😍🌱\n\nبرای شروع ثبت‌نام، روی دکمه زیر کلیک کن 👇", reply_markup=reg_btn)
    except:
        await update.message.reply_text("سلام سلام\nشهبازی هستم، مریم 😍🌱\n\nبرای شروع ثبت‌نام، روی دکمه زیر کلیک کن 👇", reply_markup=reg_btn)

async def reg_start(update: Update, ctx):
    uid = update.effective_user.id
    set_status(uid, 1)
    await update.message.reply_text(f"✅ ثبت‌نام شروع شد!\n\n{REG_QUESTIONS[0][1]}")

async def handle(update: Update, ctx):
    uid = update.effective_user.id
    text = update.message.text
    
    if text == "📝 ثبت‌نام":
        await reg_start(update, ctx)
        return
    
    status = get_status(uid)
    step = status['step']
    
    # اگه ثبت‌نام کامل شده، به Groq پاسخ بده
    if step == 0 and is_registered(uid):
        try:
            r = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": text}])
            await update.message.reply_text(r.choices[0].message.content)
        except Exception as e:
            await update.message.reply_text(f"⚠️ خطا: {e}")
        return
    
    # مرحله ثبت‌نام (1 تا 7)
    if 1 <= step <= 7:
        import json
        temp = json.loads(status['temp']) if status['temp'] else {}
        field, _ = REG_QUESTIONS[step-1]
        temp[field] = text
        set_status(uid, step+1, json.dumps(temp))
        
        if step < 7:
            _, q = REG_QUESTIONS[step]
            await update.message.reply_text(q)
        else:
            # ذخیره اطلاعات کاربر
            save_user(uid, temp)
            set_status(uid, 8)  # برو به مرحله پرسشنامه
            await update.message.reply_text("✅ اطلاعات ثبت شد!\n\nحالا به سوالات زیر پاسخ بده:")
            _, q = SURVEY_QUESTIONS[0]
            await update.message.reply_text(q)
    
    # مرحله پرسشنامه (8 تا 14)
    elif 8 <= step <= 14:
        import json
        idx = step - 8
        temp = json.loads(status['temp']) if status['temp'] else {}
        field, _ = SURVEY_QUESTIONS[idx]
        temp[field] = text
        set_status(uid, step+1, json.dumps(temp))
        
        if idx + 1 < len(SURVEY_QUESTIONS):
            _, q = SURVEY_QUESTIONS[idx+1]
            await update.message.reply_text(q)
        else:
            # ذخیره پاسخ‌ها
            save_answers(uid, temp)
            set_status(uid, 0)  # تمام شد
            await update.message.reply_text(
                "🌹 **با تشکر از شما!** 🌹\n\n"
                "اطلاعات شما ثبت شد.\n"
                "✅ **ظرف ۴۸ ساعت با شما تماس می‌گیریم.**\n\n"
                "حالا می‌تونی سوالت رو بپرسی.",
                parse_mode='Markdown'
            )

async def get_db(update: Update, ctx):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید!")
        return
    try:
        with open(DB_PATH, 'rb') as f:
            await update.message.reply_document(f, filename='users_data.db')
    except:
        await update.message.reply_text("خطا!")

# ==================== اجرا ====================
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("getdb", get_db))
app.add_handler(MessageHandler(filters.TEXT, handle))

init_db()
print("🤖 بات روشن شد...")
app.run_polling()