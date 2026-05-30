import psycopg2
import os
from datetime import datetime

def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE,
        name TEXT,
        is_admin INTEGER DEFAULT 0,
        created_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS budget (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT,
        source TEXT,
        amount REAL,
        created_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS credits (
        id SERIAL PRIMARY KEY,
        name TEXT,
        amount REAL,
        pay_day INTEGER,
        is_active INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS fixed_expenses (
        id SERIAL PRIMARY KEY,
        name TEXT,
        amount REAL,
        pay_day INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS other_expenses (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT,
        category TEXT,
        amount REAL,
        comment TEXT,
        created_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS payments (
        id SERIAL PRIMARY KEY,
        type TEXT,
        ref_id INTEGER,
        amount REAL,
        status TEXT,
        month TEXT,
        created_at TEXT
    )''')

    # Кредиттерді алдын ала қосыў
    c.execute("SELECT COUNT(*) FROM credits")
    if c.fetchone()[0] == 0:
        credits = [
            ("Солнечный панель", 0, 1),
            ("Талим кредит", 0, 1),
            ("Миллий кредит", 0, 1),
        ]
        c.executemany("INSERT INTO credits (name, amount, pay_day) VALUES (%s,%s,%s)", credits)

    # Тұрақлы харажатларды алдын ала қосыў
    c.execute("SELECT COUNT(*) FROM fixed_expenses")
    if c.fetchone()[0] == 0:
        fixed = [
            ("Квартира", 0, 1),
            ("Коммунал төлем", 0, 1),
            ("Бала таярлығы", 0, 1),
        ]
        c.executemany("INSERT INTO fixed_expenses (name, amount, pay_day) VALUES (%s,%s,%s)", fixed)

    conn.commit()
    conn.close()
