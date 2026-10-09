from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.helpers import is_admin
from database import get_session, get_chat

async def setprefix_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set command prefixes"""
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /setprefix ./!")
        return
    
    prefixes = ''.join(context.args)
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        chat.command_prefixes = prefixes
        session.commit()
        await update.message.reply_text(f"✅ Command prefixes set to: {prefixes}")
    finally:
        session.close()

async def prefix_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current prefixes"""
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        prefixes = chat.command_prefixes or '/'
        await update.message.reply_text(f"Current prefixes: `{prefixes}`", parse_mode='Markdown')
    finally:
        session.close()

def get_handlers():
    return [
        CommandHandler('setprefix', setprefix_command),
        CommandHandler('prefix', prefix_command),
    ]