import json
import random
from telethon import TelegramClient, events

# ==== ДАННЫЕ АККАУНТА ====
API_ID = 25165568
API_HASH = "0f13997a616a03ccd368f3c0f794208c"
SESSION_NAME = "first_comment"

# ==== ФАЙЛ С НАСТРОЙКАМИ ====
CONFIG_FILE = "config.json"

# ==== ЗАГРУЗКА / СОХРАНЕНИЕ ====
def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "ENABLED": True,
            "KEYWORDS": [],
            "COMMENTS": [],
            "CHANNELS": []
        }

def save_config():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

config = load_config()

# ==== КЛИЕНТ ====
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# ==== АВТООТВЕТ НА НОВЫЕ ПОСТЫ КАНАЛОВ ====
@client.on(events.NewMessage)
async def handler(event):
    if not config["ENABLED"]:
        return

    chat = await event.get_chat()
    if not hasattr(chat, "username"):
        return

    username = (chat.username or "").lower()
    if username not in [c.lower() for c in config["CHANNELS"]]:
        return

    # Проверка на ключевые слова
    text = event.raw_text.lower()
    if not any(w in text for w in config["KEYWORDS"]):
        return

    # Проверка что это пост канала (без reply на людей)
    if not event.is_channel:
        return

    # Находим связанную группу комментариев
    try:
        linked_chat = (await client(GetFullChannelRequest(chat.id))).full_chat.linked_chat_id
        if not linked_chat:
            return
    except:
        return

    if not config["COMMENTS"]:
        return

    reply_text = random.choice(config["COMMENTS"])
    try:
        await client.send_message(linked_chat, reply_text, reply_to=event.id)
        print(f"💬 Ответил в {username}: {reply_text}")
    except Exception as e:
        print(f"❌ Ошибка при ответе: {e}")

# ==== КОМАНДЫ В ИЗБРАННОМ ====
@client.on(events.NewMessage(outgoing=True))
async def commands(event):
    global config
    me = await client.get_me()
    if event.sender_id != me.id:  
        return

    text = event.raw_text.strip()

    if text == "/help":
        await event.reply(
            "📖 Доступные команды:\n\n"
            "/on – включить автоответчик\n"
            "/off – выключить автоответчик\n"
            "/addword СЛОВО – добавить ключевое слово\n"
            "/delword СЛОВО – удалить ключевое слово\n"
            "/addcomment ТЕКСТ – добавить комментарий\n"
            "/delcomment ТЕКСТ – удалить комментарий\n"
            "/addchannel @канал – добавить канал\n"
            "/delchannel @канал – удалить канал\n"
            "/list – показать настройки\n"
            "/help – список команд"
        )

    elif text == "/on":
        config["ENABLED"] = True
        save_config()
        await event.reply("✅ Бот включен")

    elif text == "/off":
        config["ENABLED"] = False
        save_config()
        await event.reply("⛔ Бот выключен")

    elif text.startswith("/addword "):
        word = text.split(" ", 1)[1].lower()
        if word not in config["KEYWORDS"]:
            config["KEYWORDS"].append(word)
            save_config()
            await event.reply(f"✅ Слово добавлено: {word}")

    elif text.startswith("/delword "):
        word = text.split(" ", 1)[1].lower()
        if word in config["KEYWORDS"]:
            config["KEYWORDS"].remove(word)
            save_config()
            await event.reply(f"🗑 Слово удалено: {word}")

    elif text.startswith("/addcomment "):
        msg = text.split(" ", 1)[1]
        if msg not in config["COMMENTS"]:
            config["COMMENTS"].append(msg)
            save_config()
            await event.reply(f"✅ Комментарий добавлен: {msg}")

    elif text.startswith("/delcomment "):
        msg = text.split(" ", 1)[1]
        if msg in config["COMMENTS"]:
            config["COMMENTS"].remove(msg)
            save_config()
            await event.reply(f"🗑 Комментарий удалён: {msg}")

    elif text.startswith("/addchannel "):
        ch = text.split(" ", 1)[1].replace("@", "")
        if ch not in config["CHANNELS"]:
            config["CHANNELS"].append(ch)
            save_config()
            await event.reply(f"✅ Канал добавлен: {ch}")

    elif text.startswith("/delchannel "):
        ch = text.split(" ", 1)[1].replace("@", "")
        if ch in config["CHANNELS"]:
            config["CHANNELS"].remove(ch)
            save_config()
            await event.reply(f"🗑 Канал удалён: {ch}")

    elif text == "/list":
        await event.reply(
            f"📋 Настройки:\n"
            f"▶ Статус: {'ВКЛ' if config['ENABLED'] else 'ВЫКЛ'}\n"
            f"🔑 Слова: {', '.join(config['KEYWORDS']) or '—'}\n"
            f"💬 Комментарии: {', '.join(config['COMMENTS']) or '—'}\n"
            f"📢 Каналы: {', '.join(config['CHANNELS']) or '—'}"
        )

# ==== СТАРТ ====
print("🚀 Бот запущен. Команды пиши в Избранном (/help)")
client.start()
client.run_until_disconnected()
