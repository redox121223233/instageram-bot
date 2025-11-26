import os
import logging
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
API_TOKEN = os.getenv('API_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

if not API_TOKEN:
    logging.error("API_TOKEN environment variable not set!")
    # Don't exit in serverless, just log the error

# Import and initialize the bot
try:
    import telebot
    bot = telebot.TeleBot(API_TOKEN) if API_TOKEN else None
    logging.info("Telegram bot initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize Telegram bot: {e}")
    bot = None

# Simple bot handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to Instagram Report Bot! 🤖\n\nUse /help to see available commands.")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
📸 **Instagram Report Bot Commands:**

/start - Start the bot
/help - Show this help message
/getmeth <username> - Analyze Instagram profile

Example: /getmeth instagram_username

⚠️ Make sure you are a member of our channel to use this bot.
    """
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    bot.reply_to(message, "❌ Unknown command. Use /help to see available commands.")

# Webhook endpoint for Telegram
@app.route('/api/webhook', methods=['POST'])
def webhook():
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 500
    
    if request.method == 'POST':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return '', 200
        except Exception as e:
            logging.error(f"Error processing webhook: {e}")
            return jsonify({'error': 'Failed to process update'}), 400
    else:
        return 'Method not allowed', 405

# Health check endpoint
@app.route('/')
def home():
    return jsonify({
        'status': 'Instagram Report Bot is running! 🤖',
        'bot_initialized': bot is not None,
        'webhook_url': WEBHOOK_URL
    })

# Endpoint to set webhook manually
@app.route('/api/set-webhook', methods=['POST'])
def set_webhook_endpoint():
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 500
    
    webhook_url = request.json.get('webhook_url') or WEBHOOK_URL
    if not webhook_url:
        return jsonify({'error': 'webhook_url is required'}), 400
    
    try:
        bot.remove_webhook()
        result = bot.set_webhook(url=webhook_url)
        if result:
            logging.info(f"Webhook set to: {webhook_url}")
            return jsonify({'status': 'success', 'webhook_url': webhook_url})
        else:
            return jsonify({'error': 'Failed to set webhook'}), 500
    except Exception as e:
        logging.error(f"Error setting webhook: {e}")
        return jsonify({'error': str(e)}), 500

# Vercel serverless function handler
def handler(environ, start_response):
    return app(environ, start_response)

# Export for Vercel
app.handler = handler

if __name__ == "__main__":
    app.run(debug=True, port=5000)