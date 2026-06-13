FROM python:3.11-slim

WORKDIR /app

# کپی فایل requirements و نصب کتابخانه‌ها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کل پروژه
COPY . .

# اجرای بات
CMD ["python", "bot.py"]