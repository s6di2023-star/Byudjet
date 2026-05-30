from database import get_conn
from datetime import datetime
import telebot

def register_report_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "📊 Есап")
    def report_period(message):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("📅 Бүгин", callback_data="rep_today"))
        markup.add(telebot.types.InlineKeyboardButton("📅 Бул ай", callback_data="rep_month"))
        markup.add(telebot.types.InlineKeyboardButton("📅 Өткен ай", callback_data="rep_last"))
        bot.send_message(message.chat.id, "Есап дәўирин таңла:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("rep_"))
    def show_report(call):
        conn = get_conn()
        c = conn.cursor()
        now = datetime.now()

        if call.data == "rep_today":
            date_filter = now.strftime("%Y-%m-%d")
            title = f"📊 Бүгинги есап ({date_filter})"
        elif call.data == "rep_month":
            date_filter = now.strftime("%Y-%m")
            title = f"📊 {now.strftime('%B %Y')} есабы"
        else:
            if now.month == 1:
                last = now.replace(year=now.year - 1, month=12)
            else:
                last = now.replace(month=now.month - 1)
            date_filter = last.strftime("%Y-%m")
            title = f"📊 {last.strftime('%B %Y')} есабы"

        c.execute(
            "SELECT COALESCE(SUM(amount),0) FROM budget WHERE created_at LIKE ?",
            (f"{date_filter}%",))
        total_budget = c.fetchone()[0]

        c.execute(
            "SELECT source, COALESCE(SUM(amount),0) FROM budget WHERE created_at LIKE ? GROUP BY source",
            (f"{date_filter}%",))
        income_by_source = c.fetchall()

        c.execute("SELECT name, amount FROM credits WHERE is_active=1")
        credits = c.fetchall()
        credit_total = sum(a for _, a in credits)

        c.execute("SELECT name, amount FROM fixed_expenses WHERE is_active=1")
        fixed = c.fetchall()
        fixed_total = sum(a for _, a in fixed)

        c.execute(
            "SELECT COALESCE(SUM(amount),0) FROM other_expenses WHERE created_at LIKE ?",
            (f"{date_filter}%",))
        other_total = c.fetchone()[0]
        conn.close()

        remaining = total_budget - credit_total - fixed_total - other_total

        text = f"{title}\n\n"
        text += f"💼 Жалпы бюджет: {total_budget:,.0f} сум\n\n"
        text += "📥 Кириc:\n"
        for source, amount in income_by_source:
            text += f"  • {source}: +{amount:,.0f} сум\n"
        text += f"\n📤 Харажатлар:\n"
        text += f"  🔴 Кредитлер: -{credit_total:,.0f} сум\n"
        text += f"  🟡 Тұрақлы: -{fixed_total:,.0f} сум\n"
        text += f"  🟢 Басқа: -{other_total:,.0f} сум\n"
        text += f"\n──────────────────\n"
        text += f"💰 Қалған бюджет: {remaining:,.0f} сум"

        bot.send_message(call.message.chat.id, text)
