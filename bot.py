"""
🌹 Rose Bot - Main Entry Point (Local Runner)
Full version with all handlers loaded
"""

import logging
from telegram.ext import Application
from config import BOT_TOKEN

# Import all handlers
from handlers import (
    start, help_menu, admin, bans, warnings_handler,
    locks, welcome, antiflood, blocklist, filters_handler,
    clean, pins, approval, antiraid, reports, disabling,
    log_channel, purge, roles, gmute, blockbots, 
    forwardblock, prefix
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Collect all handlers (ORDER MATTERS!)
    handlers = []

    # Core handlers (first)
    handlers.extend(start.get_handlers())
    handlers.extend(help_menu.get_handlers())
    handlers.extend(prefix.get_handlers())  # Prefix settings

    # Admin & Moderation
    handlers.extend(admin.get_handlers())
    handlers.extend(bans.get_handlers())
    handlers.extend(warnings_handler.get_handlers())
    handlers.extend(approval.get_handlers())
    handlers.extend(roles.get_handlers())  # NEW: Role system
    handlers.extend(purge.get_handlers())  # NEW: Purge commands

    # Content control
    handlers.extend(locks.get_handlers())
    handlers.extend(filters_handler.get_handlers())
    handlers.extend(blocklist.get_handlers())
    handlers.extend(blockbots.get_handlers())  # NEW: Block bots
    handlers.extend(forwardblock.get_handlers())  # NEW: Block forwards

    # Anti-spam
    handlers.extend(antiflood.get_handlers())
    handlers.extend(antiraid.get_handlers())

    # Group management
    handlers.extend(welcome.get_handlers())
    handlers.extend(pins.get_handlers())
    handlers.extend(clean.get_handlers())
    handlers.extend(disabling.get_handlers())

    # Utilities
    handlers.extend(reports.get_handlers())
    handlers.extend(log_channel.get_handlers())

    # Hidden features (last)
    handlers.extend(gmute.get_handlers())  # NEW: Hidden gMute

    # Add all handlers to application
    for handler in handlers:
        application.add_handler(handler)

    # Error handler
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("🌹 Rose Bot started with ALL features!")
    application.run_polling(
        allowed_updates=['message', 'callback_query', 'chat_member', 'edited_message']
    )


async def error_handler(update, context):
    """Log errors"""
    logger.error(f'Update {update} caused error {context.error}')


if __name__ == '__main__':
    main()
