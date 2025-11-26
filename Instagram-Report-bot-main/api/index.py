import os
import sys
import logging
from flask import Flask, request, jsonify
from threading import Thread

# Configure logging for serverless environment
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
API_TOKEN = os.getenv('API_TOKEN')

if not API_TOKEN:
    logging.error("API_TOKEN environment variable not set!")
    sys.exit(1)

# Import and initialize the bot
try:
    import telebot
    bot = telebot.TeleBot(API_TOKEN)
    logging.info("Telegram bot initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize Telegram bot: {e}")
    sys.exit(1)

# Bot handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to Instagram Report Bot!")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
    Available commands:
    /start - Start the bot
    /help - Show this help message
    /getmeth <username> - Analyze Instagram profile
    """
    bot.reply_to(message, help_text)

# Webhook setup for Vercel
@app.route('/')
def home():
    return "Instagram Report Bot is running!"

@app.route('/api/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Method not allowed', 405

# Set webhook
def set_webhook():
    webhook_url = f"https://{os.getenv('VERCEL_URL')}/api/webhook"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    logging.info(f"Webhook set to: {webhook_url}")

# Initialize webhook on startup
set_webhook()

# Vercel serverless function handler
def handler(environ, start_response):
    return app(environ, start_response)

# Export for Vercel
if __name__ != "__main__":
    app.handler = handler

if __name__ == "__main__":
    app.run(debug=True, port=5000)