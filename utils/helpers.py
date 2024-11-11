# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import asyncio
import logging
from info import *
from pyrogram import enums
from imdb import Cinemagoer
from pymongo.errors import DuplicateKeyError
from pyrogram.errors import UserNotParticipant
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid

# Initialize database client and collections
dbclient = AsyncIOMotorClient(DATABASE_URI)
db = dbclient["Channel-Filter"]
grp_col = db["GROUPS"]
user_col = db["USERS"]
dlt_col = db["Auto-Delete"]

ia = Cinemagoer()

async def add_group(group_id, group_name, user_name, user_id, channels, f_sub, verified):
    data = {
        "_id": group_id,
        "name": group_name,
        "user_id": user_id,
        "user_name": user_name,
        "channels": channels,
        "f_sub": f_sub,
        "verified": verified
    }
    try:
        await grp_col.insert_one(data)
    except DuplicateKeyError:
        pass  # Group already exists, no action needed
    except Exception as e:
        logging.error(f"Error adding group {group_id}: {str(e)}")

async def get_group(group_id):
    group = await grp_col.find_one({"_id": group_id})
    return dict(group) if group else None

async def get_groups():
    cursor = grp_col.find({})
    groups = await cursor.to_list(length=await grp_col.count_documents({}))
    return groups

async def update_group(group_id, new_data):
    result = await grp_col.update_one({"_id": group_id}, {"$set": new_data})
    return result.modified_count > 0

async def delete_group(group_id):
    result = await grp_col.delete_one({"_id": group_id})
    return result.deleted_count > 0

async def add_user(user_id, user_name):
    data = {"_id": user_id, "name": user_name}
    try:
        await user_col.insert_one(data)
    except DuplicateKeyError:
        pass  # User already exists, no action needed

async def get_users():
    cursor = user_col.find({})
    users = await cursor.to_list(length=await user_col.count_documents({}))
    return users

async def delete_user(user_id):
    result = await user_col.delete_one({"_id": user_id})
    return result.deleted_count > 0

async def search_imdb(query):
    try:
        # Search by IMDb ID
        if query.isdigit():
            movie = ia.get_movie(int(query))
            return movie["title"]
        # Search by movie title
        movies = ia.search_movie(query, results=10)
        return [{"title": movie["title"], "year": f" - {movie.get('year', 'N/A')}", "id": movie.movieID} for movie in movies]
    except Exception as e:
        logging.error(f"Error searching IMDb: {str(e)}")
        return []

async def force_sub(bot, message):
    group = await get_group(message.chat.id)
    if not group:
        logging.warning(f"Group not found: {message.chat.id}")
        return False

    f_sub = group.get("f_sub", False)
    admin_id = group.get("user_id")
    if not f_sub:
        return True  # No forced subscription required

    if message.from_user is None:
        return True  # Invalid user, but we'll allow the action

    try:
        f_link = (await bot.get_chat(f_sub)).invite_link
        member = await bot.get_chat_member(f_sub, message.from_user.id)
        if member.status == enums.ChatMemberStatus.BANNED:
            await message.reply(f"Sorry {message.from_user.mention}, you are banned in our channel.")
            await asyncio.sleep(10)
            await bot.ban_chat_member(message.chat.id, message.from_user.id)
            return False
    except UserNotParticipant:
        logging.info(f"{message.from_user.id} is not a participant in the channel.")
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await message.reply(f"<b>🚫 Please join the channel to send messages!</b>", 
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Join Channel", url=f_link)]]))
        await message.delete()
        return False
    except Exception as e:
        logging.error(f"Error in force_sub for {message.from_user.id}: {str(e)}")
        await bot.send_message(chat_id=admin_id, text=f"Error in force_sub: {str(e)}")
        return False
    else:
        return True

async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await delete_user(user_id)
        logging.info(f"{user_id} removed from database because the account is deleted.")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await delete_user(user_id)
        logging.info(f"{user_id} has an invalid peer ID.")
        return False, "Error"
    except Exception as e:
        logging.error(f"Error broadcasting message to {user_id}: {str(e)}")
        return False, "Error"
