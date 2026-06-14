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

# ==================== توابع خواندن و نوشتن JSON ====================
def read_json(file_path, default={}):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default
    return default

def write_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==================== توابع ذخیره اطلاعات ====================
def save_user_info(user_id, info):
    users = read_json(USERS_FILE, {})
    if str(user_id) not in users:
        users[str(user_id)] = {}
    users[str(user_id)].update(info)
    users[str(user_id)]["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_json(USERS_FILE, users)

def save_survey_answer(user_id, section, answer):
    surveys = read_json(SURVEY_FILE, {})
    if str(user_id) not in surveys:
        surveys[str(user_id)] = {}
    surveys[str(user_id)][section] = answer
    surveys[str(user_id)]["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_json(SURVEY_FILE, surveys)

def get_user_info(user_id):
    users = read_json(USERS_FILE, {})
    return users.get(str(user_id), {})

def get_user_survey(user_id):
    surveys = read_json(SURVEY_FILE, {})
    return surveys.get(str(user_id), {})

# ==================== منوی اصلی ====================
main_menu = ReplyKeyboardMarkup([
    [KeyboardButton("🆔 اطلاعات شخصی")],
    [KeyboardButton("🏢 اطلاعات کسب و کار")],
    [KeyboardButton("📊 پرسشنامه تخصصی")],
    [KeyboardButton("💬 گفتگو با مشاور")]
], resize_keyboard=True)

# دکمه بازگشت به منو
back_menu = ReplyKeyboardMarkup([
    [KeyboardButton("🔙 بازگشت به منوی اصلی")]
], resize_keyboard=True)

# ==================== سوالات هر بخش ====================
personal_info_questions = [
    ("first_name", "نام خود را وارد کنید:"),
    ("last_name", "نام خانوادگی خود را وارد کنید:"),
    ("birth_date", "تاریخ تولد (مثال: 1370/05/15):"),
    ("phone", "شماره تماس موبایل:"),
]

business_info_questions = [
    ("business_name", "نام کسب و کار خود را وارد کنید:"),
    ("address", "آدرس شعب / دفتر مرکزی:"),
    ("referral_source", "از چه طریقی با ما آشنا شدید؟"),
]

survey_questions = [
    ("about_business", "1️⃣ درباره کسب و کار خود بنویسید:\n(فعالیت، سابقه، اهداف)"),
    ("products", "2️⃣ چه محصولات یا خدماتی دارید؟\nمزیت شما نسبت به رقبا چیست؟"),
    ("infrastructure", "3️⃣ چه زیرساخت‌های مجازی دارید؟\n(سایت، اینستاگرام، اپلیکیشن، ...)"),
    ("team", "4️⃣ تیم شما شامل چه نیروهایی است؟\n(تعداد و تخصص)"),
    ("sales", "5️⃣ بالاترین فروش ماهیانه شما چقدر بوده؟"),
    ("problem", "6️⃣ مهمترین چالش یا مشکل فعلی شما چیست؟"),
    ("consulting", "7️⃣ در چه زمینه‌ای نیاز به مشاوره دارید؟")
]

# ==================== وضعیت کاربران ====================
user_states = {}  # {user_id: {"section": "personal", "step": 0, "temp": {}}}

def get_user_state(user_id):
    return user_states.get(user_id, {"section": None, "step": 0, "temp": {}})

def set_user_state(user_id, section, step=0, temp=None):
    user_states[user_id] = {
        "section": section,
        "step": step,
        "temp": temp if temp else {}
    }

def clear_user_state(user_id):
    if user_id in user_states:
        del user_states[user_id]

# ==================== دستور start ====================
async def start(update: Update, context):
    user_id = update.effective_user.id
    
    # نمایش عکس خوش‌آمدگویی
    try:
        with open('images/welcome.jpg', 'rb') as photo:
            caption = """سلام سلام
شهبازی هستم، مریم 😍🌱
اینجا قراره هویت کسب و کار و برند خودتون رو بسازید و روز به روز فروش بیشتری رو تجربه کنین. 
با من همراه باش

از منوی زیر گزینه مورد نظر خود را انتخاب کنید 👇"""
            await update.message.reply_photo(
                photo=photo,
                caption=caption,
                reply_markup=main_menu
            )
    except FileNotFoundError:
        await update.message.reply_text(
            """سلام سلام
شهبازی هستم، مریم 😍🌱
اینجا قراره هویت کسب و کار و برند خودتون رو بسازید و روز به روز فروش بیشتری رو تجربه کنین. 
با من همراه باش

از منوی زیر گزینه مورد نظر خود را انتخاب کنید 👇""",
            reply_markup=main_menu
        )

# ==================== پردازش منو ====================
async def handle_menu(update: Update, context):
    user_id = update.effective_user.id
    text = update.message.text
    
    # بازگشت به منوی اصلی
    if text == "🔙 بازگشت به منوی اصلی":
        clear_user_state(user_id)
        await update.message.reply_text("به منوی اصلی بازگشتید 👇", reply_markup=main_menu)
        return
    
    # ========== منوی اطلاعات شخصی ==========
    if text == "🆔 اطلاعات شخصی":
        set_user_state(user_id, "personal", 0, {})
        await update.message.reply_text(
            "📝 **ثبت اطلاعات شخصی**\n\n"
            f"{personal_info_questions[0][1]}\n\n"
            "💡 می‌توانید هر زمان که خواستید با دکمه 'بازگشت به منوی اصلی' برگردید.",
            reply_markup=back_menu,
            parse_mode='Markdown'
        )
        return
    
    # ========== منوی اطلاعات کسب و کار ==========
    if text == "🏢 اطلاعات کسب و کار":
        set_user_state(user_id, "business", 0, {})
        await update.message.reply_text(
            "🏢 **ثبت اطلاعات کسب و کار**\n\n"
            f"{business_info_questions[0][1]}\n\n"
            "💡 می‌توانید هر زمان که خواستید با دکمه 'بازگشت به منوی اصلی' برگردید.",
            reply_markup=back_menu,
            parse_mode='Markdown'
        )
        return
    
    # ========== منوی پرسشنامه تخصصی ==========
    if text == "📊 پرسشنامه تخصصی":
        # چک کنید که کاربر قبلاً اطلاعات شخصی و کسب و کار رو پر کرده؟
        user_info = get_user_info(user_id)
        if not user_info.get("first_name"):
            await update.message.reply_text(
                "⚠️ لطفاً ابتدا اطلاعات خود را در بخش‌های زیر ثبت کنید:\n"
                "• 🆔 اطلاعات شخصی\n"
                "• 🏢 اطلاعات کسب و کار\n\n"
                "سپس می‌توانید پرسشنامه را پر کنید.",
                reply_markup=main_menu
            )
            return
        
        set_user_state(user_id, "survey", 0, {})
        await update.message.reply_text(
            "📋 **پرسشنامه تخصصی**\n\n"
            f"{survey_questions[0][1]}\n\n"
            "💡 پاسخ‌های دقیق‌تر به ما کمک می‌کند مشاوره بهتری به شما ارائه دهیم.",
            reply_markup=back_menu,
            parse_mode='Markdown'
        )
        return
    
    # ========== گفتگو با مشاور (Groq) ==========
    if text == "💬 گفتگو با مشاور":
        user_info = get_user_info(user_id)
        if not user_info.get("first_name"):
            await update.message.reply_text(
                "⚠️ لطفاً ابتدا در بخش 'اطلاعات شخصی' ثبت‌نام کنید.\n\n"
                "سپس می‌توانید با مشاور گفتگو کنید.",
                reply_markup=main_menu
            )
            return
        
        await update.message.reply_text(
            "💬 **گفتگو با مشاور هوشمند**\n\n"
            "سلام! من مریم هستم، مشاور کسب و کار شما.\n"
            "هر سوالی درباره برندسازی، بازاریابی، فروش و... داری بپرس.\n\n"
            "برای بازگشت به منو، روی دکمه زیر کلیک کن 👇",
            reply_markup=back_menu,
            parse_mode='Markdown'
        )
        return
    
    # ========== پردازش پاسخ‌های کاربر در حالت ثبت اطلاعات ==========
    state = get_user_state(user_id)
    section = state["section"]
    step = state["step"]
    temp = state["temp"]
    
    # پردازش اطلاعات شخصی
    if section == "personal":
        if step < len(personal_info_questions):
            field_name, _ = personal_info_questions[step]
            temp[field_name] = text
            
            if step + 1 < len(personal_info_questions):
                set_user_state(user_id, "personal", step + 1, temp)
                _, next_q = personal_info_questions[step + 1]
                await update.message.reply_text(next_q, reply_markup=back_menu)
            else:
                # ذخیره اطلاعات شخصی
                save_user_info(user_id, temp)
                clear_user_state(user_id)
                
                summary = f"✅ **اطلاعات شخصی شما ثبت شد:**\n\n"
                summary += f"👤 نام: {temp.get('first_name', '')}\n"
                summary += f"👨‍👩‍👧 نام خانوادگی: {temp.get('last_name', '')}\n"
                summary += f"📅 تاریخ تولد: {temp.get('birth_date', '')}\n"
                summary += f"📞 شماره تماس: {temp.get('phone', '')}\n\n"
                summary += "به منوی اصلی بازگشتید 👇"
                
                await update.message.reply_text(summary, reply_markup=main_menu, parse_mode='Markdown')
        return
    
    # پردازش اطلاعات کسب و کار
    if section == "business":
        if step < len(business_info_questions):
            field_name, _ = business_info_questions[step]
            temp[field_name] = text
            
            if step + 1 < len(business_info_questions):
                set_user_state(user_id, "business", step + 1, temp)
                _, next_q = business_info_questions[step + 1]
                await update.message.reply_text(next_q, reply_markup=back_menu)
            else:
                # ذخیره اطلاعات کسب و کار
                save_user_info(user_id, temp)
                clear_user_state(user_id)
                
                summary = f"✅ **اطلاعات کسب و کار شما ثبت شد:**\n\n"
                summary += f"🏢 نام کسب و کار: {temp.get('business_name', '')}\n"
                summary += f"📍 آدرس: {temp.get('address', '')}\n"
                summary += f"📢 راه معرفی: {temp.get('referral_source', '')}\n\n"
                summary += "به منوی اصلی بازگشتید 👇"
                
                await update.message.reply_text(summary, reply_markup=main_menu, parse_mode='Markdown')
        return
    
    # پردازش پرسشنامه
    if section == "survey":
        if step < len(survey_questions):
            field_name, _ = survey_questions[step]
            temp[field_name] = text
            
            if step + 1 < len(survey_questions):
                set_user_state(user_id, "survey", step + 1, temp)
                _, next_q = survey_questions[step + 1]
                await update.message.reply_text(next_q, reply_markup=back_menu)
            else:
                # ذخیره پرسشنامه
                for key, value in temp.items():
                    save_survey_answer(user_id, key, value)
                clear_user_state(user_id)
                
                await update.message.reply_text(
                    "🌹 **با تشکر از شما!** 🌹\n\n"
                    "پرسشنامه شما با موفقیت ثبت شد.\n"
                    "✅ **ظرف ۴۸ ساعت آینده کارشناسان ما با شما تماس می‌گیرند.**\n\n"
                    "تا آن زمان می‌توانید از بخش 'گفتگو با مشاور' سوالات خود را بپرسید.\n\n"
                    "به منوی اصلی بازگشتید 👇",
                    reply_markup=main_menu,
                    parse_mode='Markdown'
                )
        return
    
    # ========== گفتگو با Groq ==========
    if state["section"] is None:
        user_info = get_user_info(user_id)
        if user_info.get("first_name"):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"""تو یک مشاور کسب و کار حرفه‌ای هستی به نام مریم شهبازی.
                        اطلاعات کاربر: نام: {user_info.get('first_name', '')} {user_info.get('last_name', '')}
                        کسب و کار: {user_info.get('business_name', '')}
                        با لحنی گرم و دوستانه پاسخ بده. حتما به فارسی روان پاسخ بده."""},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                await update.message.reply_text(response.choices[0].message.content, reply_markup=back_menu)
            except Exception as e:
                await update.message.reply_text(f"⚠️ خطا: {str(e)}", reply_markup=back_menu)
        else:
            await update.message.reply_text(
                "⚠️ لطفاً ابتدا در بخش 'اطلاعات شخصی' ثبت‌نام کنید.",
                reply_markup=main_menu
            )

# ==================== دستورات ادمین ====================
async def get_data(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید!")
        return
    
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'rb') as f:
            await update.message.reply_document(f, filename='users.json')
    
    if os.path.exists(SURVEY_FILE):
        with open(SURVEY_FILE, 'rb') as f:
            await update.message.reply_document(f, filename='survey.json')

async def show_summary(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید!")
        return
    
    users = read_json(USERS_FILE, {})
    surveys = read_json(SURVEY_FILE, {})
    
    completed_surveys = sum(1 for uid in surveys if len(surveys[uid]) > 2)
    
    summary = f"📊 **آمار کلی:**\n"
    summary += f"- 👥 کاربران ثبت‌نام شده: {len(users)}\n"
    summary += f"- 📋 پرسشنامه‌های تکمیل شده: {completed_surveys}\n\n"
    summary += "**آخرین کاربران:**\n"
    
    for i, (uid, info) in enumerate(list(users.items())[-5:]):
        name = f"{info.get('first_name', '')} {info.get('last_name', '')}"
        business = info.get('business_name', 'نامشخص')
        summary += f"{i+1}. {name} - {business}\n"
    
    await update.message.reply_text(summary, parse_mode='Markdown')

# ==================== اجرا ====================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("getdata", get_data))
app.add_handler(CommandHandler("summary", show_summary))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

print("🤖 بات با منوی دکمه‌ای روشن شد...")
print("📁 اطلاعات در فایل‌های JSON ذخیره می‌شوند")
app.run_polling()