import os
import logging
import telebot
from flask import Flask, request
from main import bot

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route('/api/webhook', methods=['POST'])
def webhook_handler():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Unsupported Media Type', 415

@app.route('/api/set_webhook')
def set_webhook():
    VERCEL_URL = os.environ.get('VERCEL_URL')
    if VERCEL_URL:
        bot.remove_webhook()
        webhook_url = f"https://{VERCEL_URL}/api/webhook"
        bot.set_webhook(url=webhook_url)
        return f"Webhook set to {webhook_url}", 200
    else:
        return "VERCEL_URL not found. Cannot set webhook.", 500

@app.route('/')
def index():
    return "Bot is alive!", 200
