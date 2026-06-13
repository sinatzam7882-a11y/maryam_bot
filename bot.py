import os
import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from groq import Groq
from database import init_db, save_user_info, save_questionnaire, get_user_step, update_user_step, get_all_users_data

# خواندن توکن‌ها از متغیرهای محیطی
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

# راه‌اندازی دیتابیس
init_db()

# مراحل ثبت‌نام
REGISTRATION_STEPS = [
    "first_name",    # 1: نام
    "last_name",     # 2: نام خانوادگی
    "business_name", # 3: نام کسب و کار
    "birth_date",    # 4: تاریخ تولد
    "phone",         # 5: شماره تماس
    "address",       # 6: آدرس شعب
    "referral_source" # 7: راه معرفی
]

# سوالات پرسشنامه
QUESTIONNAIRE_QUESTIONS = [
    "1️⃣ درباره کسب و کار خود بنویسید:\n(توضیح درباره فعالیت، سابقه، اهداف)",
    "2️⃣ چه محصولاتی دارید و مزیت کار شما نسبت به دیگران چیست؟",
    "3️⃣ چه زیرساخت‌های مجازی دارید؟\n(سایت، اینستاگرام، اپلیکیشن، و...)",
    "4️⃣ چه نیروهایی دارید؟\n(تعداد و تخصص نیروها)",
    "5️⃣ بالاترین فروش ماهیانه که ثبت داشتید؟\n(تومان یا تعداد)",
    "6️⃣ مسئله فعلی شما چیست؟\n(مشکلات و چالش‌ها)",
    "7️⃣ در چه زمینه‌هایی از متخصص مشاوره می‌خواهید؟"
]

# دکمه شروع ثبت‌نام
register_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("📝 ثبت‌نام در باشگاه مشتریان")]],
    resize_keyboard=True
)

# دستور start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # چک کردن اینکه کاربر قبلاً ثبت‌نام کرده یا نه
    user_step = get_user_step(user_id)
    
    if user_step['step'] == 99:  # ثبت‌نام کامل شده
        await update.message.reply_text(
            "✅ شما قبلاً ثبت‌نام کرده‌اید!\n"
            "حالا می‌توانید سوالات خود را بپرسید.",
            reply_markup=register_keyboard
        )
    else:
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
                    reply_markup=register_keyboard
                )
        except FileNotFoundError:
            await update.message.reply_text(
                """سلام سلام
شهبازی هستم، مریم 😍🌱
اینجا قراره هویت کسب و کار و برند خودتون رو بسازید و روز به روز فروش بیشتری رو تجربه کنین. 
با من همراه باش

برای شروع روی دکمه زیر کلیک کن 👇""",
                reply_markup=register_keyboard
            )

# شروع فرآیند ثبت‌نام
async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    update_user_step(user_id, 1)  # مرحله 1: شروع ثبت‌نام
    await update.message.reply_text("✅ ثبت‌نام شروع شد!\n\nلطفاً **نام** خود را وارد کنید:")

# پردازش مرحله به مرحله ثبت‌نام
async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_step = get_user_step(user_id)
    step = user_step['step']
    text = update.message.text
    
    # اگر کاربر دکمه ثبت‌نام رو زد
    if text == "📝 ثبت‌نام در باشگاه مشتریان":
        await start_registration(update, context)
        return
    
    # اگر در مرحله ثبت‌نام نیست
    if step == 0:
        # پاسخ عادی به Groq
        await handle_message(update, context)
        return
    
    # پردازش مراحل ثبت‌نام
    temp_data = json.loads(user_step['temp_data']) if user_step['temp_data'] else {}
    
    if step <= len(REGISTRATION_STEPS):
        field = REGISTRATION_STEPS[step - 1]
        temp_data[field] = text
        
        if step < len(REGISTRATION_STEPS):
            # مرحله بعدی
            update_user_step(user_id, step + 1, json.dumps(temp_data))
            
            # پیام راهنما برای مرحله بعد
            next_field = REGISTRATION_STEPS[step]
            messages = {
                "last_name": "لطفاً **نام خانوادگی** خود را وارد کنید:",
                "business_name": "لطفاً **نام کسب و کار** خود را وارد کنید:",
                "birth_date": "لطفاً **تاریخ تولد** خود را وارد کنید (مثال: 1370/05/15):",
                "phone": "لطفاً **شماره تماس موبایل** خود را وارد کنید:",
                "address": "لطفاً **آدرس شعب** خود را وارد کنید:",
                "referral_source": "لطفاً **راه معرفی** را وارد کنید:\n(چطور با ما آشنا شدید؟)"
            }
            await update.message.reply_text(messages.get(next_field, "لطفاً ادامه دهید:"))
            
        else:
            # آخرین مرحله ثبت‌نام - ذخیره اطلاعات
            save_user_info(user_id, temp_data)
            update_user_step(user_id, 100, json.dumps(temp_data), 1)  # بریم به مرحله پرسشنامه
            
            await update.message.reply_text(
                "✅ اطلاعات شما با موفقیت ثبت شد!\n\n"
                "📋 حالا لطفاً به سوالات تخصصی زیر پاسخ دهید:\n\n"
                f"{QUESTIONNAIRE_QUESTIONS[0]}"
            )
    
    # پردازش پرسشنامه
    elif 100 <= step < 100 + len(QUESTIONNAIRE_QUESTIONS):
        q_step = user_step['questionnaire_step']
        answers = json.loads(user_step['temp_data']) if user_step['temp_data'] else {}
        
        current_q = q_step - 1
        q_fields = [
            "about_business", "products_advantages", "virtual_infrastructure",
            "team_members", "max_monthly_sales", "current_problem", "consultation_fields"
        ]
        
        if current_q < len(q_fields):
            answers[q_fields[current_q]] = text
            
            if q_step < len(QUESTIONNAIRE_QUESTIONS):
                # سوال بعدی
                update_user_step(user_id, step, json.dumps(answers), q_step + 1)
                await update.message.reply_text(f"📝 {QUESTIONNAIRE_QUESTIONS[q_step]}")
            else:
                # اتمام پرسشنامه
                save_questionnaire(user_id, answers)
                update_user_step(user_id, 99)  # ثبت‌نام کامل شد
                
                await update.message.reply_text(
                    "🌹 **با تشکر از شما!** 🌹\n\n"
                    "اطلاعات شما با موفقیت ثبت شد.\n"
                    "✅ **ظرف ۴۸ ساعت آینده کارشناسان ما با شما تماس می‌گیرند.**\n\n"
                    "تا آن زمان می‌توانید سوالات خود را از من بپرسید.\n"
                    "موفق باشید 🚀",
                    parse_mode='Markdown'
                )

# پاسخگویی عادی به Groq
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "تو یک دستیار هوشمند و مفید برای کسب و کار و برندسازی هستی. به فارسی و روان پاسخ بده."
                },
                {
                    "role": "user",
                    "content": user_text
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)
        
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطایی رخ داد: {str(e)}")

# دستور مخصوص ادمین برای دریافت دیتابیس
async def get_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # فقط ادمین بتونه ببینه (ایدی تلگرام خودت رو بذار)
    ADMIN_ID = 8065571732  # ایدی عددی خودت رو بذار اینجا
    
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ شما دسترسی به این بخش ندارید!")
        return
    
    try:
        with open('users_data.db', 'rb') as db_file:
            await update.message.reply_document(
                document=db_file,
                filename='users_data.db',
                caption="📊 اطلاعات کاربران و پرسشنامه‌ها"
            )
    except:
        await update.message.reply_text("خطا در ارسال دیتابیس")

# ساختن اپلیکیشن
app = ApplicationBuilder().token(BOT_TOKEN).build()

# اضافه کردن هندلرها
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("getdb", get_database))  # دستور دریافت دیتابیس
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_registration))

print("🤖 بات با موفقیت روشن شد...")
print("منتظر پیام‌های کاربران هستم...")

app.run_polling()