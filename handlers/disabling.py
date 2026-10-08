from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.helpers import is_admin
from database import get_session, get_chat

DISABLEABLE = [
    'adminlist', 'antiflood', 'approval', 'connect', 'fedadmins',
    'fedinfo', 'filters', 'flood', 'id', 'info', 'kickme', 'locks',
    'locktypes', 'notes', 'rules', 'runs', 'saved', 'warnings', 'warns'
]

async def disabled_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        disabled = chat.disabled_commands.split(',') if chat.disabled_commands else []
        
        if not disabled or disabled == ['']:
            await update.message.reply_text("ℹ️ No commands disabled")
            return
        
        text = "🚫 <b>Disabled Commands:</b>\n\n"
        for cmd in disabled:
            if cmd:
                text += f"• /{cmd}\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
    finally:
        session.close()

async def disableable_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "✅ <b>Disableable Commands:</b>\n\n"
    text += ", ".join([f"/{cmd}" for cmd in DISABLEABLE])
    await update.message.reply_text(text, parse_mode='HTML')

async def disable_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /disable commandname")
        return
    
    cmd = context.args[0].lower()
    
    if cmd not in DISABLEABLE:
        await update.message.reply_text(f"⚠️ /{cmd} cannot be disabled")
        return
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        disabled = chat.disabled_commands.split(',') if chat.disabled_commands else []
        
        if cmd in disabled:
            await update.message.reply_text(f"ℹ️ /{cmd} is already disabled")
            return
        
        disabled.append(cmd)
        chat.disabled_commands = ','.join(disabled)
        session.commit()
        await update.message.reply_text(f"✅ Disabled /{cmd}")
    finally:
        session.close()

async def enable_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /enable commandname")
        return
    
    cmd = context.args[0].lower()
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        disabled = chat.disabled_commands.split(',') if chat.disabled_commands else []
        
        if cmd not in disabled:
            await update.message.reply_text(f"ℹ️ /{cmd} is not disabled")
            return
        
        disabled.remove(cmd)
        chat.disabled_commands = ','.join(disabled) if disabled else ''
        session.commit()
        await update.message.reply_text(f"✅ Enabled /{cmd}")
    finally:
        session.close()

def get_handlers():
    return [
        CommandHandler('disabled', disabled_command),
        CommandHandler('disableable', disableable_command),
        CommandHandler('disable', disable_command),
        CommandHandler('enable', enable_command),
    ]
