import telebot
import os
import time
import threading
from flask import Flask, request

# ================== تنظیمات ==================
TOKEN = os.getenv("TOKEN", "8803927090:AAH4f6nm3Is4Po2hKgKFFN3gEDWLnqOaiE0")
CHANNEL_ID = -1003997971554
ADMIN_ID = 5044745081
BOT_USERNAME = "SatliSoozBot"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

files_db = {}

# ====================== توابع کمکی ======================
def is_admin(user_id):
    if user_id == ADMIN_ID:
        return True
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ====================== Start Handler ======================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    args = None
    if len(message.text.split()) > 1:
        args = message.text.split()[1].strip()
    
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
            "🔴 لطفا برای استفاده از ربات و دریافت فایل:\n"
            "1️⃣ در کانال های ما عضو شوید\n"
            "2️⃣ سپس روی دکمه ی بررسی عضویت کلیک کنید\n\n"
            "@SatliSooz",
            reply_markup=markup
        )
        return
    
    send_content(user_id, args)

def send_content(user_id, unique_id):
    if unique_id not in files_db:
        return  # هیچ پیامی نمایش داده نشود
    
    data = files_db[unique_id]
    
    try:
        sent_msg = None
        
        if data["type"] == "text":
            sent_msg = bot.send_message(user_id, data["text"])
        elif data["type"] == 'photo':
            sent_msg = bot.send_photo(user_id, data["file_id"], caption=data.get("caption"))
        elif data["type"] == 'video':
            sent_msg = bot.send_video(user_id, data["file_id"], caption=data.get("caption"))
        elif data["type"] == 'document':
            sent_msg = bot.send_document(user_id, data["file_id"], caption=data.get("caption"))
        elif data["type"] == 'audio':
            sent_msg = bot.send_audio(user_id, data["file_id"], caption=data.get("caption"))
        elif data["type"] == 'voice':
            sent_msg = bot.send_voice(user_id, data["file_id"], caption=data.get("caption"))
        elif data["type"] == 'animation':
            sent_msg = bot.send_animation(user_id, data["file_id"], caption=data.get("caption"))
        
        # پیام ذخیره‌سازی
        bot.send_message(
            user_id, 
            "⏳ ۱۰ ثانیه وقت دارید فایل را در Save Message خود ذخیره کنید."
        )
        
        # حذف پیام فایل بعد از ۱۰ ثانیه
        if sent_msg:
            def auto_delete_msg():
                time.sleep(10)
                try:
                    bot.delete_message(user_id, sent_msg.message_id)
                except:
                    pass
            threading.Thread(target=auto_delete_msg, daemon=True).start()
        
    except:
        pass  # هیچ پیامی در صورت خطا ارسال نشود

# ====================== دریافت محتوا توسط ادمین ======================
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'animation'])
def handle_content(message):
    if message.text and message.text.startswith('/'):
        return
    
    if not is_admin(message.from_user.id):
        return bot.reply_to(message, "⛔ فقط ادمین‌ها می‌توانند محتوا بفرستند.")
    
    unique_id = str(int(time.time())) + str(message.message_id)
    
    if message.content_type == 'text':
        files_db[unique_id] = {"type": "text", "text": message.text}
    else:
        file_id = None
        content_type = message.content_type
        
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
        elif message.content_type == 'animation':
            file_id = message.animation.file_id
            content_type = 'animation'
        
        files_db[unique_id] = {
            "type": content_type,
            "file_id": file_id,
            "caption": message.caption
        }
    
    link = f"https://t.me/{BOT_USERNAME}?start={unique_id}"
    bot.reply_to(message, f"✅ لینک آماده شد:\n\n{link}\n\nاین لینک دائمی است.")

# ====================== Callback ======================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data.startswith("check_"):
        unique_id = call.data.split("_", 1)[1]
        if is_subscribed(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ عضویت تأیید شد!")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_content(call.from_user.id, unique_id)
        else:
            bot.answer_callback_query(call.id, "❌ هنوز عضو کانال نشده‌اید!", show_alert=True)

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
    bot.set_webhook(url="https://satlisoozbot-production.up.railway.app/" + TOKEN)
    return "Webhook set!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)