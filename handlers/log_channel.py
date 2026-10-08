from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.helpers import is_admin
from database import get_session, get_chat, LogChannel

async def setlog_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set log channel - must be used in channel first"""
    if update.effective_chat.type != 'channel':
        await update.message.reply_text(
            "⚠️ First add me to a channel as admin, then send /setlog there.\n"
            "Then forward that message to your group."
        )
        return
    
    # Store channel ID for later linking
    channel_id = update.effective_chat.id
    
    await update.message.reply_text(
        f"✅ Channel ID: <code>{channel_id}</code>\n"
        f"Forward this message to your group to link it.",
        parse_mode='HTML'
    )

async def unsetlog_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    session = get_session()
    try:
        log = session.query(LogChannel).filter_by(
            chat_id=update.effective_chat.id
        ).first()
        
        if log:
            session.delete(log)
            session.commit()
            await update.message.reply_text("✅ Log channel unlinked")
        else:
            await update.message.reply_text("ℹ️ No log channel set")
    finally:
        session.close()

async def logchannel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    try:
        log = session.query(LogChannel).filter_by(
            chat_id=update.effective_chat.id
        ).first()
        
        if log:
            await update.message.reply_text(f"ℹ️ Logging to channel ID: {log.channel_id}")
        else:
            await update.message.reply_text("ℹ️ No log channel set")
    finally:
        session.close()

def get_handlers():
    return [
        CommandHandler('setlog', setlog_command),
        CommandHandler('unsetlog', unsetlog_command),
        CommandHandler('logchannel', logchannel_command),
    ]
