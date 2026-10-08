from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.helpers import is_admin

async def pin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message to pin it")
        return
    
    loud = len(context.args) > 0 and context.args[0].lower() == 'loud'
    
    try:
        await update.message.reply_to_message.pin(
            disable_notification=not loud
        )
        
        if loud:
            await update.message.reply_text("📌 Pinned loudly!")
        else:
            await update.message.delete()  # Silent pin - delete command
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

async def unpin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    try:
        if update.message.reply_to_message:
            await update.message.reply_to_message.unpin()
            await update.message.reply_text("📌 Unpinned message")
        else:
            await context.bot.unpin_all_chat_messages(update.effective_chat.id)
            await update.message.reply_text("📌 Unpinned all messages")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

async def permapin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /permapin message text")
        return
    
    text = ' '.join(context.args)
    
    try:
        msg = await context.bot.send_message(update.effective_chat.id, text)
        await msg.pin(disable_notification=True)
        await update.message.delete()
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

def get_handlers():
    return [
        CommandHandler('pin', pin_command),
        CommandHandler('unpin', unpin_command),
        CommandHandler('permapin', permapin_command),
    ]
