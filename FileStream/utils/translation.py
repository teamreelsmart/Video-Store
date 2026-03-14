# ---------------------------------------------------
# File Name: Translation.py
# Author: NeonAnurag
# GitHub: https://github.com/MyselfNeon/
# Telegram: https://t.me/MyelfNeon
# Created: 2025-11-21
# Last Modified: 2025-11-22
# Version: Latest
# License: MIT License
# ---------------------------------------------------

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from FileStream.config import Telegram

class LANG(object):

    START_TEXT = """
<b><i><blockquote>👋 Yoo !! {}</blockquote></i></b>
<b><i><blockquote>I’ᴍ A Tᴇʟᴇɢʀᴀᴍ Fɪʟᴇ Sᴛʀᴇᴀᴍɪɴɢ Bᴏᴛ.\nPʀᴏᴠɪᴅɪɴɢ Iɴsᴛᴀɴᴛ Sᴛʀᴇᴀᴍɪɴɢ Aɴᴅ Dɪʀᴇᴄᴛ Dᴏᴡɴʟᴏᴀᴅ Lɪɴᴋs 🖇️</i></b>\n
<b><i>Fᴜʟʟʏ Oᴘᴛɪᴍɪᴢᴇᴅ Fᴏʀ Bᴏᴛʜ Cʜᴀɴɴᴇʟs Aɴᴅ Pʀɪᴠᴀᴛᴇ Cʜᴀᴛs 🧩</i></b>\n
<b><i>💕 @{}</i></b></blockquote>"""

    HELP_TEXT = """
<b><i>➠ Aᴅᴅ Mᴇ As Aɴ Aᴅᴍɪɴ Iɴ Cʜᴀɴɴᴇʟ</i></b>
<b><i>➠ Sᴇɴᴅ Mᴇ Aɴʏ Dᴏᴄᴜᴍᴇɴᴛ Oʀ Mᴇᴅɪᴀ</i></b>
<b><i>➠ I Wɪʟʟ Pʀᴏᴠɪᴅᴇ Sᴛʀᴇᴀᴍᴀʙʟᴇ Lɪɴᴋ</i></b>\n
<b><i>Aᴅᴜʟᴛ Cᴏɴᴛᴇɴᴛ Sᴛʀɪᴄᴛʟʏ Pʀᴏʜɪʙɪᴛᴇᴅ.</i></b>\n
<i><b>🧑‍💻 Rᴇᴘᴏʀᴛ Bᴜɢs Tᴏ <a href='https://telegram.me/SnapLoverXBot'>Dᴇᴠᴇʟᴏᴘᴇʀ 👮</a></b></i>"""

    ABOUT_TEXT = """
<b><i>➠ Mʏ Nᴀᴍᴇ : {}</i></b>\n
<b><i>➠ Sɴᴀᴘ Lᴏᴠᴇʀ Nᴇᴛᴡᴏʀᴋ : <a href='https://newweb-95to.onrender.com/'>Cʟɪᴄᴋ Hᴇʀᴇ</a></i></b>
<b><i>➠ BᴀᴄᴋUᴘ 2.0 : <a href='https://t.me/+TvUmstJYM1I3ZGM1'>Cʟɪᴄᴋ Hᴇʀᴇ</a></i></b>
<b><i>➠ Dᴇᴠᴇʟᴏᴘᴇʀ : <a href='https://t.me/Snap_Lover8'>Snap Lover</a></i></b> 
<b><i>➠ Sɴᴀᴘ Lᴏᴠᴇʀ Dᴀɪʟʏ : <a href='https://t.me/+5000jEnshVVmYzg1'>Cʟɪᴄᴋ Hᴇʀᴇ</a></i></b> 
<b><i>➠ Nᴇᴡs Rᴏᴏᴍ : <a href='https://t.me/+NbpXnldC3AI2NTU1'>Cʟɪᴄᴋ Hᴇʀᴇ</a></i></b> 
<b><i>➠ ᴛᴜɴᴇʙᴏᴛs : <a href='https://t.me/TuneBots'>Cʟɪᴄᴋ Hᴇʀᴇ</a></i></b> 
<b><i>➠ Dɪsᴋᴡᴀʟᴀ ʟɪɴᴋs : <a href='https://t.me/+GHL_Gg64eBZlMTVl'>Cʟɪᴄᴋ Hᴇʀᴇ</a></i></b> 
"""

    STREAM_TEXT = """
<u>𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 !</u>\n
<b><i>📂 Fɪʟᴇ Nᴀᴍᴇ ➠</b>\n{}</i>\n
<b><i>📦 Fɪʟᴇ Sɪᴢᴇ ➠</b> {}</i>\n
<b><i>📥 Dᴏᴡɴʟᴏᴀᴅ ➠</i></b>\n<code>{}</code>\n
<b><i>🖥 Wᴀᴛᴄʜ ➠</i></b>\n<code>{}</code>\n
<b><i>🔗 Sʜᴀʀᴇ ➠</i></b>\n<code>{}</code>\n"""

    STREAM_TEXT_X = """
<i><u>𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 !</u></i>\n
<b><i>📂 Fɪʟᴇ Nᴀᴍᴇ ➠</b>\n{}</i>\n
<b><i>📦 Fɪʟᴇ Sɪᴢᴇ ➠</b> {}</i>\n
<b><i>📥 Dᴏᴡɴʟᴏᴀᴅ ➠</i></b>\n<code>{}</code>\n
<b><i>🔗 Sʜᴀʀᴇ ➠</i></b>\n<code>{}</code>\n"""

    BAN_TEXT = "__Sᴏʀʀʏ Sɪʀ, Yᴏᴜ Aʀᴇ Bᴀɴɴᴇᴅ Tᴏ Usᴇ Mᴇ.__\n\n**[Cᴏɴᴛᴀᴄᴛ Dᴇᴠᴇʟᴏᴘᴇʀ](tg://user?id={}) Tʜᴇʏ Wɪʟʟ Hᴇʟᴘ Yᴏᴜ**"


class BUTTON(object):

    START_BUTTONS = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton('Watch Videos', callback_data='menu_watch'),
                InlineKeyboardButton('Submit Video', callback_data='menu_submit')
            ],
            [
                InlineKeyboardButton('Refer Friends', callback_data='menu_refer'),
                InlineKeyboardButton('Redeem Coupon', callback_data='menu_coupon')
            ],
            [
                InlineKeyboardButton('Help', callback_data='menu_help'),
                InlineKeyboardButton('Buy Premium', callback_data='menu_premium')
            ]
        ]
    )

    HELP_BUTTONS = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴘ 🦠', url='https://t.me/Snap_Lover8'),
                InlineKeyboardButton("Aʙᴏᴜᴛ 😎", callback_data='about')
            ],
            [
                InlineKeyboardButton("Cʟᴏsᴇ ❌", callback_data='close'),
                InlineKeyboardButton('Hᴏᴍᴇ 🏠', callback_data='home')
            ]
        ]
    )

    ABOUT_BUTTONS = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton('Hᴇʟᴘ 🆘', callback_data='help'),
                InlineKeyboardButton('Sᴏᴜʀᴄᴇ 🚀', url='https://t.me/TuneBots')
            ],
            [
                InlineKeyboardButton('Cʟᴏsᴇ ❌', callback_data='close'),
                InlineKeyboardButton('Bᴀᴄᴋ ⬅️', callback_data='home')
            ]
        ]
    )


# MyselfNeon
# Don't Remove Credit 🥺
# Telegram Channel @NeonFiles
