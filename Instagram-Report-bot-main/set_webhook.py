"""
Script to set webhook for the sticker bot
"""
import asyncio
import os
from bot import app

async def set_webhook():
    """Set webhook for the bot"""
    webhook_url = os.getenv('WEBHOOK_URL') or input("Enter your Vercel URL (e.g., your-app.vercel.app): ")
    if not webhook_url.startswith('https://'):
        webhook_url = f"https://{webhook_url}"
    
    if not webhook_url.endswith('/api/webhook'):
        webhook_url = f"{webhook_url}/api/webhook"
    
    try:
        await app.bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook set successfully to: {webhook_url}")
        
        # Test webhook info
        webhook_info = await app.bot.get_webhook_info()
        print(f"📡 Webhook info: {webhook_info}")
        
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")

if __name__ == "__main__":
    asyncio.run(set_webhook())