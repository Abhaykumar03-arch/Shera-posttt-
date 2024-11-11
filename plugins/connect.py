# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

from info import *
from utils import *
from plugins.generate import database
from pyrogram import Client, filters

async def get_user_session():
    vj = database.find_one({"chat_id": ADMIN})
    if vj is None:
        return None
    return Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID)

async def get_group_details(chat_id):
    try:
        group = await get_group(chat_id)
        return group
    except Exception as e:
        return None

@Client.on_message(filters.group & filters.command("connect"))
async def connect(bot, message):
    m = await message.reply("Connecting..")
    
    # Fetch user session
    user_session = await get_user_session()
    if user_session is None:
        return await message.reply("**Contact Admin and ask to log in to the bot.**")

    await user_session.connect()
    user = await user_session.get_me()

    # Fetch group details
    group = await get_group_details(message.chat.id)
    if group is None:
        return await bot.leave_chat(message.chat.id)

    user_id = group["user_id"]
    user_name = group["user_name"]
    verified = group["verified"]
    channels = group["channels"].copy()

    if message.from_user.id != user_id:
        return await m.edit(f"<b>Only {user_name} can use this command</b> 😁")
    
    if not verified:
        return await m.edit("💢 <b>This chat is not verified!\n⭕ Use /verify</b>")
    
    try:
        channel = int(message.command[-1])
        if channel in channels:
            return await m.edit("💢 <b>This channel is already connected! You can't connect again</b>")
        channels.append(channel)
    except ValueError:
        return await m.edit("❌ <b>Incorrect format! Use</b> `/connect ChannelID`")
    
    try:
        chat = await bot.get_chat(channel)
        group = await bot.get_chat(message.chat.id)
        c_link = chat.invite_link
        g_link = group.invite_link
        await user_session.join_chat(c_link)
    except Exception as e:
        if "The user is already a participant" in str(e):
            pass
        else:
            error_text = f"❌ <b>Error:</b> `{str(e)}`\n⭕ <b>Make sure I'm admin in both the channel and this group with all permissions, and {user.mention} is not banned there</b>"
            return await m.edit(error_text)

    await update_group(message.chat.id, {"channels": channels})
    await m.edit(f"💢 <b>Successfully connected to [{chat.title}]({c_link})!</b>", disable_web_page_preview=True)
    
    text = f"#NewConnection\n\nUser: {message.from_user.mention}\nGroup: [{group.title}]({g_link})\nChannel: [{chat.title}]({c_link})"
    await bot.send_message(chat_id=LOG_CHANNEL, text=text)


@Client.on_message(filters.group & filters.command("disconnect"))
async def disconnect(bot, message):
    user_session = await get_user_session()
    if user_session is None:
        return await message.reply("**Contact Admin and ask to log in to the bot.**")

    await user_session.connect()
    m = await message.reply("Please wait..")  

    group = await get_group_details(message.chat.id)
    if group is None:
        return await bot.leave_chat(message.chat.id)

    user_id = group["user_id"]
    user_name = group["user_name"]
    verified = group["verified"]
    channels = group["channels"].copy()

    if message.from_user.id != user_id:
        return await m.edit(f"Only {user_name} can use this command 😁")
    
    if not verified:
        return await m.edit("This chat is not verified!\nUse /verify")    

    try:
        channel = int(message.command[-1])
        if channel not in channels:
            return await m.edit("<b>This channel is not connected yet. Please check the Channel ID.</b>")
        channels.remove(channel)
    except ValueError:
        return await m.edit("❌ <b>Incorrect format! Use</b> `/disconnect ChannelID`")
    
    try:
        chat = await bot.get_chat(channel)
        group = await bot.get_chat(message.chat.id)
        c_link = chat.invite_link
        g_link = group.invite_link
        await user_session.leave_chat(channel)
    except Exception as e:
        error_text = f"❌ <b>Error:</b> `{str(e)}`\n💢 <b>Make sure I'm admin in both the channel and this group with all permissions, and {user.username or user.mention} is not banned there</b>"
        return await m.edit(error_text)

    await update_group(message.chat.id, {"channels": channels})
    await m.edit(f"💢 <b>Successfully disconnected from [{chat.title}]({c_link})!</b>", disable_web_page_preview=True)
    
    text = f"#DisConnection\n\nUser: {message.from_user.mention}\nGroup: [{group.title}]({g_link})\nChannel: [{chat.title}]({c_link})"
    await bot.send_message(chat_id=LOG_CHANNEL, text=text)


@Client.on_message(filters.group & filters.command("connections"))
async def connections(bot, message):
    group = await get_group_details(message.chat.id)
    if group is None:
        return await bot.leave_chat(message.chat.id)

    user_id = group["user_id"]
    user_name = group["user_name"]
    channels = group["channels"]
    f_sub = group["f_sub"]

    if message.from_user.id != user_id:
        return await message.reply(f"<b>Only {user_name} can use this command</b> 😁")

    if not channels:
        return await message.reply("<b>This group is not connected to any channels yet. Connect one using /connect</b>")

    text = "This group is currently connected to:\n\n"
    for channel in channels:
        try:
            chat = await bot.get_chat(channel)
            name = chat.title
            link = chat.invite_link
            text += f"🔗<b>Connected Channel - [{name}]({link})</b>\n"
        except Exception as e:
            await message.reply(f"❌ Error in `{channel}:`\n`{e}`")
    
    if f_sub:
        try:
            f_chat = await bot.get_chat(f_sub)
            f_title = f_chat.title
            f_link = f_chat.invite_link
            text += f"\nFSub: [{f_title}]({f_link})"
        except Exception as e:
            await message.reply(f"❌ <b>Error in FSub</b> (`{f_sub}`)\n`{e}`")
    
    await message.reply(text=text, disable_web_page_preview=True)
