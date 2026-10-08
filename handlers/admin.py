from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.helpers import is_admin

async def promote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        await update.message.reply_text("⚠️ You need to be an admin to use this command.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message to promote the user.")
        return
    
    user = update.message.reply_to_message.from_user
    
    try:
        await context.bot.promote_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            can_delete_messages=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_invite_users=True
        )
        await update.message.reply_text(f"✅ Promoted {user.first_name}!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to promote: {str(e)}")

async def demote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message to demote the user.")
        return
    
    user = update.message.reply_to_message.from_user
    
    try:
        await context.bot.promote_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            can_delete_messages=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_invite_users=False
        )
        await update.message.reply_text(f"✅ Demoted {user.first_name}!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

async def adminlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        admin_text = "<b>👮 Admins:</b>\n\n"
        for admin in admins:
            user = admin.user
            admin_text += f"• {user.first_name}\n"
        await update.message.reply_text(admin_text, parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def get_handlers():
    return [
        CommandHandler('promote', promote_command),
        CommandHandler('demote', demote_command),
        CommandHandler('adminlist', adminlist_command),
    ]
