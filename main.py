import telebot
from flask import Flask, request

API_TOKEN = "8041913948:AAFn4ujzHM1ovTNPnpOuguOV7mCnHGK0zGo"  # bu yerga bot tokenini yoz

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# --- Bot xabarlariga javob berish uchun handlerlar ---
import telebot
from telebot import types
import sqlite3, time, threading

API_TOKEN = "8041913948:AAFn4ujzHM1ovTNPnpOuguOV7mCnHGK0zGo"
TELEGRAM_CHANNEL = "@Karauzak_school"
INSTAGRAM_LINK = "https://instagram.com/karauzak_school"
ADMIN_ID = 8402317666  # admin id

bot = telebot.TeleBot(API_TOKEN)
DB_FILE = "bot_data.db"

# ----------------- DB -----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT,
        score INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

init_db()

def add_or_update_user(user_id, full_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users(user_id, full_name) VALUES(?, ?)", (user_id, full_name))
    c.execute("UPDATE users SET full_name=? WHERE user_id=?", (full_name, user_id))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT full_name, score FROM users WHERE user_id=?", (user_id,))
    r = c.fetchone()
    conn.close()
    return r

def add_score(user_id, points):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET score=score+? WHERE user_id=?", (points, user_id))
    conn.commit()
    conn.close()

def set_score(user_id, score):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET score=? WHERE user_id=?", (score, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, full_name, score FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

def get_leaderboard():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT full_name, score FROM users WHERE score>0 ORDER BY score DESC")
    rows = c.fetchall()
    conn.close()
    return rows

# ----------------- Menyu -----------------
def send_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_javob = types.KeyboardButton("📤 Juwap jiberiw")
    btn_stat = types.KeyboardButton("📊 Statistika")
    btn_profil = types.KeyboardButton("👤 Profilim")
    btn_contact_admin = types.KeyboardButton("📩 Adminga murojaat")
    markup.row(btn_javob, btn_profil)
    markup.row(btn_stat, btn_contact_admin)
    bot.send_message(chat_id, "Tiykarg'i menyu:", reply_markup=markup)

# ----------------- Start -----------------
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user = get_user(message.from_user.id)
    if user:
        send_main_menu(message.chat.id)
        return
    inline = types.InlineKeyboardMarkup()
    inline.add(types.InlineKeyboardButton("📩 Telegram kanal", url=f"https://t.me/{TELEGRAM_CHANNEL.strip('@')}"))
    inline.add(types.InlineKeyboardButton("📷 Instagram kanal", url=INSTAGRAM_LINK))
    inline.add(types.InlineKeyboardButton("✅ Tekseriw", callback_data="check_sub"))
    bot.send_message(message.chat.id,
                     "Telegram hám Instagram kanalǵa aǵza bolıń, soń ✅ Tekseriw túymesin basıń.",
                     reply_markup=inline)

@bot.callback_query_handler(func=lambda call: call.data=="check_sub")
def check_sub(call):
    try:
        status = bot.get_chat_member(TELEGRAM_CHANNEL, call.from_user.id)
        if status.status in ['member','administrator','creator']:
            bot.send_message(call.from_user.id,"Atı familyanıńızdı kiritiń:")
            bot.register_next_step_handler_by_chat_id(call.from_user.id, handle_name_input)
        else:
            bot.send_message(call.from_user.id,"❌ Siz kanalg'a ag'za bolmag'ansiz!")
    except:
        bot.send_message(call.from_user.id,"❌ Siz kanalg'a ag'za bolmag'ansiz!")

def handle_name_input(message):
    if not message.text:
        bot.send_message(message.chat.id,"Iltimas, atıńız hám familiyańızdı jazıń:")
        bot.register_next_step_handler_by_chat_id(message.chat.id, handle_name_input)
        return
    add_or_update_user(message.from_user.id, message.text.strip())
    bot.send_message(message.chat.id,f"✅ Raxmet, {message.text.strip()}!")
    send_main_menu(message.chat.id)

# ----------------- User menyu -----------------
@bot.message_handler(func=lambda m: m.text=="👤 Profilim")
def profil_cmd(message):
    user = get_user(message.from_user.id)
    if not user: return
    bot.send_message(message.chat.id,f"👤 {user[0]}\n🆔 {message.from_user.id}\n⭐ Ball: {user[1]}")

@bot.message_handler(func=lambda m: m.text=="📊 Statistika")
def stat_cmd(message):
    lb = get_leaderboard()
    if not lb:
        bot.send_message(message.chat.id,"Házirshe ballı paydalanıwshılar joq")
        return
    page_size=15
    pages=[lb[i:i+page_size] for i in range(0,len(lb),page_size)]
    send_leaderboard_page(message.chat.id,pages,0)

def send_leaderboard_page(chat_id,pages,page_index):
    page=pages[page_index]
    text=f"🏆 Reytin' bo'limi {page_index+1}/{len(pages)}:\n\n"
    medals=["🥇","🥈","🥉"]
    start_num=page_index*15+1
    for i,(name,score) in enumerate(page,start_num):
        medal=medals[i-start_num] if i-start_num<3 else "🔹"
        text+=f"{medal} {i}. {name} — {score}⭐\n"
    markup=None
    if len(pages)>1:
        markup=types.InlineKeyboardMarkup()
        if page_index>0:
            markup.add(types.InlineKeyboardButton("⬅ Aldin'g'i",callback_data=f"lb_{page_index-1}"))
        if page_index<len(pages)-1:
            markup.add(types.InlineKeyboardButton("Keyingi ➡",callback_data=f"lb_{page_index+1}"))
    bot.send_message(chat_id,text,reply_markup=markup)

@bot.callback_query_handler(func=lambda c:c.data and c.data.startswith("lb_"))
def lb_pages(c):
    idx=int(c.data.split("_")[1])
    lb=get_leaderboard()
    page_size=15
    pages=[lb[i:i+page_size] for i in range(0,len(lb),page_size)]
    bot.delete_message(c.message.chat.id,c.message.message_id)
    send_leaderboard_page(c.message.chat.id,pages,idx)
    bot.answer_callback_query(c.id)

# ----------------- Javob yuborish (xatolikdan tozalangan versiya) -----------------
user_states = {}

@bot.message_handler(func=lambda m: m.text == "📤 Juwap jiberiw")
def javob_cmd(message):
    user_states[message.chat.id] = "awaiting_answer"
    bot.send_message(message.chat.id, "📝 Juwabıńızdı jiberiń:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == "awaiting_answer")
def receive_answer(message):
    # holatni tozalaymiz
    user_states.pop(message.chat.id, None)

    user = get_user(message.from_user.id)
    if not user:
        return

    answer = message.text or "<matn yo‘q>"
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ Duris", callback_data=f"check_{message.from_user.id}_1"),
        types.InlineKeyboardButton("❌ Naduris", callback_data=f"check_{message.from_user.id}_0")
    )

    bot.send_message(
        ADMIN_ID,
        f"📩 <b>Yangi javob</b>\n👤 {user[0]}\n🆔 <code>{message.from_user.id}</code>\n✏️ <b>{answer}</b>",
        reply_markup=markup,
        parse_mode="HTML"
    )
    bot.send_message(message.chat.id, "✅ Juwap qabıl qilindi! Admin tekseredi.")


@bot.callback_query_handler(func=lambda c:c.data and c.data.startswith("check_"))
def check_answer(c):
    # faqat admin tekshirishi mumkin
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "Faqat admin!")
        return

    parts = c.data.split("_")
    try:
        uid = int(parts[1])
        point = int(parts[2])
    except:
        bot.answer_callback_query(c.id, "Xato callback ma'lumot!")
        return

    # foydalanuvchiga xabar va ball qo'shish
    if point == 1:
        add_score(uid, 1)
        user_msg = "🎉 Juwap duris! 1 ball qosıldı."
        result_text = "✅ Duris — 1 ball qosıldı."
    else:
        user_msg = "❌ Juwap naduris. Ball qosılmadı."
        result_text = "❌ Naduris — ball qosılmadı."

    try:
        bot.send_message(uid, user_msg)
    except:
        # foydalanuvchiga yuborib bo'lmasa ham davom etamiz
        pass

    # admin panelidagi xabarni yangilab, kim tekshirganini va natijani ko'rsatamiz
    checker_name = c.from_user.first_name or str(c.from_user.id)
    new_text = f"{c.message.text}\n\nTekshirildi: {result_text}\nTekshirlagan: {checker_name} (id: {c.from_user.id})"

    try:
        bot.edit_message_text(chat_id=c.message.chat.id,
                              message_id=c.message.message_id,
                              text=new_text)
    except Exception as e:
        # xatolik bo'lsa o'tkazib yuborish
        pass

    bot.answer_callback_query(c.id, "Tekserildi")

@bot.message_handler(func=lambda m:m.text=="📩 Adminga murojaat")
def contact_admin(message):
    bot.send_message(message.chat.id,"Admin ushın xabarıńızdı jazıń:")
    bot.register_next_step_handler(message,send_to_admin)

def send_to_admin(message):
    user=get_user(message.from_user.id)
    bot.send_message(ADMIN_ID,f"📨 Yangi murojaat\n👤 {user[0]}\n🆔 {message.from_user.id}\n\n{message.text}")
    bot.send_message(message.chat.id,"✅ Xabarińiz adminge jiberildi.")

# ----------------- Admin buyruqlari -----------------
# 🔐 Admin-only dekoratori
def admin_only(func):
    def wrapper(message):
        if message.from_user.id != ADMIN_ID:
            bot.send_message(message.chat.id, "⛔ Bu buyruq faqat admin uchun!")
            return
        return func(message)
    return wrapper


# ♻️ Barcha foydalanuvchilar ballini 0 ga tushirish
@bot.message_handler(commands=['resetall'])
@admin_only
def resetall_cmd(message):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET score = 0")
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "♻️ Barcha foydalanuvchilarning ballari 0 ga tushirildi!")


# ➕ Ball qo‘shish
@bot.message_handler(commands=['addscore'])
@admin_only
def addscore_cmd(message):
    try:
        _, uid, pts = message.text.split()
        add_score(int(uid), int(pts))
        bot.send_message(message.chat.id, f"✅ Foydalanuvchi {uid} ga {pts} ball qo‘shildi.")
    except:
        bot.send_message(message.chat.id, "⚠️ Foydalanish: /addscore ID BALL")


# 🧮 Ballni o‘rnatish
@bot.message_handler(commands=['setscore'])
@admin_only
def setscore_cmd(message):
    try:
        _, uid, score = message.text.split()
        set_score(int(uid), int(score))
        bot.send_message(message.chat.id, f"✅ Foydalanuvchi {uid} balli {score} ga o‘rnatildi.")
    except:
        bot.send_message(message.chat.id, "⚠️ Foydalanish: /setscore ID BALL")


# 🗑 Foydalanuvchi ma’lumotlarini o‘chirish
@bot.message_handler(commands=['clearinfo'])
@admin_only
def clearinfo_cmd(message):
    try:
        _, uid = message.text.split()
        delete_user(int(uid))
        bot.send_message(message.chat.id, f"🧹 Foydalanuvchi {uid} o‘chirildi.")
    except:
        bot.send_message(message.chat.id, "⚠️ Foydalanish: /clearinfo ID")


# ✏️ Ismni o‘zgartirish
@bot.message_handler(commands=['setname'])
@admin_only
def setname_cmd(message):
    try:
        _, uid, *name = message.text.split()
        add_or_update_user(int(uid), " ".join(name))
        bot.send_message(message.chat.id, f"✅ Foydalanuvchi {uid} ismi yangilandi.")
    except:
        bot.send_message(message.chat.id, "⚠️ Foydalanish: /setname ID Ism Familiya")


# 👥 Barcha foydalanuvchilarni ko‘rish
# 👥 Barcha foydalanuvchilarni sahifalab ko‘rsatish (faqat admin)
@bot.message_handler(commands=['allusers'])
@admin_only
def allusers_cmd(message):
    users = get_all_users()
    if not users:
        bot.send_message(message.chat.id, "😕 Hozircha foydalanuvchilar bazada yo‘q.")
        return

    # har 10 foydalanuvchidan bitta sahifa hosil qilamiz
    page_size = 10
    pages = [users[i:i + page_size] for i in range(0, len(users), page_size)]

    # birinchi sahifani yuboramiz
    send_users_page(message.chat.id, pages, 0)


def send_users_page(chat_id, pages, page_index):
    """Admin uchun sahifalangan foydalanuvchilar ro‘yxatini yuborish"""
    page = pages[page_index]
    text = f"👥 <b>Barcha foydalanuvchilar</b> — sahifa {page_index + 1}/{len(pages)}\n"
    text += "━━━━━━━━━━━━━━━━━━━\n"

    for i, u in enumerate(page, start=page_index * 10 + 1):
        text += (
            f"🔹 <b>{i}. {u[1]}</b>\n"
            f"🆔 <code>{u[0]}</code>\n"
            f"⭐ Ball: <b>{u[2]}</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
        )

    text += f"📊 <b>Jami foydalanuvchilar:</b> {sum(len(p) for p in pages)} ta"

    # sahifa o‘zgartirish tugmalari
    markup = types.InlineKeyboardMarkup()
    row = []
    if page_index > 0:
        row.append(types.InlineKeyboardButton("⬅ Oldingi", callback_data=f"users_{page_index - 1}"))
    if page_index < len(pages) - 1:
        row.append(types.InlineKeyboardButton("Keyingi ➡", callback_data=f"users_{page_index + 1}"))
    if row:
        markup.row(*row)

    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")


# Sahifalar orasida yurish
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("users_"))
def users_pagination(c):
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "⛔ Faqat admin uchun!")
        return

    try:
        idx = int(c.data.split("_")[1])
    except:
        bot.answer_callback_query(c.id, "Xatolik!")
        return

    users = get_all_users()
    page_size = 10
    pages = [users[i:i + page_size] for i in range(0, len(users), page_size)]

    # Eski xabarni o‘chiramiz va yangi sahifani yuboramiz
    try:
        bot.delete_message(c.message.chat.id, c.message.message_id)
    except:
        pass

    send_users_page(c.message.chat.id, pages, idx)
    bot.answer_callback_query(c.id)




# 📢 Hamma foydalanuvchilarga xabar yuborish
@bot.message_handler(commands=['broadcast'])
@admin_only
def broadcast_cmd(message):
    try:
        _, msg = message.text.split(" ", 1)
    except:
        bot.send_message(message.chat.id, "⚠️ Foydalanish: /broadcast xabar")
        return
    for (uid, _, _) in get_all_users():
        try:
            bot.send_message(uid, msg)
        except:
            pass
    bot.send_message(message.chat.id, "✅ Xabar barcha foydalanuvchilarga yuborildi!")


# ⏰ Taymer
@bot.message_handler(commands=['time'])
@admin_only
def time_cmd(message):
    try:
        _, sec = message.text.split()
        sec = int(sec)
    except:
        bot.send_message(message.chat.id, "⚠️ Foydalanish: /time sekund")
        return
    threading.Thread(target=timer_thread, args=(sec,)).start()
    bot.send_message(message.chat.id, f"⏳ {sec} sekundlik taymer ishga tushdi.")


def timer_thread(sec):
    time.sleep(sec)
    bot.send_message(ADMIN_ID, f"⏰ {sec} sekund tugadi!")

# ---- Faqat bitta foydalanuvchiga xabar yuborish (Admin xabari sifatida) ----
@bot.message_handler(commands=['senduser'])
def send_user_message_step1(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "📩 Kimga xabar yuboramiz? Foydalanuvchi ID sini yuboring:")
        bot.register_next_step_handler(message, send_user_message_step2)
    else:
        bot.send_message(message.chat.id, "Bu buyruq faqat admin uchun.")

def send_user_message_step2(message):
    try:
        user_id = int(message.text)
        bot.send_message(message.chat.id, "✍️ Endi yubormoqchi bo‘lgan xabaringizni yozing:")
        bot.register_next_step_handler(message, send_user_message_step3, user_id)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Noto‘g‘ri ID. Faqat raqam kiritishingiz kerak.")
        return

def send_user_message_step3(message, user_id):
    text = message.text
    admin_text = f"📢 *Adminnen xabar:*\n\n{text}\n\n— 🧑‍💼 *Administrator*"
    try:
        bot.send_message(user_id, admin_text, parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ Xabar foydalanuvchiga ({user_id}) yuborildi.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xabar yuborilmadi. Foydalanuvchi botni boshlamagan bo‘lishi mumkin.\n\n{e}")




# ----------------- Run -----------------
if __name__=="__main__":
    init_db()
    print("Bot ishga tushdi...")
    bot.infinity_polling(skip_pending=True)


# --- Flask serverni ishga tushirish ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
