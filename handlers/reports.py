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

        c.execute("SELECT COALESCE(SUM(amount),0) FROM budget WHERE created_at LIKE %s",
                  (f"{date_filter}%",))
        total_budget = c.fetchone()[0]

        c.execute("SELECT source, COALESCE(SUM(amount),0) FROM budget WHERE created_at LIKE %s GROUP BY source",
                  (f"{date_filter}%",))
        income_by_source = c.fetchall()

        c.execute("SELECT name, amount FROM credits WHERE is_active=1")
        credits = c.fetchall()
        credit_total = sum(a for _, a in credits)

        c.execute("SELECT name, amount FROM fixed_expenses WHERE is_active=1")
        fixed = c.fetchall()
        fixed_total = sum(a for _, a in fixed)

        c.execute("SELECT category, COALESCE(SUM(amount),0) FROM other_expenses WHERE created_at LIKE %s GROUP BY category",
                  (f"{date_filter}%",))
        other_by_cat = c.fetchall()
        other_total = sum(a for _, a in other_by_cat)

        month = date_filter if len(date_filter) == 7 else now.strftime("%Y-%m")
        c.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE month=%s AND status='paid'",
                  (month,))
        paid_total = c.fetchone()[0]
        conn.close()

        planned_total = credit_total + fixed_total
        remaining = total_budget - paid_total - other_total
        after_planned = total_budget - planned_total - other_total

        text = f"{title}\n\n"
        text += f"💼 Улыума бюджет: {total_budget:,.0f} сум\n\n"

        text += "📥 Кириc:\n"
        if income_by_source:
            for source, amount in income_by_source:
                text += f"  • {source}: +{amount:,.0f} сум\n"
        else:
            text += "  • Жоқ\n"

        text += "\n🔴 Кредитлер:\n"
        for name, amount in credits:
            text += f"  • {name}: {amount:,.0f} сум\n"
        text += f"  Улыума: -{credit_total:,.0f} сум\n"

        text += "\n🟡 Тұрақлы харажатлар:\n"
        for name, amount in fixed:
            text += f"  • {name}: {amount:,.0f} сум\n"
        text += f"  Улыума: -{fixed_total:,.0f} сум\n"

        if other_by_cat:
            text += "\n🟢 Басқа харажатлар:\n"
            for cat, amt in other_by_cat:
                text += f"  • {cat}: -{amt:,.0f} сум\n"
            text += f"  Улыума: -{other_total:,.0f} сум\n"

        text += f"\n📊 Ойласылған: -{planned_total:,.0f} сум\n"
        text += f"✅ Төленген: -{paid_total:,.0f} сум\n"
        text += f"\n──────────────────\n"
        text += f"💰 Қолда бар: {remaining:,.0f} сум\n"

        if after_planned >= 0:
            text += f"📉 Барлығы төленсе қалады: {after_planned:,.0f} сум"
        else:
            text += f"⚠️ Барлығы төленсе жетиспейди: {after_planned:,.0f} сум"

        bot.send_message(call.message.chat.id, text)
