import os
import threading
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Rose-Lite bot is alive!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, threaded=True)

def keep_alive():
    threading.Thread(target=run, daemon=True).start()
