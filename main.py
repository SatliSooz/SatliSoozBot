import telebot
import os
import time
import threading
from flask import Flask, request

# ================== تنظیمات ==================
TOKEN = "8803927090:AAH4f6nm3Is4Po2hKgKFFN3gEDWLnqOaiE0"
CHANNEL_ID = -1003997971554
ADMIN_ID = 5044745081
BOT_USERNAME = "SatliSoozBot"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

files_db = {}

# ====================== برودکست ======================
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ فقط ادمین اجازه دارد!")
    bot.reply_to(message, "پیام بعدی را بفرست...")

# ====================== چک عضویت ======================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ====================== دریافت محتوا از ادمین ======================
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice'])
def handle_content(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ فقط ادمین می‌تواند محتوا بفرستد.")
    
    unique_id = str(int(time.time())) + str(message.message_id)
    
    if message.content_type == 'text':
        files_db[unique_id] = {"type": "text", "text": message.text}
    else:
        file_id = None
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
        elif message.content_type == 'video':
            file_id = message.video.file_id
        elif message.content_type == 'document':
            file_id = message.document.file_id
        elif message.content_type == 'audio':
            file_id = message.audio.file_id
        elif message.content_type == 'voice':
            file_id = message.voice.file_id
        
        files_db[unique_id] = {
            "type": message.content_type,
            "file_id": file_id,
            "caption": message.caption
        }
    
    link = f"https://t.me/{BOT_USERNAME}?start={unique_id}"
    bot.reply_to(message, f"✅ لینک آماده شد:\n\n{link}\n\nفایل بعد از ۱۰ ثانیه حذف می‌شود.")

# ====================== Start Handler ======================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    if not args:
        return bot.send_message(user_id, "👋 سلام! به ربات سطلی سوز خوش آمدید.")
    
    if not is_subscribed(user_id):
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton("سطلی سوز 🔥", url="https://t.me/+4UNzVMqnR0s2ODc0"),
            telebot.types.InlineKeyboardButton("بررسی عضویت ✅", callback_data=f"check_{args}")
        )
        bot.send_message(
            user_id,
            "🔴 لطفا برای استفاده از ربات و دریافت فایل:\n1️⃣ در کانال عضو شوید\n2️⃣ روی بررسی عضویت بزنید",
            reply_markup=markup
        )
        return
    
    send_content(user_id, args)

def send_content(user_id, unique_id):
    if unique_id not in files_db:
        return bot.send_message(user_id, "❌ فایل یافت نشد.")
    
    data = files_db[unique_id]
    
    try:
        if data["type"] == "text":
            bot.send_message(user_id, data["text"])
        else:
            caption = data.get("caption")
            if data["type"] == 'photo':
                bot.send_photo(user_id, data["file_id"], caption=caption)
            elif data["type"] == 'video':
                bot.send_video(user_id, data["file_id"], caption=caption)
            elif data["type"] == 'document':
                bot.send_document(user_id, data["file_id"], caption=caption)
            elif data["type"] == 'audio':
                bot.send_audio(user_id, data["file_id"], caption=caption)
            elif data["type"] == 'voice':
                bot.send_voice(user_id, data["file_id"], caption=caption)
        
        # حذف خودکار
        def auto_delete():
            time.sleep(10)
            if unique_id in files_db:
                del files_db[unique_id]
        threading.Thread(target=auto_delete, daemon=True).start()
        
    except:
        bot.send_message(user_id, "⚠️ خطا در ارسال.")

# ====================== Callback ======================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data.startswith("check_"):
        unique_id = call.data.split("_")[1]
        if is_subscribed(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ عضویت تأیید شد")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_content(call.from_user.id, unique_id)
        else:
            bot.answer_callback_query(call.id, "❌ هنوز عضو نشده‌اید!", show_alert=True)

# ====================== Webhook ======================
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK', 200

@app.route("/")
def index():
    bot.remove_webhook()
    bot.set_webhook(url="https://YOUR-APP-NAME.onrender.com/" + TOKEN)
    return "Webhook set!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)