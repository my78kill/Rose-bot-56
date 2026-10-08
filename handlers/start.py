from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.buttons import start_buttons

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == 'private':
        welcome_text = f"""<b>👋 Hello {user.first_name}!</b>

I'm <b>Rose</b>, a group management bot designed to help admins protect their Telegram chats.

<b>What I can do:</b>
• 🛡️ Anti-spam protection
• 👮 Admin management
• 🔒 Content locks
• ⚠️ Warning system
• 🤖 CAPTCHA verification
• And much more!

Add me to your group and promote me to admin to get started!"""
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=start_buttons(context.bot.username),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            "👋 Hi! I'm Rose lte. Make me an admin to start managing this group!\n\nUse /help in PM to see all commands."
        )

def get_handlers():
    return [CommandHandler('start', start_command)]
