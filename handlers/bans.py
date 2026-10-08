from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, CommandHandler
from utils.helpers import is_admin, extract_time

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message to ban the user.")
        return
    
    user = update.message.reply_to_message.from_user
    reason = ' '.join(context.args) if context.args else "No reason given"
    
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"🔨 Banned {user.first_name}!\nReason: {reason}")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /unban user_id")
        return
    
    try:
        user_id = int(context.args[0])
        await context.bot.unban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text("✅ User unbanned!")
    except:
        await update.message.reply_text("❌ Failed to unban. Use user ID.")

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message to kick the user.")
        return
    
    user = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"👢 Kicked {user.first_name}!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message to mute the user.")
        return
    
    user = update.message.reply_to_message.from_user
    permissions = ChatPermissions(can_send_messages=False)
    
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, user.id, permissions)
        await update.message.reply_text(f"🔇 Muted {user.first_name}!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message to unmute the user.")
        return
    
    user = update.message.reply_to_message.from_user
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_send_other_messages=True
    )
    
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, user.id, permissions)
        await update.message.reply_text(f"🔊 Unmuted {user.first_name}!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

def get_handlers():
    return [
        CommandHandler('ban', ban_command),
        CommandHandler('unban', unban_command),
        CommandHandler('kick', kick_command),
        CommandHandler('mute', mute_command),
        CommandHandler('unmute', unmute_command),
    ]
