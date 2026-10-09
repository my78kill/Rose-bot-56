from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.helpers import is_admin, has_permission

# Store purge range temporarily
purge_ranges = {}

async def del_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete single message (reply to it)"""
    if not await has_permission(update, context, update.effective_user.id, 'cleaner'):
        await update.message.reply_text("⚠️ You need Cleaner role or higher!")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message to delete it")
        return
    
    try:
        await update.message.reply_to_message.delete()
        await update.message.delete()
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

async def purge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Purge messages from reply to current"""
    if not await has_permission(update, context, update.effective_user.id, 'cleaner'):
        await update.message.reply_text("⚠️ You need Cleaner role or higher!")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message to purge from there")
        return
    
    start_msg = update.message.reply_to_message.message_id
    end_msg = update.message.message_id
    
    try:
        # Delete in batches (Telegram limit)
        for msg_id in range(start_msg, end_msg + 1):
            try:
                await context.bot.delete_message(update.effective_chat.id, msg_id)
            except:
                pass
        
        await update.message.reply_text(f"🗑️ Purged {end_msg - start_msg + 1} messages")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

async def spurge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Silent purge (no confirmation)"""
    if not await has_permission(update, context, update.effective_user.id, 'cleaner'):
        return
    
    if not update.message.reply_to_message:
        return
    
    start_msg = update.message.reply_to_message.message_id
    end_msg = update.message.message_id
    
    try:
        for msg_id in range(start_msg, end_msg + 1):
            try:
                await context.bot.delete_message(update.effective_chat.id, msg_id)
            except:
                pass
    except:
        pass

async def purgefrom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark start of purge range"""
    if not await has_permission(update, context, update.effective_user.id, 'cleaner'):
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message to mark purge start")
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if chat_id not in purge_ranges:
        purge_ranges[chat_id] = {}
    
    purge_ranges[chat_id][user_id] = {
        'start': update.message.reply_to_message.message_id
    }
    
    await update.message.reply_text("✅ Purge start marked. Now reply to end message with /purgeto")

async def purgeto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark end and execute purge"""
    if not await has_permission(update, context, update.effective_user.id, 'cleaner'):
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message to mark purge end")
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if chat_id not in purge_ranges or user_id not in purge_ranges[chat_id]:
        await update.message.reply_text("⚠️ Use /purgefrom first!")
        return
    
    start_msg = purge_ranges[chat_id][user_id]['start']
    end_msg = update.message.reply_to_message.message_id
    
    try:
        for msg_id in range(start_msg, end_msg + 1):
            try:
                await context.bot.delete_message(chat_id, msg_id)
            except:
                pass
        
        count = abs(end_msg - start_msg) + 1
        await update.message.reply_text(f"🗑️ Purged {count} messages")
        
        # Clear range
        del purge_ranges[chat_id][user_id]
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

def get_handlers():
    return [
        CommandHandler('del', del_command),
        CommandHandler('purge', purge_command),
        CommandHandler('spurge', spurge_command),
        CommandHandler('purgefrom', purgefrom_command),
        CommandHandler('purgeto', purgeto_command),
    ]