import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from groq import Groq

# خواندن توکن‌ها از متغیرهای محیطی
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ساختن کلاینت Groq
client = Groq(api_key=GROQ_API_KEY)

# تابع خوش‌آمدگویی با عکس و متن تو
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # باز کردن فایل عکس از پوشه images
        with open('images/welcome.jpg', 'rb') as photo:
            caption = """سلام سلام
شهبازی هستم، مریم 😍🌱
اینجا قراره هویت کسب و کار و برند خودتون رو بسازید و روز به روز فروش بیشتری رو تجربه کنین. 
با من همراه باش"""
            
            # ارسال عکس به همراه متن
            await update.message.reply_photo(
                photo=photo, 
                caption=caption
            )
    except FileNotFoundError:
        # اگه عکس پیدا نشد، فقط متن بفرست
        await update.message.reply_text(
            """سلام سلام
شهبازی هستم، مریم 😍🌱
اینجا قراره هویت کسب و کار و برند خودتون رو بسازید و روز به روز فروش بیشتری رو تجربه کنین. 
با من همراه باش"""
        )

# تابع پاسخگویی به پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # چک کردن دستور start
    if update.message.text == "/start":
        await start(update, context)
        return
    
    user_text = update.message.text
    
    try:
        # ارسال درخواست به Groq
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
        error_message = f"⚠️ خطایی رخ داد: {str(e)}"
        await update.message.reply_text(error_message)

# ساختن اپلیکیشن
app = ApplicationBuilder().token(BOT_TOKEN).build()

# اضافه کردن هندلرها
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 بات با موفقیت روشن شد...")
print("منتظر پیام‌های کاربران هستم...")

# اجرای بات
app.run_polling()