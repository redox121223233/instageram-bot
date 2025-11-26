import os
import sys
import logging
from flask import Flask, request, jsonify

# Configure logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global variables
bot = None
API_TOKEN = None

def init_bot():
    """Initialize the bot safely"""
    global bot, API_TOKEN
    try:
        API_TOKEN = os.getenv('API_TOKEN')
        if not API_TOKEN:
            logger.error("API_TOKEN environment variable not set!")
            return False
        
        import telebot
        bot = telebot.TeleBot(API_TOKEN)
        logger.info("Telegram bot initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Telegram bot: {e}")
        return False

# Initialize bot safely
if not init_bot():
    logger.warning("Bot initialization failed, but continuing anyway...")

# Bot handlers (only if bot is initialized)
def setup_bot_handlers():
    if not bot:
        return
    
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        try:
            bot.reply_to(message, "Welcome to Instagram Report Bot! 🤖\n\nUse /help to see available commands.")
        except Exception as e:
            logger.error(f"Error in start handler: {e}")

    @bot.message_handler(commands=['help'])
    def send_help(message):
        try:
            help_text = """
📸 **Instagram Report Bot Commands:**

/start - Start the bot
/help - Show this help message
/getmeth <username> - Analyze Instagram profile

Example: /getmeth instagram_username

⚠️ Make sure you are a member of our channel to use this bot.
            """
            bot.reply_to(message, help_text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in help handler: {e}")

    @bot.message_handler(func=lambda message: True)
    def handle_unknown(message):
        try:
            bot.reply_to(message, "❌ Unknown command. Use /help to see available commands.")
        except Exception as e:
            logger.error(f"Error in unknown handler: {e}")

# Setup handlers if bot is available
setup_bot_handlers()

# Webhook endpoint for Telegram
@app.route('/api/webhook', methods=['POST'])
def webhook():
    try:
        if request.method == 'POST':
            if not bot:
                logger.error("Bot not initialized")
                return jsonify({'error': 'Bot not initialized'}), 500
            
            try:
                json_string = request.get_data().decode('utf-8')
                logger.info(f"Received webhook data: {json_string[:100]}...")
                
                import telebot
                update = telebot.types.Update.de_json(json_string)
                bot.process_new_updates([update])
                return '', 200
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                return jsonify({'error': 'Failed to process update'}), 400
        else:
            return 'Method not allowed', 405
    except Exception as e:
        logger.error(f"Unexpected error in webhook: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Health check endpoint
@app.route('/')
def home():
    try:
        return jsonify({
            'status': 'Instagram Report Bot is running! 🤖',
            'bot_initialized': bot is not None,
            'api_token_set': bool(API_TOKEN),
            'environment': os.getenv('VERCEL_ENV', 'unknown')
        })
    except Exception as e:
        logger.error(f"Error in home endpoint: {e}")
        return jsonify({'error': 'Internal error'}), 500

# Endpoint to set webhook manually
@app.route('/api/set-webhook', methods=['POST', 'GET'])
def set_webhook_endpoint():
    try:
        if not bot:
            return jsonify({'error': 'Bot not initialized'}), 500
        
        webhook_url = None
        if request.method == 'POST':
            webhook_url = request.json.get('webhook_url') if request.json else None
        else:
            webhook_url = request.args.get('webhook_url')
        
        if not webhook_url:
            # Try to construct from request
            webhook_url = f"https://{request.host}/api/webhook"
        
        if not webhook_url:
            return jsonify({'error': 'webhook_url is required'}), 400
        
        try:
            bot.remove_webhook()
            result = bot.set_webhook(url=webhook_url)
            if result:
                logger.info(f"Webhook set to: {webhook_url}")
                return jsonify({'status': 'success', 'webhook_url': webhook_url})
            else:
                return jsonify({'error': 'Failed to set webhook'}), 500
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in set_webhook: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Vercel serverless function handler
def handler(environ, start_response):
    """Main handler for Vercel serverless functions"""
    try:
        return app(environ, start_response)
    except Exception as e:
        logger.error(f"Error in handler: {e}")
        # Return a simple error response
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'application/json')]
        start_response(status, headers)
        return [json.dumps({'error': 'Internal server error'}).encode()]

# Export for Vercel
app.handler = handler

if __name__ == "__main__":
    # This will only run when running locally, not on Vercel
    try:
        logger.info("Starting local development server...")
        app.run(debug=True, port=5000)
    except Exception as e:
        logger.error(f"Error starting local server: {e}")
        sys.exit(1)