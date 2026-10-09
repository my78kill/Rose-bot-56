from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, CommandHandler
from utils.helpers import has_permission, extract_time, is_user_gmuted

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban user permanently"""
    if not await has_permission(update, context, update.effective_user.id, 'moderator'):
        await update.message.reply_text("⚠️ You need Moderator role or higher!")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message to ban the user.")
        return
    
    user = update.message.reply_to_message.from_user
    reason = ' '.join(context.args) if context.args else "No reason given"
    
    # Check if user is globally muted (gmutted users can't be banned by non-admins)
    if await is_user_gmuted(user.id):
        if not await has_permission(update, context, update.effective_user.id, 'admin'):
            await update.message.reply_text("🔇 This user is protected.")
            return
    
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"🔨 Banned {user.first_name}!\nReason: {reason}")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to ban: {str(e)}")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban user"""
    if not await has_permission(update, context, update.effective_user.id, 'moderator'):
        await update.message.reply_text("⚠️ You need Moderator role or higher!")
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

async def tban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Temp ban user"""
    if not await has_permission(update, context, update.effective_user.id, 'moderator'):
        await update.message.reply_text("⚠️ You need Moderator role or higher!")
        return
    
    if not update.message.reply_to_message or len(context.args) < 1:
        await update.message.reply_text("⚠️ Usage: /tban 3d (reply to user)")
        return
    
    user = update.message.reply_to_message.from_user
    time_str = context.args[0]
    until_date = extract_time(time_str)
    
    try:
        await context.bot.ban_chat_member(
            update.effective_chat.id, 
            user.id,
            until_date=until_date
        )
        await update.message.reply_text(f"🔨 Temporarily banned {user.first_name} for {time_str}!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kick user"""
    if not await has_permission(update, context, update.effective_user.id, 'moderator'):
        await update.message.reply_text("⚠️ You need Moderator role or higher!")
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
    """Mute user permanently"""
    if not await has_permission(update, context, update.effective_user.id, 'muter'):
        await update.message.reply_text("⚠️ You need Muter role or higher!")
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
    """Unmute user"""
    if not await has_permission(update, context, update.effective_user.id, 'muter'):
        await update.message.reply_text("⚠️ You need Muter role or higher!")
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

async def tmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Temp mute user"""
    if not await has_permission(update, context, update.effective_user.id, 'muter'):
        await update.message.reply_text("⚠️ You need Muter role or higher!")
        return
    
    if not update.message.reply_to_message or len(context.args) < 1:
        await update.message.reply_text("⚠️ Usage: /tmute 2h (reply to user)")
        return
    
    user = update.message.reply_to_message.from_user
    time_str = context.args[0]
    until_date = extract_time(time_str)
    permissions = ChatPermissions(can_send_messages=False)
    
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, 
            user.id, 
            permissions,
            until_date=until_date
        )
        await update.message.reply_text(f"🔇 Temporarily muted {user.first_name} for {time_str}!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

async def sbankick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kick and ban spam account"""
    if not await has_permission(update, context, update.effective_user.id, 'moderator'):
        await update.message.reply_text("⚠️ You need Moderator role or higher!")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a spam message.")
        return
    
    user = update.message.reply_to_message.from_user
    
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"🔨🦶 Spam account {user.first_name} kicked and banned!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

def get_handlers():
    return [
        CommandHandler('ban', ban_command),
        CommandHandler('unban', unban_command),
        CommandHandler('tban', tban_command),
        CommandHandler('kick', kick_command),
        CommandHandler('mute', mute_command),
        CommandHandler('unmute', unmute_command),
        CommandHandler('tmute', tmute_command),
        CommandHandler('sbankick', sbankick_command),
    ]