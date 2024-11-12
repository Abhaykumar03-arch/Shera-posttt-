import asyncio
from info import *  # Make sure your database configuration and API credentials are correct
from utils import *  # Ensure these utility functions are implemented correctly
from time import time
from plugins.generate import database
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message


# Function to send message in chunks
async def send_message_in_chunks(client, chat_id, text, reply_to_message_id=None):
    max_length = 4096  # Maximum length of a message
    for i in range(0, len(text), max_length):
        msg = await client.send_message(
            chat_id=chat_id, 
            text=text[i:i + max_length], 
            reply_to_message_id=reply_to_message_id
        )
        # Schedule message deletion after delay (30 minutes in this case)
        asyncio.create_task(delete_after_delay(msg, 1800))


# Function to delete message after delay
async def delete_after_delay(message: Message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass


# Function that handles incoming messages in groups (search functionality)
@Client.on_message(filters.text & filters.group & filters.incoming & ~filters.command(["verify", "connect", "id"]))
async def search(bot, message):
    vj = database.find_one({"chat_id": ADMIN})  # Retrieve the session information for the bot
    if vj is None:
        return await message.reply("**Contact Admin Then Say To Login In Bot.**")
    
    User = Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID)
    await User.connect()

    # Ensure the user is subscribed to required channels (assuming 'force_sub' is defined elsewhere)
    f_sub = await force_sub(bot, message)
    if not f_sub:
        return

    # Get the list of channels where messages are searched
    channels = (await get_group(message.chat.id))["channels"]
    if not channels:
        return

    if message.text.startswith("/"):
        return  # Ignore commands

    query = message.text
    head = f"<u>⭕ Here are the results, 👇</u>\n\n"
    results = ""

    try:
        for channel in channels:
            # Search for the query in each channel
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                results += f"<b><I>♻️ {name}\n🔗 {msg.link}</I></b>\n\n"

        if not results:
            # If no results found, search IMDb
            movies = await search_imdb(query)
            buttons = [InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}") for movie in movies]
            msg = await message.reply_photo(
                photo="https://graph.org/file/c361a803c7b70fc50d435.jpg",
                caption="<b><I>🔻 I Couldn't find anything related to Your Query😕.\n🔺 Did you mean any of these?</I></b>",
                reply_markup=InlineKeyboardMarkup([[button] for button in buttons]),
                reply_to_message_id=message.message_id  # Reply to the original message
            )
        else:
            # If results found, send them in chunks
            await send_message_in_chunks(bot, message.chat.id, head + results, reply_to_message_id=message.message_id)

    except Exception as e:
        print(f"Error: {e}")
        pass


# Function to handle callback queries (recheck search results)
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
    query = await search_imdb(id)  # Perform an IMDb search for the movie ID
    channels = (await get_group(update.message.chat.id))["channels"]
    head = "<u>⭕ I Have Searched Movie With Possible Misspelling, but take care next time 👇\n\n</u>"
    results = ""

    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                results += f"<b><I>♻️🍿 {name}</I></b>\n\n🔗 {msg.link}</I></b>\n\n"

        if not results:
            # No results found, allow user to request admin for a movie search
            return await update.message.edit(
                "🔺 Still no results found! Please Request To Group Admin 🔻",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Request To Admin 🎯", callback_data=f"request_{id}")]])
            )

        await send_message_in_chunks(bot, update.message.chat.id, head + results, reply_to_message_id=update.message.reply_to_message.message_id)

    except Exception as e:
        await update.message.edit(f"❌ Error: `{e}`")


# Function to handle requests to the admin (sending the IMDb movie request)
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
    await bot.send_message(chat_id=admin, text=text, disable_web_page_preview=True)

    await update.answer("✅ Request Sent To Admin", show_alert=True)
    await update.message.delete(60)


# Run the bot
if __name__ == "__main__":
    bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    bot.run()
