import sqlite3
import os

DB_PATH = "users_data.db"

def init_db():
    """ایجاد جدول‌های دیتابیس"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # جدول اصلی کاربران
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            business_name TEXT,
            birth_date TEXT,
            phone TEXT,
            address TEXT,
            referral_source TEXT,
            register_date TEXT
        )
    ''')
    
    # جدول پاسخ‌های پرسشنامه
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questionnaire (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            about_business TEXT,
            products_advantages TEXT,
            virtual_infrastructure TEXT,
            team_members TEXT,
            max_monthly_sales TEXT,
            current_problem TEXT,
            consultation_fields TEXT,
            submit_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # جدول وضعیت ثبت‌نام کاربران
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registration_state (
            user_id INTEGER PRIMARY KEY,
            step INTEGER DEFAULT 0,
            temp_data TEXT,
            questionnaire_step INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()

def save_user_info(user_id, data):
    """ذخیره اطلاعات شخصی کاربر"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (user_id, first_name, last_name, business_name, birth_date, phone, address, referral_source, register_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (
        user_id, data['first_name'], data['last_name'], data['business_name'],
        data['birth_date'], data['phone'], data['address'], data['referral_source']
    ))
    conn.commit()
    conn.close()

def save_questionnaire(user_id, answers):
    """ذخیره پاسخ‌های پرسشنامه"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO questionnaire 
        (user_id, about_business, products_advantages, virtual_infrastructure, 
         team_members, max_monthly_sales, current_problem, consultation_fields, submit_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (
        user_id, answers['about_business'], answers['products_advantages'],
        answers['virtual_infrastructure'], answers['team_members'],
        answers['max_monthly_sales'], answers['current_problem'], answers['consultation_fields']
    ))
    conn.commit()
    conn.close()

def get_user_step(user_id):
    """دریافت مرحله ثبت‌نام کاربر"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT step, temp_data, questionnaire_step FROM registration_state WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {'step': result[0], 'temp_data': result[1], 'questionnaire_step': result[2]}
    return {'step': 0, 'temp_data': None, 'questionnaire_step': 0}

def update_user_step(user_id, step, temp_data=None, questionnaire_step=0):
    """به‌روزرسانی مرحله ثبت‌نام کاربر"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO registration_state (user_id, step, temp_data, questionnaire_step)
        VALUES (?, ?, ?, ?)
    ''', (user_id, step, temp_data, questionnaire_step))
    conn.commit()
    conn.close()

def get_all_users_data():
    """دریافت تمام اطلاعات کاربران (برای دسترسی تو)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.*, q.* 
        FROM users u
        LEFT JOIN questionnaire q ON u.user_id = q.user_id
        ORDER BY u.register_date DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    return results