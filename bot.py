import telebot
import os
import threading
from flask import Flask
from dotenv import load_dotenv
from datetime import datetime
from database import init_db, get_conn
from scheduler import start_scheduler
from handlers.budget import register_budget_handlers
from handlers.expenses import register_expense_handlers
from handlers.reports import register_report_handlers

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

init_db()

@app.route('/')
def home():
    return "Бот жұмыс істеп тур! ✅"

def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🏠 Баслапқы бет")
    markup.row("➕ Бюджет қосыў", "➕ Харажат қосыў")
    markup.row("📊 Есап", "⚙️ Өзгертиў")
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id=%s", (message.from_user.id,))
    user = c.fetchone()
    if not user:
        is_admin = 1 if message.from_user.id == ADMIN_ID else 0
        c.execute("INSERT INTO users (telegram_id, name, is_admin, created_at) VALUES (%s,%s,%s,%s)",
                  (message.from_user.id, message.from_user.first_name, is_admin, str(datetime.now())))
        conn.commit()
    conn.close()
    bot.send_message(message.chat.id,
                     f"Ассалаума алейкум, {message.from_user.first_name}! 👋\nБюджет ботына хош келдиңиз!",
                     reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🏠 Баслапқы бет")
def dashboard(message):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(amount),0) FROM budget")
    total_budget = c.fetchone()[0]
    c.execute("SELECT name, amount, pay_day FROM credits WHERE is_active=1")
    credits = c.fetchall()
    c.execute("SELECT name, amount, pay_day FROM fixed_expenses WHERE is_active=1")
    fixed = c.fetchall()
    month = datetime.now().strftime("%Y-%m")
    c.execute("SELECT COALESCE(SUM(amount),0) FROM other_expenses WHERE created_at LIKE %s",
              (f"{month}%",))
    other = c.fetchone()[0]
    conn.close()

    credit_total = sum(a for _, a, _ in credits)
    fixed_total = sum(a for _, a, _ in fixed)
    remaining = total_budget - credit_total - fixed_total - other

    months_kk = {
        1: "январь", 2: "февраль", 3: "март", 4: "апрель",
        5: "май", 6: "июнь", 7: "июль", 8: "август",
        9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь"
    }
    cur_month = months_kk[datetime.now().month]

    text = f"💼 Бюджет: {total_budget:,.0f} сум\n\n"
    text += "🔴 Кредитлер:\n"
    for name, amount, pay_day in credits:
        text += f"  • {name}: -{amount:,.0f} сум ({pay_day}-{cur_month})\n"
    text += "\n🟡 Тұрақлы харажатлар:\n"
    for name, amount, pay_day in fixed:
        text += f"  • {name}: -{amount:,.0f} сум ({pay_day}-{cur_month})\n"
    text += f"\n🟢 Басқа харажатлар: -{other:,.0f} сум\n"
    text += f"\n──────────────────\n"
    text += f"💰 Қалған бюджет: {remaining:,.0f} сум"

    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "⚙️ Өзгертиў")
def settings(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Бул бөлим тек админ ушын!")
        return
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("💳 Кредит өзгертиў", callback_data="set_credit"))
    markup.add(telebot.types.InlineKeyboardButton("🏠 Тұрақлы харажат өзгертиў", callback_data="set_fixed"))
    bot.send_message(message.chat.id, "⚙️ Не өзгертесиз?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "set_credit")
def set_credit_menu(call):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name, amount, pay_day FROM credits WHERE is_active=1")
    credits = c.fetchall()
    conn.close()
    markup = telebot.types.InlineKeyboardMarkup()
    for cid, name, amount, pay_day in credits:
        markup.add(telebot.types.InlineKeyboardButton(
            f"{name}: {amount:,.0f} сум ({pay_day}-күн)",
            callback_data=f"ec_{cid}"
        ))
    bot.send_message(call.message.chat.id, "Қайси кредитти өзгертесиз?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ec_"))
def edit_credit(call):
    cid = int(call.data.split("_")[1])
    msg = bot.send_message(call.message.chat.id,
                           "Жаңа сомма жаз (сум):\nМысалы: 450000")
    bot.register_next_step_handler(msg, save_credit_amount, cid)

def save_credit_amount(message, cid):
    try:
        amount = float(message.text.replace(",", "").replace(" ", ""))
        msg = bot.send_message(message.chat.id,
                               "Төлем күнин жаз (1-31):\nМысалы: 15")
        bot.register_next_step_handler(msg, save_credit_day, cid, amount)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Қате! Тек сан жазың.")

def save_credit_day(message, cid, amount):
    try:
        day = int(message.text.strip())
        if not 1 <= day <= 31:
            raise ValueError
        conn = get_conn()
        c = conn.cursor()
        c.execute("UPDATE credits SET amount=?, pay_day=? WHERE id=?",
                  (amount, day, cid))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id,
                         f"✅ Жаңартылды!\n"
                         f"• Сомма: {amount:,.0f} сум\n"
                         f"• Төлем күни: {day}-күн")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Қате! 1-31 арасында жазың.")

@bot.callback_query_handler(func=lambda call: call.data == "set_fixed")
def set_fixed_menu(call):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name, amount FROM fixed_expenses WHERE is_active=1")
    fixed = c.fetchall()
    conn.close()
    markup = telebot.types.InlineKeyboardMarkup()
    for fid, name, amount in fixed:
        markup.add(telebot.types.InlineKeyboardButton(
            f"{name}: {amount:,.0f} сум",
            callback_data=f"ef_{fid}"
        ))
    bot.send_message(call.message.chat.id, "Қайси харажатты өзгертесиз?",
                     reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ef_"))
def edit_fixed(call):
    fid = int(call.data.split("_")[1])
    msg = bot.send_message(call.message.chat.id,
                           "Жаңа сомма жаз (сум):\nМысалы: 600000")
    bot.register_next_step_handler(msg, save_fixed_amount, fid)

def save_fixed_amount(message, fid):
    try:
        amount = float(message.text.replace(",", "").replace(" ", ""))
        msg = bot.send_message(message.chat.id,
                               "Төлем күнин жаз (1-31):\nМысалы: 5")
        bot.register_next_step_handler(msg, save_fixed_day, fid, amount)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Қате! Тек сан жазың.")

def save_fixed_day(message, fid, amount):
    try:
        day = int(message.text.strip())
        if not 1 <= day <= 31:
            raise ValueError
        conn = get_conn()
        c = conn.cursor()
        c.execute("UPDATE fixed_expenses SET amount=? WHERE id=?", (amount, fid))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id,
                         f"✅ Жаңартылды!\n"
                         f"• Сомма: {amount:,.0f} сум\n"
                         f"• Төлем күни: {day}-күн")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Қате! 1-31 арасында жазың.")

register_budget_handlers(bot)
register_expense_handlers(bot)
register_report_handlers(bot)
start_scheduler(bot, ADMIN_ID)

def run_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
