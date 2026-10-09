from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, CommandHandler
from utils.helpers import is_authorized_for_gmute
from database import get_session, GlobalMute

async def gmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hidden global mute command - only authorized users"""
    user_id = update.effective_user.id
    
    if not is_authorized_for_gmute(user_id):
        # Pretend command doesn't exist
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /gmute user_id [reason]")
        return
    
    target_id = int(context.args[0])
    reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "No reason"
    
    session = get_session()
    try:
        # Check if already gmuted
        existing = session.query(GlobalMute).filter_by(user_id=target_id).first()
        if existing:
            await update.message.reply_text("ℹ️ User is already globally muted")
            return
        
        gmute = GlobalMute(
            user_id=target_id,
            reason=reason,
            muted_by=user_id
        )
        session.add(gmute)
        session.commit()
        
        await update.message.reply_text(f"🔇 Globally muted user {target_id}")
    finally:
        session.close()

async def ungmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove global mute"""
    user_id = update.effective_user.id
    
    if not is_authorized_for_gmute(user_id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /ungmute user_id")
        return
    
    target_id = int(context.args[0])
    
    session = get_session()
    try:
        session.query(GlobalMute).filter_by(user_id=target_id).delete()
        session.commit()
        await update.message.reply_text(f"🔊 Removed global mute from user {target_id}")
    finally:
        session.close()

async def gmutelist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all globally muted users"""
    user_id = update.effective_user.id
    
    if not is_authorized_for_gmute(user_id):
        return
    
    session = get_session()
    try:
        mutes = session.query(GlobalMute).all()
        
        if not mutes:
            await update.message.reply_text("ℹ️ No global mutes")
            return
        
        text = "🔇 <b>Global Mutes:</b>\n\n"
        for mute in mutes:
            text += f"• User ID: <code>{mute.user_id}</code>\n"
            text += f"  Reason: {mute.reason}\n\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
    finally:
        session.close()

def get_handlers():
    return [
        CommandHandler('gmute', gmute_command),
        CommandHandler('ungmute', ungmute_command),
        CommandHandler('gmutelist', gmutelist_command),
    ]