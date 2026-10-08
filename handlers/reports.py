from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.helpers import is_admin
from database import get_session, get_chat

async def reports_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        session = get_session()
        try:
            chat = get_chat(session, update.effective_chat.id)
            status = "enabled" if chat.reports_enabled else "disabled"
            await update.message.reply_text(f"Reports are currently {status}")
        finally:
            session.close()
        return
    
    setting = context.args[0].lower()
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        if setting in ['on', 'yes', 'true']:
            chat.reports_enabled = True
            await update.message.reply_text("✅ Reports enabled")
        elif setting in ['off', 'no', 'false']:
            chat.reports_enabled = False
            await update.message.reply_text("✅ Reports disabled")
        session.commit()
    finally:
        session.close()

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message to report it")
        return
    
    # Check if reports enabled
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        if not chat.reports_enabled:
            return
        
        # Get admins
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        mentions = []
        for admin in admins:
            if not admin.user.is_bot:
                mentions.append(admin.user.mention_html())
        
        reported_msg = update.message.reply_to_message
        reporter = update.effective_user
        
        text = (
            f"🚨 <b>Report!</b>\n\n"
            f"Reporter: {reporter.mention_html()}\n"
            f"Reported Message: {reported_msg.link if hasattr(reported_msg, 'link') else 'N/A'}\n\n"
            f"Admins: {', '.join(mentions)}"
        )
        
        await update.message.reply_text(text, parse_mode='HTML')
    finally:
        session.close()

def get_handlers():
    return [
        CommandHandler('reports', reports_command),
        CommandHandler('report', report_command),
    ]
