from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from utils.helpers import is_admin
from database import get_session, get_chat, BlockList

async def addblocklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if len(context.args) < 1:
        await update.message.reply_text('⚠️ Usage: /addblocklist "word" reason')
        return
    
    trigger = context.args[0]
    reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Blacklisted"
    
    session = get_session()
    try:
        # Check if exists
        existing = session.query(BlockList).filter_by(
            chat_id=update.effective_chat.id,
            trigger=trigger.lower()
        ).first()
        
        if existing:
            await update.message.reply_text("⚠️ Already in blocklist")
            return
        
        block = BlockList(
            chat_id=update.effective_chat.id,
            trigger=trigger.lower(),
            reason=reason
        )
        session.add(block)
        session.commit()
        await update.message.reply_text(f"✅ Added '{trigger}' to blocklist")
    finally:
        session.close()

async def blocklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    try:
        blocks = session.query(BlockList).filter_by(
            chat_id=update.effective_chat.id
        ).all()
        
        if not blocks:
            await update.message.reply_text("ℹ️ No blocklisted words")
            return
        
        text = "🚫 <b>Blocklist:</b>\n\n"
        for block in blocks:
            text += f"• {block.trigger}"
            if block.reason:
                text += f" - {block.reason}"
            text += "\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
    finally:
        session.close()

async def rmblocklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /rmblocklist word")
        return
    
    trigger = context.args[0].lower()
    
    session = get_session()
    try:
        block = session.query(BlockList).filter_by(
            chat_id=update.effective_chat.id,
            trigger=trigger
        ).first()
        
        if block:
            session.delete(block)
            session.commit()
            await update.message.reply_text(f"✅ Removed '{trigger}' from blocklist")
        else:
            await update.message.reply_text(f"ℹ️ '{trigger}' not in blocklist")
    finally:
        session.close()

async def check_blocklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check messages for blocklisted words"""
    if not update.message or not update.message.text:
        return
    
    # Skip admins
    if await is_admin(update, context, update.effective_user.id):
        return
    
    session = get_session()
    try:
        blocks = session.query(BlockList).filter_by(
            chat_id=update.effective_chat.id
        ).all()
        
        text_lower = update.message.text.lower()
        
        for block in blocks:
            if block.trigger in text_lower:
                await update.message.delete()
                await update.message.reply_text(
                    f"🚫 {update.effective_user.first_name}, that word is not allowed!"
                )
                return
    finally:
        session.close()

def get_handlers():
    return [
        CommandHandler('addblocklist', addblocklist_command),
        CommandHandler('blocklist', blocklist_command),
        CommandHandler('rmblocklist', rmblocklist_command),
        MessageHandler(filters.TEXT & ~filters.COMMAND, check_blocklist),
    ]
