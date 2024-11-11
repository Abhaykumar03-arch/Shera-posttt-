import asyncio
from info import *
from utils import *
from time import time 
from plugins.generate import database
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message


async def send_message_in_chunks(client, chat_id, text):
    """
    Send long messages in chunks, if the message length exceeds the Telegram limit.
    """
    max_length = 4096  # Maximum length of a message
    for i in range(0, len(text), max_length):
        msg = await client.send_message(
            chat_id=chat_id,
            text=text[i:i + max_length],
            disable_web_page_preview=True  # Disable web page preview
        )
        asyncio.create_task(delete_after_delay(msg, 1800))


async def delete_after_delay(message: Message, delay: int):
    """
    Delete a message after a specified delay.
    """
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        # Log the exception for troubleshooting
        print(f"Error deleting message: {e}")
        pass


@Client.on_message(filters.text & filters.group & filters.incoming & ~filters.command(["verify", "connect", "id"]))
async def search(bot, message: Message):
    """
    Handle search queries in the group chat and return results from a set of channels.
    """
    vj = database.find_one({"chat_id": ADMIN})
    if vj is None:
        return await message.reply("**Contact Admin Then Say To Login In Bot.**")
    
    # Initialize the user session with Telegram credentials
    User = Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID)
    await User.connect()
    
    # Check for mandatory subscription
    f_sub = await force_sub(bot, message)
    if not f_sub:
        return
    
    channels = (await get_group(message.chat.id))["channels"]
    if not channels:
        return
    
    # Skip processing for commands
    if message.text.startswith("/"):
        return
    
    query = message.text
    head = f"<u>⭕ Here are the results, {message.from_user.mention} 👇\n\n💢 Powered By </u> <b><I>@VJ_Botz ❗</I></b>\n\n"
    results = ""

    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                results += f"<b><I>♻️ {name}\n🔗 {msg.link}</I></b>\n\n"
        
        if not results:
            # If no results found, search on IMDb
            movies = await search_imdb(query)
            buttons = [
                [InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}")]
                for movie in movies
            ]
            msg = await message.reply_photo(
                photo="https://graph.org/file/c361a803c7b70fc50d435.jpg",
                caption="<b><I>🔻 I Couldn't find anything related to Your Query😕.\n🔺 Did you mean any of these?</I></b>",
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True  # Disable image preview
            )
        else:
            # Send the results with no web preview
            await send_message_in_chunks(bot, message.chat.id, head + results)
    except Exception as e:
        # Log the exception for troubleshooting
        print(f"Error during search: {e}")
        pass


@Client.on_callback_query(filters.regex(r"^recheck"))
async def recheck(bot, update):
    """
    Handle recheck callback when the user clicks a movie link to search again.
    """
    vj = database.find_one({"chat_id": ADMIN})
    if vj is None:
        return await update.message.edit("**Contact Admin Then Say To Login In Bot.**")
    
    User = Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID)
    await User.connect()

    clicked_user_id = update.from_user.id
    try:
        reply_user_id = update.message.reply_to_message.from_user.id
    except AttributeError:
        return await update.message.delete(2)
    
    # Check if the user clicked the recheck button for their own query
    if clicked_user_id != reply_user_id:
        return await update.answer("That's not for you! 👀", show_alert=True)

    m = await update.message.edit("**Searching..💥**")
    movie_id = update.data.split("_")[-1]
    query = await search_imdb(movie_id)
    
    channels = (await get_group(update.message.chat.id))["channels"]
    head = "<u>⭕ I Have Searched Movie With a Similar Name, but Take care next time 👇\n\n💢 Powered By </u> <b><I>@VJ_Botz ❗</I></b>\n\n"
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
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Request To Admin 🎯", callback_data=f"request_{movie_id}")]]),
                disable_web_page_preview=True  # Disable image preview
            )
        
        await send_message_in_chunks(bot, update.message.chat.id, head + results)
    except Exception as e:
        await update.message.edit(f"❌ Error: `{e}`")


@Client.on_callback_query(filters.regex(r"^request"))
async def request(bot, update):
    """
    Handle requests to the admin to search for a movie if no results were found.
    """
    clicked_user_id = update.from_user.id
    try:
        reply_user_id = update.message.reply_to_message.from_user.id
    except AttributeError:
        return await update.message.delete()

    # Ensure that the request is from the person who initiated the search
    if clicked_user_id != reply_user_id:
        return await update.answer("That's not for you! 👀", show_alert=True)

    admin_id = (await get_group(update.message.chat.id))["user_id"]
    movie_id = update.data.split("_")[1]
    movie_name = await search_imdb(movie_id)
    imdb_url = f"https://www.imdb.com/title/tt{movie_id}"

    # Send a request to the admin with the movie details
    text = f"#RequestFromYourGroup\n\nName: {movie_name}\nIMDb: {imdb_url}"
    await bot.send_message(chat_id=admin_id, text=text, disable_web_page_preview=True)
    
    await update.answer("✅ Request Sent To Admin", show_alert=True)
    await update.message.delete(60)
