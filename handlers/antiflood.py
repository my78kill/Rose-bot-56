from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from utils.helpers import is_admin
from database import get_session, get_chat
import time

# Store message counts temporarily
flood_dict = {}

async def check_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user is flooding"""
    if not update.message or update.effective_chat.type == 'private':
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Skip admins
    if await is_admin(update, context, user_id):
        return
    
    session = get_session()
    try:
        chat = get_chat(session, chat_id)
        
        if not hasattr(chat, 'antiflood_limit'):
            return
        
        key = f"{chat_id}:{user_id}"
        now = time.time()
        
        if key not in flood_dict:
            flood_dict[key] = []
        
        # Add current message time
        flood_dict[key].append(now)
        
        # Remove old messages outside time window
        flood_dict[key] = [t for t in flood_dict[key] if now - t < 60]
        
        # Check if exceeded limit
        if len(flood_dict[key]) > chat.antiflood_limit:
            # Punish user
            if chat.antiflood_mode == 'ban':
                await context.bot.ban_chat_member(chat_id, user_id)
                await update.message.reply_text("🔨 Flooder banned!")
            elif chat.antiflood_mode == 'mute':
                from telegram import ChatPermissions
                await context.bot.restrict_chat_member(
                    chat_id, user_id, ChatPermissions(can_send_messages=False)
                )
                await update.message.reply_text("🔇 Flooder muted!")
            elif chat.antiflood_mode == 'kick':
                await context.bot.ban_chat_member(chat_id, user_id)
                await context.bot.unban_chat_member(chat_id, user_id)
                await update.message.reply_text("👢 Flooder kicked!")
            
            # Clear their flood count
            flood_dict[key] = []
    finally:
        session.close()

async def setflood_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /setflood 5")
        return
    
    limit = int(context.args[0])
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        chat.antiflood_limit = limit
        session.commit()
        await update.message.reply_text(f"✅ Antiflood limit set to {limit} messages per minute")
    finally:
        session.close()

async def setfloodmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /setfloodmode ban/kick/mute")
        return
    
    mode = context.args[0].lower()
    if mode not in ['ban', 'kick', 'mute']:
        await update.message.reply_text("⚠️ Mode must be: ban, kick, or mute")
        return
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        chat.antiflood_mode = mode
        session.commit()
        await update.message.reply_text(f"✅ Antiflood mode set to {mode}")
    finally:
        session.close()

async def flood_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        await update.message.reply_text(
            f"📊 Antiflood Settings:\n"
            f"Limit: {chat.antiflood_limit} messages/minute\n"
            f"Mode: {chat.antiflood_mode}"
        )
    finally:
        session.close()

def get_handlers():
    return [
        CommandHandler('setflood', setflood_command),
        CommandHandler('setfloodmode', setfloodmode_command),
        CommandHandler('flood', flood_command),
        MessageHandler(filters.TEXT & ~filters.COMMAND, check_flood),
    ]
