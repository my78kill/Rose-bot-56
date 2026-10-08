from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ChatMemberHandler
from utils.helpers import is_admin, format_welcome
from database import get_session, get_chat

async def setwelcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    welcome_text = ' '.join(context.args)
    if not welcome_text:
        await update.message.reply_text("⚠️ Usage: /setwelcome Welcome {first}!")
        return
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        chat.welcome_message = welcome_text
        session.commit()
        await update.message.reply_text("✅ Welcome message set!")
    finally:
        session.close()

async def welcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle welcome on/off"""
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        session = get_session()
        try:
            chat = get_chat(session, update.effective_chat.id)
            status = "enabled" if chat.welcome_enabled else "disabled"
            await update.message.reply_text(f"Welcome is currently {status}")
        finally:
            session.close()
        return
    
    setting = context.args[0].lower()
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        if setting in ['on', 'yes', 'true']:
            chat.welcome_enabled = True
            await update.message.reply_text("✅ Welcome messages enabled!")
        elif setting in ['off', 'no', 'false']:
            chat.welcome_enabled = False
            await update.message.reply_text("✅ Welcome messages disabled!")
        session.commit()
    finally:
        session.close()

async def resetwelcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        chat.welcome_message = "Welcome {first}!"
        session.commit()
        await update.message.reply_text("✅ Welcome message reset to default")
    finally:
        session.close()

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new members joining"""
    if not update.chat_member:
        return
    
    new_status = update.chat_member.new_chat_member.status
    old_status = update.chat_member.old_chat_member.status
    
    # Only trigger when user joins (was not member before)
    if old_status in ['left', 'kicked'] and new_status == 'member':
        user = update.chat_member.new_chat_member.user
        chat = update.chat_member.chat
        
        session = get_session()
        try:
            chat_db = get_chat(session, chat.id)
            
            if chat_db.welcome_enabled and chat_db.welcome_message:
                welcome_text = format_welcome(chat_db.welcome_message, user, chat)
                await context.bot.send_message(chat.id, welcome_text, parse_mode='HTML')
        finally:
            session.close()

def get_handlers():
    return [
        CommandHandler('setwelcome', setwelcome_command),
        CommandHandler('welcome', welcome_command),
        CommandHandler('resetwelcome', resetwelcome_command),
        ChatMemberHandler(handle_new_member, ChatMemberHandler.CHAT_MEMBER),
    ]
