from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.helpers import is_admin
from database import get_session, get_chat, Warning

async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        await update.message.reply_text("⚠️ You need to be an admin.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message to warn the user.")
        return
    
    user = update.message.reply_to_message.from_user
    reason = ' '.join(context.args) if context.args else "No reason given"
    
    session = get_session()
    try:
        # Add warning to database
        warning = Warning(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            reason=reason,
            warned_by=update.effective_user.id
        )
        session.add(warning)
        session.commit()
        
        # Count warnings
        warn_count = session.query(Warning).filter_by(
            chat_id=update.effective_chat.id,
            user_id=user.id
        ).count()
        
        chat = get_chat(session, update.effective_chat.id)
        
        await update.message.reply_text(
            f"⚠️ {user.first_name} has been warned.\n"
            f"Reason: {reason}\n"
            f"Warnings: {warn_count}/{chat.warn_limit}"
        )
        
        # Check if should punish
        if warn_count >= chat.warn_limit:
            if chat.warn_mode == 'ban':
                await context.bot.ban_chat_member(update.effective_chat.id, user.id)
                await update.message.reply_text(f"🔨 {user.first_name} has been banned for exceeding warning limit!")
            elif chat.warn_mode == 'kick':
                await context.bot.ban_chat_member(update.effective_chat.id, user.id)
                await context.bot.unban_chat_member(update.effective_chat.id, user.id)
                await update.message.reply_text(f"👢 {user.first_name} has been kicked for exceeding warning limit!")
            elif chat.warn_mode == 'mute':
                from telegram import ChatPermissions
                await context.bot.restrict_chat_member(
                    update.effective_chat.id, 
                    user.id, 
                    ChatPermissions(can_send_messages=False)
                )
                await update.message.reply_text(f"🔇 {user.first_name} has been muted for exceeding warning limit!")
                
    finally:
        session.close()

async def swarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Silent warn - deletes command after"""
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not update.message.reply_to_message:
        return
    
    user = update.message.reply_to_message.from_user
    
    session = get_session()
    try:
        warning = Warning(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            reason="Silent warning",
            warned_by=update.effective_user.id
        )
        session.add(warning)
        session.commit()
        
        # Delete command message
        await update.message.delete()
    finally:
        session.close()

async def dwarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Warn and delete offending message"""
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message to warn and delete.")
        return
    
    user = update.message.reply_to_message.from_user
    
    # Delete the offending message
    await update.message.reply_to_message.delete()
    
    session = get_session()
    try:
        warning = Warning(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            reason="Warn and delete",
            warned_by=update.effective_user.id
        )
        session.add(warning)
        session.commit()
        
        warn_count = session.query(Warning).filter_by(
            chat_id=update.effective_chat.id,
            user_id=user.id
        ).count()
        
        await update.message.reply_text(
            f"⚠️ {user.first_name} has been warned and message deleted.\n"
            f"Total warnings: {warn_count}"
        )
    finally:
        session.close()

async def rmwarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove last warning"""
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a user to remove their last warning.")
        return
    
    user = update.message.reply_to_message.from_user
    
    session = get_session()
    try:
        last_warning = session.query(Warning).filter_by(
            chat_id=update.effective_chat.id,
            user_id=user.id
        ).order_by(Warning.id.desc()).first()
        
        if last_warning:
            session.delete(last_warning)
            session.commit()
            await update.message.reply_text(f"✅ Removed last warning from {user.first_name}")
        else:
            await update.message.reply_text(f"ℹ️ {user.first_name} has no warnings")
    finally:
        session.close()

async def resetwarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all warnings"""
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a user to clear all warnings.")
        return
    
    user = update.message.reply_to_message.from_user
    
    session = get_session()
    try:
        session.query(Warning).filter_by(
            chat_id=update.effective_chat.id,
            user_id=user.id
        ).delete()
        session.commit()
        await update.message.reply_text(f"✅ Cleared all warnings from {user.first_name}")
    finally:
        session.close()

async def warns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check warning history"""
    if not update.message.reply_to_message and not context.args:
        await update.message.reply_text("⚠️ Reply to a user or provide user ID.")
        return
    
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    else:
        user_id = int(context.args[0])
        user = await context.bot.get_chat(user_id)
    
    session = get_session()
    try:
        warnings = session.query(Warning).filter_by(
            chat_id=update.effective_chat.id,
            user_id=user.id
        ).all()
        
        if not warnings:
            await update.message.reply_text(f"ℹ️ {user.first_name} has no warnings.")
            return
        
        text = f"⚠️ <b>Warnings for {user.first_name}:</b>\n\n"
        for i, w in enumerate(warnings, 1):
            text += f"{i}. {w.reason}\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
    finally:
        session.close()

async def setwarnlimit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set warning limit before punishment"""
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /setwarnlimit 3")
        return
    
    limit = int(context.args[0])
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        chat.warn_limit = limit
        session.commit()
        await update.message.reply_text(f"✅ Warning limit set to {limit}")
    finally:
        session.close()

async def setwarnmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set warning punishment mode"""
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /setwarnmode ban/kick/mute")
        return
    
    mode = context.args[0].lower()
    if mode not in ['ban', 'kick', 'mute']:
        await update.message.reply_text("⚠️ Mode must be: ban, kick, or mute")
        return
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        chat.warn_mode = mode
        session.commit()
        await update.message.reply_text(f"✅ Warning mode set to {mode}")
    finally:
        session.close()

def get_handlers():
    return [
        CommandHandler('warn', warn_command),
        CommandHandler('swarn', swarn_command),
        CommandHandler('dwarn', dwarn_command),
        CommandHandler('rmwarn', rmwarn_command),
        CommandHandler('resetwarn', resetwarn_command),
        CommandHandler('warns', warns_command),
        CommandHandler('setwarnlimit', setwarnlimit_command),
        CommandHandler('setwarnmode', setwarnmode_command),
    ]
