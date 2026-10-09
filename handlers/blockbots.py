from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, CommandHandler, ChatMemberHandler
from utils.helpers import is_admin
from database import get_session, get_chat

async def blockbots_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle bot blocking"""
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        session = get_session()
        try:
            chat = get_chat(session, update.effective_chat.id)
            status = "enabled" if chat.block_bots else "disabled"
            await update.message.reply_text(f"Block bots is {status}")
        finally:
            session.close()
        return
    
    setting = context.args[0].lower()
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        if setting in ['on', 'yes', 'true']:
            chat.block_bots = True
            await update.message.reply_text("✅ Bot blocking enabled!\nNon-admins adding bots will be muted.")
        elif setting in ['off', 'no', 'false']:
            chat.block_bots = False
            await update.message.reply_text("✅ Bot blocking disabled")
        session.commit()
    finally:
        session.close()

async def handle_bot_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when a bot is added to chat"""
    if not update.chat_member:
        return
    
    new_member = update.chat_member.new_chat_member
    old_member = update.chat_member.old_chat_member
    
    # Check if new member is a bot
    if not new_member.user.is_bot:
        return
    
    # Check if bot was just added
    if old_member.status not in ['left', 'kicked']:
        return
    
    chat_id = update.chat_member.chat.id
    added_by = update.chat_member.from_user
    
    session = get_session()
    try:
        chat = get_chat(session, chat_id)
        
        if not chat.block_bots:
            return
        
        # Check if adder is admin
        if await is_admin(update, context, added_by.id):
            return
        
        # Mute the user who added bot
        await context.bot.restrict_chat_member(
            chat_id, 
            added_by.id,
            ChatPermissions(can_send_messages=False)
        )
        
        # Kick the bot
        await context.bot.ban_chat_member(chat_id, new_member.user.id)
        await context.bot.unban_chat_member(chat_id, new_member.user.id)
        
        await context.bot.send_message(
            chat_id,
            f"🚫 {added_by.first_name} tried to add a bot!\n"
            f"User muted, bot removed."
        )
    finally:
        session.close()

def get_handlers():
    return [
        CommandHandler('blockbots', blockbots_command),
        ChatMemberHandler(handle_bot_add, ChatMemberHandler.CHAT_MEMBER),
    ]