# ---------------------------------------------------
# File Name: Callback.py
# Author: NeonAnurag
# GitHub: https://github.com/MyselfNeon/
# Telegram: https://t.me/MyelfNeon
# Created: 2025-11-21
# Last Modified: 2025-11-22
# Version: Latest
# License: MIT License
# ---------------------------------------------------

import datetime
import math
import random
import time
from urllib.parse import quote_plus
from FileStream import __version__
from FileStream.bot import FileStream
from FileStream.config import Telegram, Server
from FileStream.utils.translation import LANG, BUTTON
from FileStream.utils.bot_utils import gen_link
from FileStream.utils.database import Database
from FileStream.utils.human_readable import humanbytes
from FileStream.utils.shortener import create_short_link, ShortenerError
from FileStream.server.exceptions import FIleNotFound
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.file_id import FileId, FileType, PHOTO_TYPES
from pyrogram.enums.parse_mode import ParseMode

db = Database(Telegram.DATABASE_URL, Telegram.SESSION_NAME)


async def show_home(update: CallbackQuery):
    await update.message.edit_text(
        text=LANG.START_TEXT.format(update.from_user.mention, FileStream.username),
        disable_web_page_preview=True,
        reply_markup=BUTTON.START_BUTTONS
    )


async def show_help(update: CallbackQuery):
    await update.message.edit_text(
        text=LANG.HELP_TEXT.format(Telegram.OWNER_ID),
        disable_web_page_preview=True,
        reply_markup=BUTTON.HELP_BUTTONS
    )


async def show_about(update: CallbackQuery):
    await update.message.edit_text(
        text=LANG.ABOUT_TEXT.format(FileStream.fname, __version__),
        disable_web_page_preview=True,
        reply_markup=BUTTON.ABOUT_BUTTONS
    )


def _extract_video_file_id(message):
    if getattr(message, "video", None):
        return message.video.file_id
    if getattr(message, "animation", None):
        return message.animation.file_id
    if getattr(message, "video_note", None):
        return message.video_note.file_id
    return None


async def _refresh_video_catalog_cache(bot, limit=80):
    channel_id = int(getattr(Telegram, "VIDEO_CATALOG_CHANNEL_ID", 0) or 0)
    if not channel_id:
        return []

    file_ids = []
    async for post in bot.get_chat_history(channel_id, limit=int(limit)):
        file_id = _extract_video_file_id(post)
        if file_id:
            file_ids.append(file_id)

    if file_ids:
        await db.set_catalog_file_ids(channel_id, file_ids)

    return file_ids


async def _send_watch_video(update: CallbackQuery, video_doc, premium_active: bool):
    file_id = video_doc.get("file_id")
    file_db_id = str(video_doc.get("_id"))
    if not file_id or not file_db_id:
        return False

    stream_url = f"{Server.URL}watch/{file_db_id}"
    fast_dl_url = f"{Server.URL}dl/{file_db_id}"

    if premium_active:
        download_button = InlineKeyboardButton("⚡ Fast Download", url=fast_dl_url)
    else:
        download_button = InlineKeyboardButton("⚡ Fast Download (Premium)", callback_data="premium_dl_locked")

    await update.message.reply_cached_media(
        file_id=file_id,
        caption="For stream online or fast download use below buttons.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🎬 Stream", url=stream_url),
                    download_button,
                ]
            ]
        ),
    )
    return True


async def handle_menu_watch(bot, update: CallbackQuery):
    access_state = await db.get_access_state(update.from_user.id) or {}
    now = int(time.time())

    premium_active = int(access_state.get("premium_until", 0) or 0) > now
    free_access_active = int(access_state.get("free_access_until", 0) or 0) > now
    tokens = int(access_state.get("tokens", 0) or 0)

    has_access = premium_active or free_access_active or tokens > 0
    if not has_access:
        await update.message.reply_photo(
            photo=Telegram.VERIFY_PIC,
            caption=(
                "<b>Access required to watch videos.</b>\n\n"
                "Choose one verification option:\n"
                "• <b>50 tokens</b>\n"
                "• <b>24 hours access</b>"
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("50 tokens", callback_data="premium_tokens_50"),
                        InlineKeyboardButton("24 hours access", callback_data="premium_access_24h"),
                    ]
                ]
            ),
        )
        await update.answer("Verification required.", show_alert=True)
        return

    random_videos = await db.get_random_video_files(limit=5)
    if len(random_videos) < 5:
        await update.message.reply_text(
            "Catalog is not ready yet. Ask admin to add at least 5 videos.",
        )
        return

    sent_count = 0
    token_deducted = 0

    for video_doc in random_videos:
        if not premium_active and not free_access_active:
            consumed = await db.consume_token(update.from_user.id, 1)
            if not consumed:
                break
            token_deducted += 1

        delivered = await _send_watch_video(update, video_doc, premium_active)
        if delivered:
            sent_count += 1

    if sent_count == 0:
        await update.answer("No tokens left to send videos.", show_alert=True)
        return

    if token_deducted:
        await update.answer(
            f"Sent {sent_count} videos. Deducted {token_deducted} token(s).",
            show_alert=True,
        )
    else:
        await update.answer(f"Sent {sent_count} videos.", show_alert=True)


async def handle_menu_submit(update: CallbackQuery):
    await db.set_user_state(update.from_user.id, "awaiting_video_submission")
    await update.message.reply_text(
        "🎬 <b>Send your video now.</b>\n\n"
        "Please send a video/animation/video note in your next message."
        " It will be submitted for admin review.",
        parse_mode=ParseMode.HTML,
    )
    await update.answer("Waiting for your video.", show_alert=True)


async def handle_menu_refer(update: CallbackQuery):
    ref_code = f"ref_{update.from_user.id}"
    referral_link = f"https://t.me/{FileStream.username}?start={quote_plus(ref_code)}"
    await update.message.reply_text(
        "🤝 <b>Your referral link</b>\n\n"
        f"{referral_link}\n\n"
        f"Reward: <b>{Telegram.REFERRAL_REWARD_TOKENS} tokens</b> when a referred user joins and verifies for the first time.",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    await update.answer("Referral link generated.", show_alert=True)


async def handle_menu_coupon(update: CallbackQuery):
    await db.set_user_state(update.from_user.id, "awaiting_coupon_code")
    await update.message.reply_text(
        "🎁 Send your coupon code in the next message.",
        parse_mode=ParseMode.HTML,
    )
    await update.answer("Waiting for coupon code.", show_alert=True)


async def handle_menu_help(update: CallbackQuery):
    await show_help(update)


def _fqdn_verify_link(code, user_id):
    return f"{Server.URL}verify/{code}?uid={int(user_id)}"


async def _create_verify_session(user_id, reward_type, reward_value, *, step=1, previous_code=None):
    callback_url = f"{Server.URL}verify/complete/{{code}}"
    context = {
        "user_id": int(user_id),
        "step": step,
    }

    placeholder_url = callback_url.replace("{code}", "__CODE__")
    short_data = create_short_link(placeholder_url, context)
    short_url_template = short_data.get("short_url")
    if not short_url_template:
        raise ShortenerError("Shortener did not return a URL")

    session = await db.create_verification_session(
        user_id=user_id,
        shortener_url=short_url_template,
        step=step,
        previous_code=previous_code,
        reward_type=reward_type,
        reward_value=reward_value,
        expires_in=3600,
    )

    final_callback = callback_url.replace("{code}", session["one_time_code"])
    context["code"] = session["one_time_code"]
    finalized_short_data = create_short_link(final_callback, context)
    finalized_short_url = finalized_short_data.get("short_url")

    await db.verify_sessions.update_one(
        {"one_time_code": session["one_time_code"]},
        {"$set": {"shortner_url": finalized_short_url}},
    )

    session["shortner_url"] = finalized_short_url
    return session


async def handle_menu_premium(update: CallbackQuery):
    plan_lines = [line.strip() for line in Telegram.PREMIUM_PLANS.split("|") if line.strip()]
    plans = "\n".join([f"• {line}" for line in plan_lines]) or "• Contact admin for latest plans"
    payment_note = f"UPI: <code>{Telegram.PREMIUM_UPI_ID}</code>\n" if Telegram.PREMIUM_UPI_ID else ""
    keyboard = [
        [InlineKeyboardButton("💬 Contact for Payment", url=Telegram.PREMIUM_SUPPORT_URL)],
        [InlineKeyboardButton("⬅️ Back", callback_data="home")],
    ]
    await update.message.edit_text(
        text=(
            "<b>💎 Buy Premium</b>\n\n"
            "<b>Available plans</b>\n"
            f"{plans}\n\n"
            "<b>Payment instructions</b>\n"
            f"{payment_note}"
            "After payment, send screenshot to admin for manual confirmation."
        ),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


MENU_CALLBACK_SERVICES = {
    "menu_watch": handle_menu_watch,
    "menu_submit": handle_menu_submit,
    "menu_refer": handle_menu_refer,
    "menu_coupon": handle_menu_coupon,
    "menu_help": handle_menu_help,
    "menu_premium": handle_menu_premium,
}

@FileStream.on_callback_query()
async def cb_data(bot, update: CallbackQuery):
    callback_data = update.data
    if callback_data in MENU_CALLBACK_SERVICES:
        if callback_data == "menu_watch":
            await MENU_CALLBACK_SERVICES[callback_data](bot, update)
        else:
            await MENU_CALLBACK_SERVICES[callback_data](update)
        return

    if callback_data == "premium_dl_locked":
        await update.answer("Fast Download is available for premium users only.", show_alert=True)
        return

    usr_cmd = callback_data.split("_")
    if usr_cmd[0] == "home":
        await show_home(update)
    elif usr_cmd[0] == "help":
        await show_help(update)
    elif usr_cmd[0] == "about":
        await show_about(update)

    elif usr_cmd[0] == "N/A":
        await update.answer("N/A", True)
    elif usr_cmd[0] == "close":
        await update.message.delete()
    elif usr_cmd[0] == "msgdelete":
        await update.message.edit_caption(
            caption="**Cᴏɴғɪʀᴍ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜᴇ Fɪʟᴇ**\n\n",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("ʏᴇs", callback_data=f"msgdelyes_{usr_cmd[1]}_{usr_cmd[2]}"),
                    InlineKeyboardButton("ɴᴏ", callback_data=f"myfile_{usr_cmd[1]}_{usr_cmd[2]}")
                ]
            ])
        )
    elif usr_cmd[0] == "msgdelyes":
        await delete_user_file(usr_cmd[1], int(usr_cmd[2]), update)
        return
    elif usr_cmd[0] == "msgdelpvt":
        await update.message.edit_caption(
            caption="**Cᴏɴғɪʀᴍ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜᴇ Fɪʟᴇ**\n\n",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("ʏᴇs", callback_data=f"msgdelpvtyes_{usr_cmd[1]}"),
                    InlineKeyboardButton("ɴᴏ", callback_data=f"mainstream_{usr_cmd[1]}")
                ]
            ])
        )
    elif usr_cmd[0] == "msgdelpvtyes":
        await delete_user_filex(usr_cmd[1], update)
        return

    elif usr_cmd[0] == "mainstream":
        _id = usr_cmd[1]
        reply_markup, stream_text = await gen_link(_id=_id)
        await update.message.edit_text(
            text=stream_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )

    elif usr_cmd[0] == "userfiles":
        file_list, total_files = await gen_file_list_button(int(usr_cmd[1]), update.from_user.id)
        await update.message.edit_caption(
            caption=f"Total files: {total_files}",
            reply_markup=InlineKeyboardMarkup(file_list)
        )

    elif usr_cmd[0] == "myfile":
        await gen_file_menu(usr_cmd[1], usr_cmd[2], update)
        return

    elif usr_cmd[0] == "sendfile":
        myfile = await db.get_file(usr_cmd[1])
        file_name = myfile['file_name']
        await update.answer(f"Sending File {file_name}")
        await update.message.reply_cached_media(myfile['file_id'], caption=f'**{file_name}**')

    elif usr_cmd[0] == "premium":
        if len(usr_cmd) >= 3 and usr_cmd[1] == "tokens" and usr_cmd[2] == "50":
            try:
                session = await _create_verify_session(
                    user_id=update.from_user.id,
                    reward_type="tokens",
                    reward_value=50,
                    step=1,
                )
                verify_url = _fqdn_verify_link(session["one_time_code"], update.from_user.id)
                await update.message.reply_text(
                    f"✅ 50 token verification link:\n{verify_url}",
                    disable_web_page_preview=True,
                )
                await update.answer("Verification link generated.", show_alert=True)
            except Exception as error:
                await update.answer(f"Failed: {error}", show_alert=True)
            return

        if len(usr_cmd) >= 3 and usr_cmd[1] == "access" and usr_cmd[2] == "24h":
            try:
                step1 = await _create_verify_session(
                    user_id=update.from_user.id,
                    reward_type="none",
                    reward_value=0,
                    step=1,
                )
                step2 = await _create_verify_session(
                    user_id=update.from_user.id,
                    reward_type="free_access_hours",
                    reward_value=24,
                    step=2,
                    previous_code=step1["one_time_code"],
                )
                link1 = _fqdn_verify_link(step1["one_time_code"], update.from_user.id)
                link2 = _fqdn_verify_link(step2["one_time_code"], update.from_user.id)
                await update.message.reply_text(
                    "✅ 24 hours access verification links:\n"
                    f"Step 1: {link1}\n"
                    f"Step 2: {link2}\n\n"
                    "⚠️ Complete Step 1 before opening Step 2.",
                    disable_web_page_preview=True,
                )
                await update.answer("Step links generated.", show_alert=True)
            except Exception as error:
                await update.answer(f"Failed: {error}", show_alert=True)
            return
    else:
        await update.message.delete()

async def gen_file_list_button(file_list_no: int, user_id: int):
    file_range = [file_list_no * 10 - 10 + 1, file_list_no * 10]
    user_files, total_files = await db.find_files(user_id, file_range)

    file_list = []
    async for x in user_files:
        file_list.append([InlineKeyboardButton(x["file_name"], callback_data=f"myfile_{x['_id']}_{file_list_no}")])

    if total_files > 10:
        file_list.append([
            InlineKeyboardButton("◄", callback_data=f"userfiles_{file_list_no-1}" if file_list_no > 1 else "N/A"),
            InlineKeyboardButton(f"{file_list_no}/{math.ceil(total_files / 10)}", callback_data="N/A"),
            InlineKeyboardButton("►", callback_data=f"userfiles_{file_list_no+1}" if total_files > file_list_no * 10 else "N/A")
        ])
    if not file_list:
        file_list.append([InlineKeyboardButton("ᴇᴍᴘᴛʏ", callback_data="N/A")])

    file_list.append([InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")])
    return file_list, total_files


async def gen_file_menu(_id, file_list_no, update: CallbackQuery):
    try:
        myfile_info = await db.get_file(_id)
    except FIleNotFound:
        await update.answer("File Not Found")
        return

    file_id = FileId.decode(myfile_info['file_id'])

    if file_id.file_type in PHOTO_TYPES:
        file_type = "Image"
    elif file_id.file_type == FileType.VOICE:
        file_type = "Voice"
    elif file_id.file_type in (FileType.VIDEO, FileType.ANIMATION, FileType.VIDEO_NOTE):
        file_type = "Video"
    elif file_id.file_type == FileType.DOCUMENT:
        file_type = "Document"
    elif file_id.file_type == FileType.STICKER:
        file_type = "Sticker"
    elif file_id.file_type == FileType.AUDIO:
        file_type = "Audio"
    else:
        file_type = "Unknown"

    page_link = f"{Server.URL}watch/{myfile_info['_id']}"
    stream_link = f"{Server.URL}dl/{myfile_info['_id']}"

    if "video" in file_type.lower():
        MYFILES_BUTTONS = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("sᴛʀᴇᴀᴍ", url=page_link),
                InlineKeyboardButton("ᴅᴏᴡɴʟᴏᴀᴅ", url=stream_link)
            ],
            [
                InlineKeyboardButton("ɢᴇᴛ ғɪʟᴇ", callback_data=f"sendfile_{myfile_info['_id']}"),
                InlineKeyboardButton("ʀᴇᴠᴏᴋᴇ ғɪʟᴇ", callback_data=f"msgdelete_{myfile_info['_id']}_{file_list_no}")
            ],
            [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data=f"userfiles_{file_list_no}")]
        ])
    else:
        MYFILES_BUTTONS = InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴅᴏᴡɴʟᴏᴀᴅ", url=stream_link)],
            [
                InlineKeyboardButton("ɢᴇᴛ ғɪʟᴇ", callback_data=f"sendfile_{myfile_info['_id']}"),
                InlineKeyboardButton("ʀᴇᴠᴏᴋᴇ ғɪʟᴇ", callback_data=f"msgdelete_{myfile_info['_id']}_{file_list_no}")
            ],
            [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data=f"userfiles_{file_list_no}")]
        ])

    TiMe = myfile_info['time']
    if isinstance(TiMe, float):
        date = datetime.datetime.fromtimestamp(TiMe)
    await update.edit_message_caption(
        caption="**File Name :** `{}`\n**File Size :** `{}`\n**File Type :** `{}`\n**Created On :** `{}`".format(
            myfile_info['file_name'],
            humanbytes(int(myfile_info['file_size'])),
            file_type,
            TiMe if isinstance(TiMe, str) else date.date()
        ),
        reply_markup=MYFILES_BUTTONS
    )


async def delete_user_file(_id, file_list_no: int, update: CallbackQuery):
    try:
        myfile_info = await db.get_file(_id)
    except FIleNotFound:
        await update.answer("File Already Deleted")
        return

    await db.delete_one_file(myfile_info['_id'])
    await db.count_links(update.from_user.id, "-")
    await update.message.edit_caption(
        caption="**Fɪʟᴇ Dᴇʟᴇᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ !**" +
                update.message.caption.replace("Cᴏɴғɪʀᴍ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜᴇ Fɪʟᴇ", ""),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="userfiles_1")]])
    )


async def delete_user_filex(_id, update: CallbackQuery):
    try:
        myfile_info = await db.get_file(_id)
    except FIleNotFound:
        await update.answer("File Already Deleted")
        return

    await db.delete_one_file(myfile_info['_id'])
    await db.count_links(update.from_user.id, "-")
    await update.message.edit_caption(
        caption="**Fɪʟᴇ Dᴇʟᴇᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ !**\n\n",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]])
                                    )


# MyselfNeon
# Don't Remove Credit 🥺
# Telegram Channel @NeonFiles
