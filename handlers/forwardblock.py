from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from utils.helpers import is_admin
from database import get_session, get_chat

async def blockforward_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle forward blocking"""
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        session = get_session()
        try:
            chat = get_chat(session, update.effective_chat.id)
            status = "enabled" if chat.block_forward else "disabled"
            await update.message.reply_text(f"Block forward is {status}")
        finally:
            session.close()
        return
    
    setting = context.args[0].lower()
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        if setting in ['on', 'yes', 'true']:
            chat.block_forward = True
            await update.message.reply_text("✅ Forward blocking enabled!")
        elif setting in ['off', 'no', 'false']:
            chat.block_forward = False
            await update.message.reply_text("✅ Forward blocking disabled")
        session.commit()
    finally:
        session.close()

async def check_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check and handle forwarded messages"""
    if not update.message or not update.message.forward_origin:
        return
    
    # Skip admins
    if await is_admin(update, context, update.effective_user.id):
        return
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        
        if not chat.block_forward:
            return
        
        # Delete the forwarded message
        await update.message.delete()
        
        # Apply punishment based on mode
        if chat.block_forward_mode == 'mute':
            from telegram import ChatPermissions
            await context.bot.restrict_chat_member(
                update.effective_chat.id,
                update.effective_user.id,
                ChatPermissions(can_send_messages=False)
            )
            await context.bot.send_message(
                update.effective_chat.id,
                f"🔇 {update.effective_user.first_name} muted for forwarding!"
            )
        elif chat.block_forward_mode == 'ban':
            await context.bot.ban_chat_member(
                update.effective_chat.id,
                update.effective_user.id
            )
            await context.bot.send_message(
                update.effective_chat.id,
                f"🔨 {update.effective_user.first_name} banned for forwarding!"
            )
        else:
            # Just delete
            await context.bot.send_message(
                update.effective_chat.id,
                f"🚫 Forward deleted from {update.effective_user.first_name}"
            )
    finally:
        session.close()

def get_handlers():
    return [
        CommandHandler('blockforward', blockforward_command),
        MessageHandler(filters.FORWARDED & ~filters.COMMAND, check_forward),
    ]