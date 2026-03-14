# ---------------------------------------------------
# File Name: Start.py
# Author: NeonAnurag
# GitHub: https://github.com/MyselfNeon/
# Telegram: https://t.me/MyelfNeon
# Created: 2025-11-21
# Last Modified: 2025-11-22
# Version: Latest
# License: MIT License
# ---------------------------------------------------

import logging
import math
import asyncio
import random
import time
from FileStream import __version__
from FileStream.bot import FileStream
from FileStream.server.exceptions import FIleNotFound
from FileStream.utils.bot_utils import gen_linkx, verify_user
from FileStream.config import Telegram # Assuming Telegram.START_PICS is now a list
from FileStream.utils.database import Database
from FileStream.utils.translation import LANG, BUTTON
from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums.parse_mode import ParseMode

db = Database(Telegram.DATABASE_URL, Telegram.SESSION_NAME)

# Supported Reactions
REACTIONS = [
    "🤝", "😇", "🤗", "😍", "👍", "🎅", "😐", "🥰", "🤩",
    "😱", "🤣", "😘", "👏", "😛", "😈", "🎉", "⚡️", "🫡",
    "🤓", "😎", "🏆", "🔥", "🤭", "🌚", "🆒", "👻", "😁"
]

@FileStream.on_message(filters.command('start') & filters.private)
async def start(bot: Client, message: Message):
    # 🌀 Random reaction at the start
    try:
        await message.react(
            emoji=random.choice(REACTIONS),
            big=True
        )
    except Exception as e:
        logging.warning(f"Reaction failed: {e}")

    # ✅ Proceed with your original logic
    if not await verify_user(bot, message):
        return

    start_parts = message.text.split(maxsplit=1)
    start_arg = start_parts[1].strip() if len(start_parts) > 1 else ""

    if start_arg.startswith("ref_"):
        inviter_raw = start_arg.split("ref_", 1)[-1]
        try:
            inviter_id = int(inviter_raw)
        except ValueError:
            inviter_id = 0

        if inviter_id and inviter_id != message.from_user.id:
            user = await db.get_user(message.from_user.id) or {}
            if not user.get("referred_by"):
                await db.col.update_one(
                    {"id": int(message.from_user.id)},
                    {"$set": {"referred_by": int(inviter_id), "referred_at": int(time.time())}},
                )
                await message.reply_text("✅ Referral tag applied. Complete your first verification to unlock inviter reward.")

    usr_cmd = start_arg.split("_")[-1] if start_arg else "/start"
    # 🌟 Select a random picture URL from the list
    try:
        random_start_pic = random.choice(Telegram.START_PICS)
    except (TypeError, IndexError):
        # Fallback if START_PICS is empty
        random_start_pic = None 

    if usr_cmd == "/start":
        # Check if a valid picture was selected
        if random_start_pic:
            await message.reply_photo(
                photo=random_start_pic, # Use the randomly selected URL
                caption=LANG.START_TEXT.format(message.from_user.mention, FileStream.username),
                parse_mode=ParseMode.HTML,
                reply_markup=BUTTON.START_BUTTONS
            )
        else:
            await message.reply_text(
                text=LANG.START_TEXT.format(message.from_user.mention, FileStream.username),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=BUTTON.START_BUTTONS
            )
    
    else:
        if "stream_" in message.text:
            try:
                file_check = await db.get_file(usr_cmd)
                file_id = str(file_check['_id'])
                if file_id == usr_cmd:
                    reply_markup, stream_text = await gen_linkx(
                        m=message,
                        _id=file_id,
                        name=[FileStream.username, FileStream.fname]
                    )
                    await message.reply_text(
                        text=stream_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                        reply_markup=reply_markup,
                        quote=True
                    )
            except FIleNotFound:
                await message.reply_text("File Not Found")
            except Exception as e:
                await message.reply_text("Something Went Wrong")
                logging.error(e)

        elif "file_" in message.text:
            try:
                file_check = await db.get_file(usr_cmd)
                db_id = str(file_check['_id'])
                file_id = file_check['file_id']
                file_name = file_check['file_name']
                if db_id == usr_cmd:
                    filex = await message.reply_cached_media(file_id=file_id, caption=f'**{file_name}**')
                    await asyncio.sleep(3600)
                    try:
                        await filex.delete()
                        await message.delete()
                    except Exception:
                        pass
            except FIleNotFound:
                await message.reply_text("**File Not Found**")
            except Exception as e:
                await message.reply_text("Something Went Wrong")
                logging.error(e)
        else:
            await message.reply_text("**Invalid Command**")

@FileStream.on_message(filters.private & filters.command(["about"]))
async def start(bot, message):
    if not await verify_user(bot, message):
        return
        
    try:
        random_start_pic = random.choice(Telegram.START_PICS)
    except (TypeError, IndexError):
        random_start_pic = None
        
    if random_start_pic:
        await message.reply_photo(
            photo=random_start_pic, 
            caption=LANG.ABOUT_TEXT.format(FileStream.fname, __version__),
            parse_mode=ParseMode.HTML,
            reply_markup=BUTTON.ABOUT_BUTTONS
        )
    
    else:
        await message.reply_text(
            text=LANG.ABOUT_TEXT.format(FileStream.fname, __version__),
            disable_web_page_preview=True,
            reply_markup=BUTTON.ABOUT_BUTTONS
        )

@FileStream.on_message(filters.command('help') & filters.private)
async def help_handler(bot, message):
    if not await verify_user(bot, message):
        return
        
    try:
        random_start_pic = random.choice(Telegram.START_PICS)
    except (TypeError, IndexError):
        random_start_pic = None
        
    if random_start_pic:
        await message.reply_photo(
            photo=random_start_pic, # Use the randomly selected URL
            caption=LANG.HELP_TEXT.format(Telegram.OWNER_ID),
            parse_mode=ParseMode.HTML,
            reply_markup=BUTTON.HELP_BUTTONS
        )

    else:
        await message.reply_text(
            text=LANG.HELP_TEXT.format(Telegram.OWNER_ID),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=BUTTON.HELP_BUTTONS
        )

@FileStream.on_message(filters.command('files') & filters.private)
async def my_files(bot: Client, message: Message):
    if not await verify_user(bot, message):
        return

    user_files, total_files = await db.find_files(message.from_user.id, [1, 10])
    file_list = []

    async for x in user_files:
        file_list.append([InlineKeyboardButton(x["file_name"], callback_data=f"myfile_{x['_id']}_{1}")])

    if total_files > 10:
        file_list.append([
            InlineKeyboardButton("◄", callback_data="N/A"),
            InlineKeyboardButton(f"1/{math.ceil(total_files / 10)}", callback_data="N/A"),
            InlineKeyboardButton("►", callback_data="userfiles_2")
        ])

    if not file_list:
        file_list.append([InlineKeyboardButton("ᴇᴍᴘᴛʏ", callback_data="N/A")])

    file_list.append([InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")])

    await message.reply_photo(
        photo=Telegram.FILE_PIC,
        caption=f"Total files: {total_files}",
        reply_markup=InlineKeyboardMarkup(file_list)
    )


@FileStream.on_message(filters.private & filters.text & ~filters.command(["start", "help", "about", "files"]))
async def handle_user_states(bot: Client, message: Message):
    if not await verify_user(bot, message):
        return

    state_doc = await db.get_user_state(message.from_user.id)
    if not state_doc:
        return

    state = state_doc.get("state")
    if state == "awaiting_coupon_code":
        code = (message.text or "").strip().upper()
        if not code:
            await message.reply_text("Please send a valid coupon code.")
            return

        coupon = await db.redeem_coupon_once_per_user(code, message.from_user.id)
        await db.clear_user_state(message.from_user.id)
        if coupon is None:
            await message.reply_text("❌ Invalid / inactive / expired coupon.")
            return
        if coupon is False:
            await message.reply_text("⚠️ You already redeemed this coupon.")
            return

        reward_type = coupon.get("reward_type")
        reward_value = coupon.get("reward_value")
        await message.reply_text(f"✅ Coupon redeemed. Reward: {reward_type} = {reward_value}.")
        return

# MyselfNeon
# Don't Remove Credit 🥺
# Telegram Channel @NeonFiles
