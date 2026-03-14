# ---------------------------------------------------
# File Name: Config.py
# Author: NeonAnurag
# GitHub: https://github.com/MyselfNeon/
# Telegram: https://t.me/MyelfNeon
# Created: 2025-11-21
# Last Modified: 2025-11-22
# Version: Latest
# License: MIT License
# ---------------------------------------------------

from os import environ as env
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# Telegram Configuration
class Telegram:
    API_ID = int(env.get("API_ID"))
    API_HASH = str(env.get("API_HASH"))
    BOT_TOKEN = str(env.get("BOT_TOKEN"))
    OWNER_ID = int(env.get('OWNER_ID', '6891095964'))
    WORKERS = int(env.get("WORKERS", "6"))  # 6 workers = 6 commands at once
    DATABASE_URL = str(env.get('DATABASE_URL'))
    UPDATES_CHANNEL = str(env.get('UPDATES_CHANNEL', "TuneBots"))
    SESSION_NAME = str(env.get('SESSION_NAME', 'FilesToLinkZBot'))
    FORCE_SUB_ID = env.get('FORCE_SUB_ID', '-1003870553259')
    FORCE_SUB = env.get('FORCE_UPDATES_CHANNEL', True)
    FORCE_SUB = True if str(FORCE_SUB).lower() == "true" else False
    SLEEP_THRESHOLD = int(env.get("SLEEP_THRESHOLD", "60"))
    FILE_PIC = env.get('FILE_PIC', "https://files.catbox.moe/10l8j0.jpg")
    
    # Comma-seperated urls to get random images on each start command
    START_PICS_STRING = env.get(
    'START_PICS',
    ",".join([
        "https://i.ibb.co/kV3sC266/637a97059cf0.jpg",
        "https://i.ibb.co/5WK4tFbp/0e282ebcc464.jpg",
        "https://i.ibb.co/Ps1JLz89/70dde20478b3.jpg",
        "https://i.ibb.co/20jPQ44R/05ea4ea9d996.jpg",
    ])
    )
    START_PICS = [url.strip() for url in START_PICS_STRING.split(',')]
    
    VERIFY_PIC = env.get('VERIFY_PIC', "https://i.ibb.co/5WK4tFbp/0e282ebcc464.jpg")
    VIDEO_CATALOG_CHANNEL_ID = int(env.get("VIDEO_CATALOG_CHANNEL_ID", "0"))
    MULTI_CLIENT = False
    FLOG_CHANNEL = int(env.get("FLOG_CHANNEL", '-1003542287615'))   # Logs channel for file logs
    ULOG_CHANNEL = int(env.get("ULOG_CHANNEL", '-1003591916255'))   # Logs channel for user logs
    MODE = env.get("MODE", "primary")
    SECONDARY = True if MODE.lower() == "secondary" else False
    AUTH_USERS = list(set(int(x) for x in str(env.get("AUTH_USERS", "")).split()))

# Server Configuration
class Server:
    PORT = int(env.get("PORT", 8080))  # Render will auto-assign or override this
    BIND_ADDRESS = str(env.get("BIND_ADDRESS", "0.0.0.0"))  # <-- important fix
    PING_INTERVAL = int(env.get("PING_INTERVAL", "1200"))
    HAS_SSL = str(env.get("HAS_SSL", "1").lower()) in ("1", "true", "t", "yes", "y")
    NO_PORT = str(env.get("NO_PORT", "1").lower()) in ("1", "true", "t", "yes", "y")
    FQDN = str(env.get("FQDN", "filestream-bot-njtx.onrender.com"))  # <-- your Render domain (no https://)
    URL = "http{}://{}{}/".format(
        "s" if HAS_SSL else "", FQDN, "" if NO_PORT else ":" + str(PORT)
    )

    SHORTENER_PROVIDER = str(env.get("SHORTENER_PROVIDER", "direct"))
    SHORTENER_API_KEY = str(env.get("SHORTENER_API_KEY", ""))
    SHORTENER_DOMAIN = str(env.get("SHORTENER_DOMAIN", ""))
    SHORTENER_TEMPLATE = str(env.get("SHORTENER_TEMPLATE", ""))
    SHORTENER_SECRET = str(env.get("SHORTENER_SECRET", ""))

# Keep-Alive URL
KEEP_ALIVE_URL = env.get("KEEP_ALIVE_URL", "")


# MyselfNeon
# Don't Remove Credit 🥺
# Telegram Channel @NeonFiles
