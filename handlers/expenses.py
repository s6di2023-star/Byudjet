from database import get_conn
from datetime import datetime
import telebot

def register_expense_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "➕ Харажат қосыў")
    def expense_type(message):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔴 Кредит төлеми", callback_data="exp_credit"))
        markup.add(telebot.types.InlineKeyboardButton("🟡 Тұрақлы харажат", callback_data="exp_fixed"))
        markup.add(telebot.types.InlineKeyboardButton("🟢 Басқа харажат", callback_data="exp_other"))
        bot.send_message(message.chat.id, "Харажат түрин таңла:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == "exp_credit")
    def show_credits(call):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, name, amount FROM credits WHERE is_active=1")
        credits = c.fetchall()
        conn.close()
        markup = telebot.types.InlineKeyboardMarkup()
        for cid, name, amount in credits:
            markup.add(telebot.types.InlineKeyboardButton(
                f"{name}: {amount:,.0f} сум",
                callback_data=f"pc_{cid}"
            ))
        bot.send_message(call.message.chat.id, "Қайси кредит?", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == "exp_fixed")
    def show_fixed(call):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, name, amount FROM fixed_expenses WHERE is_active=1")
        fixed = c.fetchall()
        conn.close()
        markup = telebot.types.InlineKeyboardMarkup()
        for fid, name, amount in fixed:
            markup.add(telebot.types.InlineKeyboardButton(
                f"{name}: {amount:,.0f} сум",
                callback_data=f"pf_{fid}"
            ))
        bot.send_message(call.message.chat.id, "Қайси харажат?", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == "exp_other")
    def other_category(call):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🛒 Азық-түлик", callback_data="oth_azyk"))
        markup.add(telebot.types.InlineKeyboardButton("🚗 Көлик", callback_data="oth_kolik"))
        markup.add(telebot.types.InlineKeyboardButton("📦 Басқа", callback_data="oth_baska"))
        bot.send_message(call.message.chat.id, "Категория таңла:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("oth_"))
    def other_amount(call):
        categories = {
            "oth_azyk": "Азық-түлик",
            "oth_kolik": "Көлик",
            "oth_baska": "Басқа"
        }
        category = categories.get(call.data, "Басқа")
        msg = bot.send_message(call.message.chat.id, f"💸 {category} суммасын жаз (сум):")
        bot.register_next_step_handler(msg, save_other_expense, category, call.from_user.id)

    def save_other_e
