import sqlite3
from datetime import datetime

DB_NAME = "budget.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER UNIQUE,
        name TEXT,
        is_admin INTEGER DEFAULT 0,
        created_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS budget (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        source TEXT,
        amount REAL,
        created_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS credits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        amount REAL,
        pay_day INTEGER,
        is_active INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS fixed_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        amount REAL,
        is_active INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS other_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        category TEXT,
        amount REAL,
        comment TEXT,
        created_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        c.executemany("INSERT INTO credits (name, amount, pay_day) VALUES (?,?,?)", credits)

    # Тұрақлы харажатларды алдын ала қосыў
    c.execute("SELECT COUNT(*) FROM fixed_expenses")
    if c.fetchone()[0] == 0:
        fixed = [
            ("Квартира", 0),
            ("Коммунал төлем", 0),
            ("Бала таярлығы", 0),
        ]
        c.executemany("INSERT INTO fixed_expenses (name, amount) VALUES (?,?)", fixed)

    conn.commit()
    conn.close()

def get_conn():
    return sqlite3.connect(DB_NAME)
