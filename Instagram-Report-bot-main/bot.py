import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import asyncio

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation
SELECTING_STYLE, ADDING_TEXT = range(2)

# Sticker styles
STICKER_STYLES = {
    'bold': {'text': '🔥 Bold', 'style': '**', 'emoji': '🔥'},
    'italic': {'text': '💫 Italic', 'style': '*', 'emoji': '💫'},
    'code': {'text': '💻 Code', 'style': '`', 'emoji': '💻'},
    'underline': {'text': '⭐ Underline', 'style': '__', 'emoji': '⭐'},
    'strikethrough': {'text': '⚡ Strike', 'style': '~~', 'emoji': '⚡'},
}

async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is member of required channel"""
    try:
        channel_username = os.getenv('FORCE_JOIN_CHANNEL', '').replace('@', '')
        if not channel_username:
            return True
            
        user_id = update.effective_user.id
        member = await context.bot.get_chat_member(f"@{channel_username}", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Membership check failed: {e}")
        # If we can't check, allow to continue (for testing)
        return True

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the bot and show main menu"""
    # Check membership first
    if not await check_membership(update, context):
        keyboard = [
            [InlineKeyboardButton("📺 Join Channel", url=f"https://t.me/{os.getenv('FORCE_JOIN_CHANNEL', '')}")],
            [InlineKeyboardButton("✅ I Joined", callback_data='check_join')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "برای استفاده از ربات، لطفا در کانال عضو شوید.\n\n"
            "To use the bot, please join the channel:",
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    
    # Show main sticker menu
    keyboard = []
    for key, style in STICKER_STYLES.items():
        keyboard.append([InlineKeyboardButton(f"{style['emoji']} {style['text']}", callback_data=f'style_{key}')])
    
    keyboard.append([
        [InlineKeyboardButton("🎨 Custom Style", callback_data='custom_style')],
        [InlineKeyboardButton("❓ Help", callback_data='help')]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎭 *Welcome to Sticker Bot!*\n\n"
        "Choose a sticker style for your text:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECTING_STYLE

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle 'I Joined' button click"""
    query = update.callback_query
    await query.answer()
    
    if await check_membership(update, context):
        # User is now a member, show main menu
        keyboard = []
        for key, style in STICKER_STYLES.items():
            keyboard.append([InlineKeyboardButton(f"{style['emoji']} {style['text']}", callback_data=f'style_{key}')])
        
        keyboard.append([
            [InlineKeyboardButton("🎨 Custom Style", callback_data='custom_style')],
            [InlineKeyboardButton("❓ Help", callback_data='help')]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "✅ *Thank you for joining!* 🎉\n\n"
            "Choose a sticker style for your text:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return SELECTING_STYLE
    else:
        await query.edit_message_text(
            "❌ You're still not a member of the channel. "
            "Please join the channel first and then try again."
        )
        return ConversationHandler.END

async def style_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle style selection"""
    query = update.callback_query
    await query.answer()
    
    style_key = query.data.replace('style_', '')
    if style_key in STICKER_STYLES:
        style_info = STICKER_STYLES[style_key]
        context.user_data['selected_style'] = style_key
        
        # Create back button
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Styles", callback_data='back_to_styles')],
            [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        example_text = f"{style_info['style']}Hello World{style_info['style']}"
        
        await query.edit_message_text(
            f"{style_info['emoji']} *{style_info['text']} Style Selected*\n\n"
            f"Example: {example_text}\n\n"
            f"Now send me your text to convert to this style:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return ADDING_TEXT

async def custom_style_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle custom style selection"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back", callback_data='back_to_styles')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎨 *Custom Style*\n\n"
        "Send your text with custom markdown:\n"
        "`**bold**`, `*italic*`, `__underline__`, `~~strike~~`\n\n"
        "Or send regular text and I'll help you style it!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return ADDING_TEXT

async def back_to_styles_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to style selection"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for key, style in STICKER_STYLES.items():
        keyboard.append([InlineKeyboardButton(f"{style['emoji']} {style['text']}", callback_data=f'style_{key}')])
    
    keyboard.append([
        [InlineKeyboardButton("🎨 Custom Style", callback_data='custom_style')],
        [InlineKeyboardButton("❓ Help", callback_data='help')]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎭 *Choose a sticker style for your text:*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECTING_STYLE

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to main menu"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for key, style in STICKER_STYLES.items():
        keyboard.append([InlineKeyboardButton(f"{style['emoji']} {style['text']}", callback_data=f'style_{key}')])
    
    keyboard.append([
        [InlineKeyboardButton("🎨 Custom Style", callback_data='custom_style')],
        [InlineKeyboardButton("❓ Help", callback_data='help')]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎭 *Welcome to Sticker Bot!*\n\n"
        "Choose a sticker style for your text:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECTING_STYLE

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show help information"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back", callback_data='back_to_styles')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    help_text = """
    ❓ *How to use Sticker Bot:*
    
    1. Choose a style from the menu
    2. Send your text
    3. Get styled text instantly!
    
    🎨 *Available Styles:*
    • 🔥 **Bold** - Makes text bold
    • 💫 *Italic* - Makes text italic
    • 💻 `Code` - Code style formatting
    • ⭐ __Underline__ - Underlines text
    • ⚡ ~~Strike~~ - Strikethrough text
    
    💡 *Tips:*
    • You can use multiple styles together
    • Send /start to return to main menu
    • Custom markdown also works!
    """
    
    await query.edit_message_text(
        help_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECTING_STYLE

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle text messages and apply selected style"""
    user_text = update.message.text
    selected_style = context.user_data.get('selected_style')
    
    keyboard = [
        [InlineKeyboardButton("🎨 New Style", callback_data='back_to_styles')],
        [InlineKeyboardButton("📝 Another Text", callback_data='another_text')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if selected_style and selected_style in STICKER_STYLES:
        style_info = STICKER_STYLES[selected_style]
        styled_text = f"{style_info['style']}{user_text}{style_info['style']}"
        
        await update.message.reply_text(
            f"{style_info['emoji']} *Your Styled Text:*\n\n"
            f"{styled_text}\n\n"
            f"💡 Copy the text above and paste it anywhere!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        # Custom markdown or regular text
        await update.message.reply_text(
            f"📝 *Your Text:*\n\n"
            f"{user_text}\n\n"
            f"💡 You can use markdown: `**bold**`, `*italic*`, etc.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    return SELECTING_STYLE

async def another_text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle 'Another Text' button"""
    query = update.callback_query
    await query.answer()
    
    selected_style = context.user_data.get('selected_style')
    if selected_style and selected_style in STICKER_STYLES:
        style_info = STICKER_STYLES[selected_style]
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Styles", callback_data='back_to_styles')],
            [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📝 *Send me another text for {style_info['text']} style:*\n\n"
            f"Example: {style_info['style']}Your text here{style_info['style']}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return ADDING_TEXT
    else:
        await query.edit_message_text(
            "📝 *Send me another text with custom markdown:*",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data='back_to_styles')
            ]]),
            parse_mode='Markdown'
        )
        return ADDING_TEXT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation"""
    await update.message.reply_text(
        "Operation cancelled. Send /start to begin again."
    )
    return ConversationHandler.END

def main():
    """Main function to run the bot"""
    # Get the token
    token = os.getenv('API_TOKEN')
    if not token:
        logger.error("API_TOKEN environment variable not set!")
        return
    
    # Create the Application with optimized settings for Vercel
    application = (
        Application.builder()
        .token(token)
        .pool_timeout(30.0)  # Increase timeout
        .connection_pool_size(1)  # Reduce pool size for serverless
        .read_timeout(10)
        .write_timeout(10)
        .connect_timeout(10)
        .build()
    )
    
    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            SELECTING_STYLE: [
                CallbackQueryHandler(check_join_callback, pattern='^check_join$'),
                CallbackQueryHandler(style_selection_callback, pattern='^style_'),
                CallbackQueryHandler(custom_style_callback, pattern='^custom_style$'),
                CallbackQueryHandler(back_to_styles_callback, pattern='^back_to_styles$'),
                CallbackQueryHandler(main_menu_callback, pattern='^main_menu$'),
                CallbackQueryHandler(help_callback, pattern='^help$'),
            ],
            ADDING_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message),
                CallbackQueryHandler(back_to_styles_callback, pattern='^back_to_styles$'),
                CallbackQueryHandler(main_menu_callback, pattern='^main_menu$'),
                CallbackQueryHandler(another_text_callback, pattern='^another_text$'),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_chat=True,
        per_user=True,
        per_message=False,
    )
    
    # Add handler to application
    application.add_handler(conv_handler)
    
    return application

# Create application instance for Vercel
app = main()