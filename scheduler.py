import telebot
from apscheduler.schedulers.background import BackgroundScheduler
from database import get_conn
from datetime import datetime, timedelta

def start_scheduler(bot, admin_id):
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_credit_reminders, 'cron', hour=9, minute=0,
                      args=[bot, admin_id])
    scheduler.add_job(monthly_payment_reminder, 'cron', day=1, hour=9, minute=0,
                      args=[bot, admin_id])
    scheduler.start()

def check_credit_reminders(bot, admin_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT name, amount, pay_day FROM credits WHERE is_active=1")
    credits = c.fetchall()
    conn.close()

    today = datetime.now()
    remind_date = (today + timedelta(days=2)).day
    reminders = [(n, a, p) for n, a, p in credits if p == remind_date]

    if reminders:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT telegram_id FROM users")
        users = c.fetchall()
        conn.close()

        months_kk = {
            1: "январь", 2: "февраль", 3: "март", 4: "апрель",
            5: "май", 6: "июнь", 7: "июль", 8: "август",
            9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь"
        }
        cur_month = months_kk[today.month]

        text = "🔔 2 күннен кейин төлем!\n\n"
        for name, amount, pay_day in reminders:
            text += f"• {name}: {amount:,.0f} сум\n"
            text += f"  Төлем күні: {pay_day}-{cur_month}\n\n"

        for (telegram_id,) in users:
            try:
                bot.send_message(telegram_id, text)
            except:
                pass

def monthly_payment_reminder(bot, admin_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name, amount FROM credits WHERE is_active=1")
    credits = c.fetchall()
    c.execute("SELECT id, name, amount FROM fixed_expenses WHERE is_active=1")
    fixed = c.fetchall()
    c.execute("SELECT telegram_id FROM users")
    users = c.fetchall()
    conn.close()

    markup = telebot.types.InlineKeyboardMarkup()
    text = "📅 Таза ай басланды!\nТөлемлерди раслаң:\n\n"

    for cid, name, amount in credits:
        text += f"💳 {name}: {amount:,.0f} сум\n"
        markup.add(telebot.types.InlineKeyboardButton(
            f"✅ {name} төледим",
            callback_data=f"pc_{cid}"
        ))

    for fid, name, amount in fixed:
        text += f"🏠 {name}: {amount:,.0f} сум\n"
        markup.add(telebot.types.InlineKeyboardButton(
            f"✅ {name} төледим",
            callback_data=f"pf_{fid}"
        ))

    for (telegram_id,) in users:
        try:
            bot.send_message(telegram_id, text, reply_markup=markup)
        except:
            pass
