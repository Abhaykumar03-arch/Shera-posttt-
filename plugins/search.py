from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import asyncio
from time import time
from info import *
from utils import *
from plugins.generate import database

# Utility to send message in chunks
async def send_message_in_chunks(client, chat_id, text, reply_markup=None):
    max_length = 4096  # Maximum length of a message
    for i in range(0, len(text), max_length):
        msg = await client.send_message(chat_id=chat_id, text=text[i:i+max_length], disable_web_page_preview=True, reply_markup=reply_markup)
        asyncio.create_task(delete_after_delay(msg, 1800))

# Utility to delete messages after a delay
async def delete_after_delay(message: Message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

# Handle searching for messages and adding forward feature
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
        return

    if message.text.startswith("/"):
        return

    query = message.text
    head = f"<u>⭕ Here are the results {message.from_user.mention} 👇\n\n💢 Powered By </u> <b><I>@RMCBACKUP ❗</I></b>\n\n"
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
            # Send results along with forward button
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔁 Forward this to Admin", callback_data="forward_to_admin")]
            ])
            await send_message_in_chunks(bot, message.chat.id, head + results + "\n\n", reply_markup=keyboard)

    except Exception as e:
        print(f"Error in search function: {e}")
        pass

# Handle callback when "forward_to_admin" is clicked
@Client.on_callback_query(filters.regex(r"^forward_to_admin"))
async def forward_to_admin(bot, update):
    clicked = update.from_user.id
    message_to_forward = update.message.reply_to_message

    if message_to_forward is None:
        return await update.answer("Please reply to a message to forward it.", show_alert=True)

    admin = (await get_group(update.message.chat.id))["user_id"]
    text_to_forward = message_to_forward.text or message_to_forward.caption

    # Forward the message content to the admin
    try:
        await bot.forward_messages(chat_id=admin, from_chat_id=update.message.chat.id, message_ids=message_to_forward.message_id)
        await update.answer("✅ Forwarded to Admin.", show_alert=True)
    except Exception as e:
        await update.answer(f"❌ Error forwarding the message: {str(e)}", show_alert=True)

# Handle recheck callback for movies
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
            # If no results found after recheck, return a custom message and offer a request to admin
            return await update.message.edit(
                "🔺 Sorry, I think we don't have that post regarding your request. 🔻",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Request To Admin 🎯", callback_data=f"request_{id}")]])
            )

        await send_message_in_chunks(bot, update.message.chat.id, head + results)

    except Exception as e:
        await update.message.edit(f"❌ Error: `{e}`")

# Handle requests to admin (when recheck fails)
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

    await bot.send_message(chat_id=admin, text=text, disable_web_page_preview=True)
    await update.answer("✅ Request Sent To Admin", show_alert=True)
    await update.message.delete(60)
