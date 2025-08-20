"""
First Comment Userbot (с заходом в связанную группу)

📌 Возможности:
- При старте просит указать канал (username без @).
- При /on находит связанную группу комментариев, вступает в неё и слушает новые посты.
- Как только появляется новый пост — мгновенно оставляет комментарий.
- Управление командами из Saved Messages.

🧰 Команды:
  /set_text <текст> — задать текст для комментариев
  /text             — показать текущий текст
  /on               — включить юзербот
  /off              — выключить
  /status           — показать состояние
  /ch <username>    — сменить канал
  /help             — подсказка
"""

import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest
import time

# 🔴 Вставь свои данные
API_ID = 25165568
API_HASH = "0f13997a616a03ccd368f3c0f794208c"
SESSION_NAME = "first_comment_userbot"

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

channel_username = None
linked_chat_id = None
current_text = ""
enabled = False


# --- Вспомогательное ---
async def is_owner(event):
    me = await client.get_me()
    return event.sender_id == me.id


# --- Команды ---
@client.on(events.NewMessage(pattern="/set_text (.+)"))
async def set_text(event):
    if not await is_owner(event):
        return
    global current_text
    current_text = event.pattern_match.group(1)
    await event.respond(f"✅ Текст установлен: {current_text}")


@client.on(events.NewMessage(pattern="/text"))
async def show_text(event):
    if not await is_owner(event):
        return
    await event.respond(f"📝 Текущий текст: {current_text or '❌ не задан'}")


@client.on(events.NewMessage(pattern="/on"))
async def turn_on(event):
    if not await is_owner(event):
        return
    global enabled, linked_chat_id
    enabled = True
    await event.respond("✅ Бот включён")

    if channel_username:
        try:
            full = await client(GetFullChannelRequest(channel_username))
            if full.full_chat.linked_chat_id:
                linked_chat_id = full.full_chat.linked_chat_id
                try:
                    await client(JoinChannelRequest(linked_chat_id))
                    print("✅ Вошёл в связанную группу комментариев")
                except Exception as e:
                    print("⚠️ Уже в группе или ошибка:", e)
            else:
                print("❌ У канала нет связанной группы комментариев")
        except Exception as e:
            print("Ошибка при получении инфо о канале:", e)


@client.on(events.NewMessage(pattern="/off"))
async def turn_off(event):
    if not await is_owner(event):
        return
    global enabled
    enabled = False
    await event.respond("⛔ Бот выключён")


@client.on(events.NewMessage(pattern="/status"))
async def status(event):
    if not await is_owner(event):
        return
    msg = f"📡 Канал: {channel_username or '❌ не выбран'}\n"
    msg += f"💬 Текст: {current_text or '❌ не задан'}\n"
    msg += f"⚙️ Статус: {'✅ ВКЛ' if enabled else '⛔ ВЫКЛ'}"
    await event.respond(msg)


@client.on(events.NewMessage(pattern="/ch (.+)"))
async def set_channel(event):
    if not await is_owner(event):
        return
    global channel_username, linked_chat_id
    channel_username = event.pattern_match.group(1).lstrip("@")
    linked_chat_id = None
    await event.respond(f"📡 Канал изменён на: {channel_username}")


@client.on(events.NewMessage(pattern="/help"))
async def help_cmd(event):
    if not await is_owner(event):
        return
    await event.respond(
        "🧰 Команды:\n"
        "/set_text <текст> — задать текст\n"
        "/text — показать текст\n"
        "/on — включить\n"
        "/off — выключить\n"
        "/status — статус\n"
        "/ch <username> — сменить канал\n"
        "/help — помощь"
    )


# --- Логика комментария ---
@client.on(events.NewMessage)
async def first_comment(event):
    global enabled, channel_username, current_text, linked_chat_id
    if not enabled or not current_text or not channel_username:
        return

    # Новый пост от канала
    if event.is_channel and event.chat and event.chat.username == channel_username and not event.fwd_from:
        try:
            start_time = time.perf_counter()
            if linked_chat_id:
                await client.send_message(entity=linked_chat_id, message=current_text, reply_to=event.id)
            else:
                await client.send_message(entity=event.chat, message=current_text, comment_to=event.id)

            elapsed = (time.perf_counter() - start_time) * 1000
            print(f"⚡ Комментарий добавлен за {elapsed:.2f} мс: {current_text}")
        except Exception as e:
            print("Ошибка при попытке комментировать:", e)


# --- Старт ---
async def main():
    global channel_username
    await client.start()
    channel_username = input("Введите username канала (без @): ").strip()
    print("Запущено... /help для команд")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
