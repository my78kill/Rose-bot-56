import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_token_here")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///rose_bot.db")
BOT_NAME = "Rose Bot"
SUPPORT_CHANNEL = "https://t.me/YourSupportChannel"
OWNER_ID = 123456789  # Your Telegram ID

# NEW: Authorized users for hidden gMute command (comma separated IDs)
GMUTE_AUTH_USERS = [
    int(x.strip()) for x in os.environ.get("GMUTE_AUTH_USERS", "123456789").split(",")
]

# Role hierarchy (highest to lowest)
ROLE_HIERARCHY = {
    'founder': 7,
    'cofounder': 6,
    'admin': 5,
    'moderator': 4,
    'cleaner': 3,
    'muter': 2,
    'helper': 1,
    'free': 0,
    None: -1
}

ROLE_EMOJIS = {
    'founder': '👑',
    'cofounder': '⚜️',
    'admin': '👮',
    'moderator': '👷',
    'cleaner': '🛃',
    'muter': '🙊',
    'helper': '⛑',
    'free': '🔓'
}