from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.helpers import is_admin
from database import get_session, get_chat, ChatLock

LOCK_TYPES = [
    'url', 'invitelink', 'forward', 'sticker', 'photo', 'video', 
    'gif', 'audio', 'document', 'voice', 'poll', 'contact', 
    'location', 'command', 'emoji', 'phone', 'email', 'cjk', 
    'cyrillic', 'rtl', 'zalgo', 'all'
]

async def lock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /lock url/invitelink/forward/etc")
        return
    
    lock_type = context.args[0].lower()
    
    if lock_type not in LOCK_TYPES:
        await update.message.reply_text(f"⚠️ Invalid lock type. Use /locktypes to see all.")
        return
    
    session = get_session()
    try:
        # Check if already locked
        existing = session.query(ChatLock).filter_by(
            chat_id=update.effective_chat.id,
            lock_type=lock_type
        ).first()
        
        if existing:
            await update.message.reply_text(f"🔒 {lock_type} is already locked!")
            return
        
        lock = ChatLock(
            chat_id=update.effective_chat.id,
            lock_type=lock_type
        )
        session.add(lock)
        session.commit()
        await update.message.reply_text(f"🔒 Locked {lock_type}")
    finally:
        session.close()

async def unlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /unlock url/invitelink/etc")
        return
    
    lock_type = context.args[0].lower()
    
    session = get_session()
    try:
        lock = session.query(ChatLock).filter_by(
            chat_id=update.effective_chat.id,
            lock_type=lock_type
        ).first()
        
        if lock:
            session.delete(lock)
            session.commit()
            await update.message.reply_text(f"🔓 Unlocked {lock_type}")
        else:
            await update.message.reply_text(f"ℹ️ {lock_type} is not locked")
    finally:
        session.close()

async def locks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    try:
        locks = session.query(ChatLock).filter_by(
            chat_id=update.effective_chat.id
        ).all()
        
        if not locks:
            await update.message.reply_text("ℹ️ No locks active")
            return
        
        text = "🔒 <b>Active Locks:</b>\n\n"
        for lock in locks:
            text += f"• {lock.lock_type}\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
    finally:
        session.close()

async def locktypes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🔒 <b>Available Lock Types:</b>\n\n"
    text += ", ".join(LOCK_TYPES)
    await update.message.reply_text(text, parse_mode='HTML')

def get_handlers():
    return [
        CommandHandler('lock', lock_command),
        CommandHandler('unlock', unlock_command),
        CommandHandler('locks', locks_command),
        CommandHandler('locktypes', locktypes_command),
    ]
