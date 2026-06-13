import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from groq import Groq

# خواندن توکن‌ها از متغیرهای محیطی
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ارسال عکس همراه با متن خوش‌آمدگویی
    photo_url = "https://your-image-url.com/welcome.jpg"  # یه لینک معتبر برای عکس بذار
    caption = """🤖 به بات هوش مصنوعی خوش اومدی!

من میتونم به هر سوالی جواب بدم. فقط کافیه سوالت رو بپرسی.

✨ **قابلیت‌ها:**
- پاسخ به سوالات عمومی
- کمک در برنامه‌نویسی
- مشاوره و راهنمایی

📝 **فقط سوالت رو بپرس...**"""
    
    await update.message.reply_photo(photo=photo_url, caption=caption)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # اگه کاربر دستور start رو فرستاد
    if update.message.text == "/start":
        await start(update, context)
        return
    
    user_text = update.message.text
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": user_text
                }
            ]
        )
        
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)
        
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطایی رخ داد: {str(e)}")

# ساختن اپلیکیشن
app = ApplicationBuilder().token(BOT_TOKEN).build()

# اضافه کردن هندلرها
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 بات با موفقیت روشن شد...")

app.run_polling()