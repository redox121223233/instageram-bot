import os
import sys
import logging
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global variables
bot_app = None

def init_bot():
    """Initialize the bot safely"""
    global bot_app
    try:
        # Import the bot application
        from bot import app as bot_application
        bot_app = bot_application
        logger.info("Sticker bot initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize sticker bot: {e}")
        return False

# Initialize bot
if not init_bot():
    logger.warning("Bot initialization failed, but continuing...")

# Health check endpoint
@app.route('/')
def home():
    try:
        return jsonify({
            'status': 'Sticker Bot is running! 🎭',
            'bot_initialized': bot_app is not None,
            'environment': os.getenv('VERCEL_ENV', 'unknown')
        })
    except Exception as e:
        logger.error(f"Error in home endpoint: {e}")
        return jsonify({'error': 'Internal error'}), 500

# Test endpoint
@app.route('/api/test')
def test():
    try:
        return jsonify({
            'message': 'Sticker bot test endpoint is working! 🎨',
            'method': 'GET',
            'path': '/api/test'
        })
    except Exception as e:
        logger.error(f"Error in test endpoint: {e}")
        return jsonify({'error': 'Test failed'}), 500

# Webhook endpoint for Telegram
@app.route('/api/webhook', methods=['POST'])
def webhook():
    try:
        if not bot_app:
            logger.error("Bot not initialized")
            return jsonify({'error': 'Bot not initialized'}), 500
        
        if request.method == 'POST':
            try:
                # Get the update data
                update_data = request.get_data()
                if not update_data:
                    logger.warning("Received empty webhook data")
                    return '', 200
                
                logger.info(f"Received webhook data: {len(update_data)} bytes")
                
                # Process the update asynchronously
                import asyncio
                from telegram.update import Update
                
                # Create asyncio event loop for serverless environment
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Parse the update
                    update = Update.de_json(update_data.decode('utf-8'), bot_app.bot)
                    
                    # Process the update
                    loop.run_until_complete(bot_app.process_update(update))
                    
                finally:
                    loop.close()
                
                return '', 200
                
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                return jsonify({'error': 'Failed to process update'}), 400
        else:
            return 'Method not allowed', 405
            
    except Exception as e:
        logger.error(f"Unexpected error in webhook: {e}")
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