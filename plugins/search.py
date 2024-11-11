# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import asyncio
from info import *
from utils import *
from time import time
from plugins.generate import database
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

async def send_message_in_chunks(client, chat_id, text):
    max_length = 4096  # Maximum length of a message
    for i in range(0, len(text), max_length):
        msg = await client.send_message(chat_id=chat_id, text=text[i:i + max_length])
        asyncio.create_task(delete_after_delay(msg, 1800))

async def delete_after_delay(message: Message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

@Client.on_message(filters.text & filters.group & filters.incoming & ~filters.command(["verify", "connect", "id"]))
async def search(bot, message):
    vj = database.find_one({"chat_id": ADMIN})
    if vj is None:
        return await message.reply("**Contact Admin Then Say To Login In Bot.**")

    User = Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID)
    await User.connect()

    f_sub = await force_sub(bot, message)
    if f_sub is False:
        return

    channels = (await get_group(message.chat.id))["channels"]
    if not channels:
import asyncio
from info import *
from utils import *
from time import time 
from plugins.generate import database
from pyrogram import Client, filters 
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message 

async def send_message_in_chunks(client, chat_id, text):
    max_length = 4096  # Maximum length of a message
    for i in range(0, len(text), max_length):
        msg = await client.send_message(chat_id=chat_id, text=text[i:i+max_length], disable_web_page_preview=True)
        asyncio.create_task(delete_after_delay(msg, 1800))

async def delete_after_delay(message: Message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

@Client.on_message(filters.text & filters.group & filters.incoming & ~filters.command(["verify", "connect", "id"]))
async def search(bot, message):
    vj = database.find_one({"chat_id": ADMIN})
    if vj is None:
        return await message.reply("**Contact Admin Then Say To Login In Bot.**")  # Indent this line

    User = Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID)
    await User.connect()

    f_sub = await force_sub(bot, message)
    if f_sub is False:
        return  # Indent this line correctly

    channels = (await get_group(message.chat.id))["channels"]
    if not channels:
        return  # Indent this line correctly

    if message.text.startswith("/"):
        return  # Indent this line correctly

    query = message.text
    head = f"<u>⭕ Here is the results {message.from_user.mention} 👇\n\n💢 Powered By </u> <b><I>@RMCBACKUP ❗</I></b>\n\n"
    results = ""

    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                results += f"<b><I>♻️ {name}\n🔗 {msg.link}</I></b>\n\n"

        if not results:
            # No results found in the channels, search IMDB
            movies = await search_imdb(query)
            buttons = []
            for movie in movies:
                buttons.append([InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}")])
            msg = await message.reply_photo(
                photo="https://graph.org/file/c361a803c7b70fc50d435.jpg",
                caption="<b><I>🔻 I Couldn't find anything related to Your Query😕.\n🔺 Did you mean any of these?</I></b>",
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True  # Disable the web preview for the image link
            )
        else:
            await send_message_in_chunks(bot, message.chat.id, head + results)
    except Exception as e:
        print(f"Error in search function: {e}")
        pass

@Client.on_callback_query(filters.regex(r"^recheck"))
async def recheck(bot, update):
    vj = database.find_one({"chat_id": ADMIN})
    User = Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID)
    if vj is None:
        return await update.message.edit("**Contact Admin Then Say To Login In Bot.**")

    await User.connect()
    clicked = update.from_user.id

    try:
        typed = update.message.reply_to_message.from_user.id
    except AttributeError:
        return await update.message.delete()

    if clicked != typed:
        return await update.answer("That's not for you! 👀", show_alert=True)

    m = await update.message.edit("**Searching..💥**")
    id = update.data.split("_")[-1]
    query = await search_imdb(id)
    channels = (await get_group(update.message.chat.id))["channels"]
    head = "<u>⭕ I Have Searched Movie With Wrong Spelling But Take care next time 👇\n\n💢 Powered By </u> <b><I>@RMCBACKUP ❗</I></b>\n\n"
    results = ""

    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                results += f"<b><I>♻️🍿 {name}</I></b>\n\n🔗 {msg.link}</I></b>\n\n"

        if not results:
            return await update.message.edit(
                "🔺 Still no results found! Please Request To Group Admin 🔻",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Request To Admin 🎯", callback_data=f"request_{id}")]]),
                disable_web_page_preview=True  # Disable web preview for the link button
            )

        await send_message_in_chunks(bot, update.message.chat.id, head + results)

    except Exception as e:
        await update.message.edit(f"❌ Error: `{e}`")

@Client.on_callback_query(filters.regex(r"^request"))
async def request(bot, update):
    clicked = update.from_user.id

    try:
        typed = update.message.reply_to_message.from_user.id
    except AttributeError:
        return await update.message.delete()

    if clicked != typed:
        return await update.answer("That's not for you! 👀", show_alert=True)

    admin = (await get_group(update.message.chat.id))["user_id"]
    id = update.data.split("_")[1]
    name = await search_imdb(id)
    url = f"https://www.imdb.com/title/tt{id}"
    text = f"#RequestFromYourGroup\n\nName: {name}\nIMDb: {url}"

    # Add quote feature: quote the message that is being replied to
    if update.message.reply_to_message:
        quoted_message = update.message.reply_to_message
        quote_text = f"\n\n<quote>{quoted_message.text or quoted_message.caption}</quote>"
        text += quote_text

    await bot.send_message(chat_id=admin, text=text, disable_web_page_preview=True)  # Disable web page preview for the admin message
    await update.answer("✅ Request Sent To Admin", show_alert=True)
    await update.message.delete(60)
