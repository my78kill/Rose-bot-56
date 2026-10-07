import os
import threading
from flask import Flask
import bot

flask_app = Flask("live")


@flask_app.route("/")
def home():
    return "Bot is alive and running!"


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(
        host="0.0.0.0",
        port=port,
        threaded=True,
        use_reloader=False
    )


threading.Thread(target=run_flask, daemon=True).start()

app = bot.build_app()
app.add_error_handler(bot.error_handler)
app.run_polling(drop_pending_updates=True)
