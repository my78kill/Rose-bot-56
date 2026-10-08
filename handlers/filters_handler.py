from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from utils.helpers import is_admin
from database import get_session, get_chat, ChatFilter

async def filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if len(context.args) < 2:
        await update.message.reply_text('⚠️ Usage: /filter "trigger" response')
        return
    
    trigger = context.args[0].lower()
    response = ' '.join(context.args[1:])
    
    session = get_session()
    try:
        # Check if exists
        existing = session.query(ChatFilter).filter_by(
            chat_id=update.effective_chat.id,
            trigger=trigger
        ).first()
        
        if existing:
            existing.response = response
            session.commit()
            await update.message.reply_text(f"✅ Updated filter for '{trigger}'")
        else:
            new_filter = ChatFilter(
                chat_id=update.effective_chat.id,
                trigger=trigger,
                response=response
            )
            session.add(new_filter)
            session.commit()
            await update.message.reply_text(f"✅ Added filter for '{trigger}'")
    finally:
        session.close()

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /stop trigger")
        return
    
    trigger = context.args[0].lower()
    
    session = get_session()
    try:
        filt = session.query(ChatFilter).filter_by(
            chat_id=update.effective_chat.id,
            trigger=trigger
        ).first()
        
        if filt:
            session.delete(filt)
            session.commit()
            await update.message.reply_text(f"✅ Removed filter for '{trigger}'")
        else:
            await update.message.reply_text(f"ℹ️ No filter found for '{trigger}'")
    finally:
        session.close()

async def filters_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    try:
        filts = session.query(ChatFilter).filter_by(
            chat_id=update.effective_chat.id
        ).all()
        
        if not filts:
            await update.message.reply_text("ℹ️ No filters set")
            return
        
        text = "🔍 <b>Active Filters:</b>\n\n"
        for filt in filts:
            text += f"• <code>{filt.trigger}</code>\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
    finally:
        session.close()

async def check_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check messages for filter triggers"""
    if not update.message or not update.message.text:
        return
    
    session = get_session()
    try:
        filts = session.query(ChatFilter).filter_by(
            chat_id=update.effective_chat.id
        ).all()
        
        text_lower = update.message.text.lower()
        
        for filt in filts:
            if filt.trigger in text_lower:
                await update.message.reply_text(filt.response)
                return
    finally:
        session.close()

def get_handlers():
    return [
        CommandHandler('filter', filter_command),
        CommandHandler('stop', stop_command),
        CommandHandler('filters', filters_command),
        MessageHandler(filters.TEXT & ~filters.COMMAND, check_filter),
    ]
