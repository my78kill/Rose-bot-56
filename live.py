"""
🌹 Rose Bot - Render Deployment File
This keeps the bot alive on Render's web service
"""

from flask import Flask, jsonify
import threading
import logging
import os
from telegram.ext import Application
from config import BOT_TOKEN

# Import all handlers
from handlers import (
    start, help_menu, admin, bans, warnings_handler,
    locks, welcome, antiflood, blocklist, filters_handler,
    clean, pins, approval, antiraid, reports, disabling,
    log_channel
)

# Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "alive",
        "bot": "Rose Bot",
        "message": "Bot is running!"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def run_bot():
    """Run the Telegram bot"""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add all handlers
    handlers = []
    
    # Core handlers
    handlers.extend(start.get_handlers())
    handlers.extend(help_menu.get_handlers())
    
    # Admin & Moderation
    handlers.extend(admin.get_handlers())
    handlers.extend(bans.get_handlers())
    handlers.extend(warnings_handler.get_handlers())
    handlers.extend(approval.get_handlers())
    
    # Content control
    handlers.extend(locks.get_handlers())
    handlers.extend(filters_handler.get_handlers())
    handlers.extend(blocklist.get_handlers())
    
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
    
    for handler in handlers:
        application.add_handler(handler)
    
    # Error handler
    application.add_error_handler(error_handler)
    
    logger.info("🌹 Rose Bot started!")
    application.run_polling(allowed_updates=['message', 'callback_query', 'chat_member', 'edited_message'])

async def error_handler(update, context):
    logging.error(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    # Start Flask in separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run bot in main thread
    run_bot()
