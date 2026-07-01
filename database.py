def reset_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS payments")
    c.execute("DROP TABLE IF EXISTS other_expenses")
    c.execute("DROP TABLE IF EXISTS fixed_expenses")
    c.execute("DROP TABLE IF EXISTS credits")
    c.execute("DROP TABLE IF EXISTS budget")
    c.execute("DROP TABLE IF EXISTS users")
    conn.commit()
    conn.close()
import psycopg2
import os

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
        pay_day INTEGER DEFAULT 1,
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

    c.execute("SELECT COUNT(*) FROM credits")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO credits (name, amount, pay_day) VALUES (%s,%s,%s)", [
            ("Солнечный панель", 0, 1),
            ("Талим кредит", 0, 1),
            ("Миллий кредит", 0, 1),
        ])

    c.execute("SELECT COUNT(*) FROM fixed_expenses")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO fixed_expenses (name, amount, pay_day) VALUES (%s,%s,%s)", [
            ("Квартира", 0, 1),
            ("Бала таярлығы", 0, 1),
        ])

    conn.commit()
    conn.close()
