"""
🌹 Rose Bot - Render Deployment File
"""

from flask import Flask, jsonify
import threading
import logging
import os
from telegram.ext import Application
from config import BOT_TOKEN

# Import ALL handlers
from handlers import (
    start, help_menu, admin, bans, warnings_handler,
    locks, welcome, antiflood, blocklist, filters_handler,
    clean, pins, approval, antiraid, reports, disabling,
    log_channel, purge, roles, gmute, blockbots, 
    forwardblock, prefix
)

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "alive", "bot": "Rose Bot", "message": "Bot is running!"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def run_bot():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ALL handlers
    handlers = []
    handlers.extend(start.get_handlers())
    handlers.extend(help_menu.get_handlers())
    handlers.extend(prefix.get_handlers())
    handlers.extend(admin.get_handlers())
    handlers.extend(bans.get_handlers())
    handlers.extend(warnings_handler.get_handlers())
    handlers.extend(approval.get_handlers())
    handlers.extend(roles.get_handlers())
    handlers.extend(purge.get_handlers())
    handlers.extend(locks.get_handlers())
    handlers.extend(filters_handler.get_handlers())
    handlers.extend(blocklist.get_handlers())
    handlers.extend(blockbots.get_handlers())
    handlers.extend(forwardblock.get_handlers())
    handlers.extend(antiflood.get_handlers())
    handlers.extend(antiraid.get_handlers())
    handlers.extend(welcome.get_handlers())
    handlers.extend(pins.get_handlers())
    handlers.extend(clean.get_handlers())
    handlers.extend(disabling.get_handlers())
    handlers.extend(reports.get_handlers())
    handlers.extend(log_channel.get_handlers())
    handlers.extend(gmute.get_handlers())
    
    for handler in handlers:
        application.add_handler(handler)
    
    application.add_error_handler(lambda u, c: logging.error(f'Error: {c.error}'))
    
    logger.info("🌹 Rose Bot with ALL features started!")
    application.run_polling(allowed_updates=['message', 'callback_query', 'chat_member', 'edited_message'])

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    run_bot()