import os
import json
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from groq import Groq

# ==================== تنظیمات ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = 8065571732  # 🔴 ایدی خودت رو بذار اینجا (از @userinfobot بگیر)

client = Groq(api_key=GROQ_API_KEY)

# فایل‌های JSON برای ذخیره اطلاعات
USERS_FILE = "users.json"
SURVEY_FILE = "survey.json"
STATUS_FILE = "status.json"

# ==================== توابع خواندن و نوشتن JSON ====================
def read_json(file_path, default={}):
    """خواندن اطلاعات از فایل JSON"""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default
    return default

def write_json(file_path, data):
    """نوشتن اطلاعات در فایل JSON"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==================== توابع ذخیره و بازیابی اطلاعات ====================
def save_user_info(user_id, info):
    """ذخیره اطلاعات کاربر"""
    users = read_json(USERS_FILE, {})
    users[str(user_id)] = {
        **info,
        "register_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    write_json(USERS_FILE, users)
    print(f"✅ اطلاعات کاربر {user_id} ذخیره شد")

def get_user_info(user_id):
    """دریافت اطلاعات یک کاربر"""
    users = read_json(USERS_FILE, {})
    return users.get(str(user_id))

def save_survey_answers(user_id, answers):
    """ذخیره پاسخ‌های پرسشنامه"""
    all_surveys = read_json(SURVEY_FILE, {})
    all_surveys[str(user_id)] = {
        **answers,
        "submit_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    write_json(SURVEY_FILE, all_surveys)
    print(f"✅ پرسشنامه کاربر {user_id} ذخیره شد")

def get_user_status(user_id):
    """دریافت مرحله فعلی کاربر"""
    statuses = read_json(STATUS_FILE, {})
    return statuses.get(str(user_id), {"step": 0, "temp": {}})

def set_user_status(user_id, step, temp_data=None):
    """تنظیم مرحله کاربر"""
    statuses = read_json(STATUS_FILE, {})
    statuses[str(user_id)] = {
        "step": step,
        "temp": temp_data if temp_data else {}
    }
    write_json(STATUS_FILE, statuses)

def delete_user_status(user_id):
    """حذف وضعیت کاربر بعد از اتمام"""
    statuses = read_json(STATUS_FILE, {})
    if str(user_id) in statuses:
        del statuses[str(user_id)]
        write_json(STATUS_FILE, statuses)

def is_user_registered(user_id):
    """بررسی ثبت‌نام کاربر"""
    users = read_json(USERS_FILE, {})
    return str(user_id) in users

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
reg_btn = ReplyKeyboardMarkup(
    [[KeyboardButton("📝 ثبت‌نام در باشگاه مشتریان")]],
    resize_keyboard=True
)

# ==================== دستور start ====================
async def start(update: Update, context):
    user_id = update.effective_user.id
    
    if is_user_registered(user_id):
        await update.message.reply_text(
            "✅ شما قبلاً ثبت‌نام کرده‌اید!\n\nحالا می‌توانید سوالات خود را بپرسید.",
            reply_markup=reg_btn
        )
        return
    
    # نمایش عکس و پیام خوش‌آمدگویی
    try:
        with open('images/welcome.jpg', 'rb') as photo:
            caption = """سلام سلام
شهبازی هستم، مریم 😍🌱
اینجا قراره هویت کسب و کار و برند خودتون رو بسازید و روز به روز فروش بیشتری رو تجربه کنین. 
با من همراه باش

برای شروع روی دکمه زیر کلیک کن 👇"""
            await update.message.reply_photo(
                photo=photo,
                caption=caption,
                reply_markup=reg_btn
            )
    except FileNotFoundError:
        await update.message.reply_text(
            """سلام سلام
شهبازی هستم، مریم 😍🌱
اینجا قراره هویت کسب و کار و برند خودتون رو بسازید و روز به روز فروش بیشتری رو تجربه کنین. 
با من همراه باش

برای شروع روی دکمه زیر کلیک کن 👇""",
            reply_markup=reg_btn
        )

# ==================== شروع ثبت‌نام ====================
async def start_registration(update: Update, context):
    user_id = update.effective_user.id
    set_user_status(user_id, 1, {})
    await update.message.reply_text(f"✅ ثبت‌نام شروع شد!\n\n{REG_QUESTIONS[0][1]}")

# ==================== پردازش اصلی پیام‌ها ====================
async def handle_message(update: Update, context):
    user_id = update.effective_user.id
    text = update.message.text
    
    # اگر کاربر دکمه ثبت‌نام زد
    if text == "📝 ثبت‌نام در باشگاه مشتریان":
        await start_registration(update, context)
        return
    
    # دریافت وضعیت کاربر
    status = get_user_status(user_id)
    step = status.get("step", 0)
    temp = status.get("temp", {})
    
    # مرحله 0: کاربر در حال ثبت‌نام نیست -> پاسخ عادی از Groq
    if step == 0:
        # اگه ثبت‌نام نکرده، یادآوری کن
        if not is_user_registered(user_id):
            await update.message.reply_text(
                "⚠️ لطفاً ابتدا ثبت‌نام کنید.\n\n"
                "روی دکمه 📝 ثبت‌نام در باشگاه مشتریان کلیک کن.",
                reply_markup=reg_btn
            )
            return
        
        # پاسخ عادی از Groq
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "تو یک دستیار هوشمند و مفید برای کسب و کار و برندسازی هستی. به فارسی و روان پاسخ بده."},
                    {"role": "user", "content": text}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            await update.message.reply_text(response.choices[0].message.content)
        except Exception as e:
            await update.message.reply_text(f"⚠️ خطا: {str(e)}")
        return
    
    # مرحله 1 تا 7: ثبت‌نام
    if 1 <= step <= 7:
        idx = step - 1
        field_name, _ = REG_QUESTIONS[idx]
        temp[field_name] = text
        
        if step < 7:
            # مرحله بعدی
            set_user_status(user_id, step + 1, temp)
            _, next_q = REG_QUESTIONS[step]
            await update.message.reply_text(next_q)
        else:
            # آخرین مرحله ثبت‌نام - ذخیره اطلاعات
            save_user_info(user_id, temp)
            set_user_status(user_id, 8, {})  # برو به مرحله پرسشنامه
            await update.message.reply_text(
                "✅ اطلاعات شما با موفقیت ثبت شد!\n\n"
                "📋 حالا لطفاً به سوالات تخصصی زیر پاسخ دهید:\n\n"
                f"{SURVEY_QUESTIONS[0][1]}"
            )
        return
    
    # مرحله 8 تا 14: پرسشنامه
    if 8 <= step <= 14:
        idx = step - 8
        field_name, _ = SURVEY_QUESTIONS[idx]
        temp[field_name] = text
        
        if idx + 1 < len(SURVEY_QUESTIONS):
            # سوال بعدی
            set_user_status(user_id, step + 1, temp)
            _, next_q = SURVEY_QUESTIONS[idx + 1]
            await update.message.reply_text(next_q)
        else:
            # اتمام پرسشنامه
            save_survey_answers(user_id, temp)
            delete_user_status(user_id)  # پاک کردن وضعیت
            await update.message.reply_text(
                "🌹 **با تشکر از شما!** 🌹\n\n"
                "اطلاعات شما با موفقیت ثبت شد.\n"
                "✅ **ظرف ۴۸ ساعت آینده کارشناسان ما با شما تماس می‌گیرند.**\n\n"
                "تا آن زمان می‌توانید سوالات خود را از من بپرسید.\n"
                "موفق باشید 🚀",
                parse_mode='Markdown'
            )
        return

# ==================== دستور دریافت فایل‌های JSON (فقط ادمین) ====================
async def get_data(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ شما دسترسی به این بخش ندارید!")
        return
    
    # ارسال فایل users.json
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'rb') as f:
            await update.message.reply_document(document=f, filename='users.json')
    else:
        await update.message.reply_text("فایل users.json وجود ندارد")
    
    # ارسال فایل survey.json
    if os.path.exists(SURVEY_FILE):
        with open(SURVEY_FILE, 'rb') as f:
            await update.message.reply_document(document=f, filename='survey.json')

# ==================== دستور مشاهده خلاصه اطلاعات (فقط ادمین) ====================
async def show_summary(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ شما دسترسی به این بخش ندارید!")
        return
    
    users = read_json(USERS_FILE, {})
    surveys = read_json(SURVEY_FILE, {})
    
    if not users:
        await update.message.reply_text("📭 هنوز کاربری ثبت‌نام نکرده است.")
        return
    
    summary = f"📊 **آمار کلی:**\n"
    summary += f"- تعداد کاربران ثبت‌نام شده: {len(users)}\n"
    summary += f"- تعداد پرسشنامه‌های تکمیل شده: {len(surveys)}\n\n"
    summary += "**آخرین کاربران:**\n"
    
    for i, (uid, info) in enumerate(list(users.items())[-5:]):
        summary += f"{i+1}. {info.get('first_name', '')} {info.get('last_name', '')} - {info.get('business_name', '')}\n"
    
    await update.message.reply_text(summary, parse_mode='Markdown')

# ==================== اجرای اصلی ====================
app = ApplicationBuilder().token(BOT_TOKEN).build()

# اضافه کردن هندلرها
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("getdata", get_data))      # دریافت فایل‌های JSON
app.add_handler(CommandHandler("summary", show_summary))   # مشاهده خلاصه
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 بات با موفقیت روشن شد...")
print("📁 اطلاعات در فایل‌های JSON ذخیره می‌شوند:")
print(f"   - {USERS_FILE} : اطلاعات کاربران")
print(f"   - {SURVEY_FILE} : پاسخ‌های پرسشنامه")
print("منتظر پیام‌های کاربران هستم...")

app.run_polling()