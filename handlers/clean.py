from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.helpers import is_admin
from database import get_session, get_chat

SERVICE_TYPES = ['join', 'leave', 'pin', 'photo', 'title', 'videochat', 'other']
COMMAND_TYPES = ['admin', 'user', 'other']

async def cleanservice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        session = get_session()
        try:
            chat = get_chat(session, update.effective_chat.id)
            status = "enabled" if chat.clean_service_enabled else "disabled"
            await update.message.reply_text(f"Clean service is {status}")
        finally:
            session.close()
        return
    
    setting = context.args[0].lower()
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        
        if setting in ['on', 'yes', 'true', 'all']:
            chat.clean_service_enabled = True
            chat.clean_service_types = 'all'
            await update.message.reply_text("✅ Will clean all service messages")
        elif setting in ['off', 'no', 'false']:
            chat.clean_service_enabled = False
            await update.message.reply_text("✅ Stopped cleaning service messages")
        elif setting in SERVICE_TYPES:
            current = chat.clean_service_types.split(',') if chat.clean_service_types else []
            if setting not in current:
                current.append(setting)
                chat.clean_service_types = ','.join(current)
                chat.clean_service_enabled = True
                await update.message.reply_text(f"✅ Will clean {setting} messages")
        session.commit()
    finally:
        session.close()

async def cleancommand_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        session = get_session()
        try:
            chat = get_chat(session, update.effective_chat.id)
            status = "enabled" if chat.clean_command_enabled else "disabled"
            await update.message.reply_text(f"Clean command is {status}")
        finally:
            session.close()
        return
    
    setting = context.args[0].lower()
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        
        if setting in ['on', 'yes', 'true', 'all']:
            chat.clean_command_enabled = True
            chat.clean_command_types = 'all'
            await update.message.reply_text("✅ Will clean all commands")
        elif setting in ['off', 'no', 'false']:
            chat.clean_command_enabled = False
            await update.message.reply_text("✅ Stopped cleaning commands")
        elif setting in COMMAND_TYPES:
            current = chat.clean_command_types.split(',') if chat.clean_command_types else []
            if setting not in current:
                current.append(setting)
                chat.clean_command_types = ','.join(current)
                chat.clean_command_enabled = True
                await update.message.reply_text(f"✅ Will clean {setting} commands")
        session.commit()
    finally:
        session.close()

def get_handlers():
    return [
        CommandHandler('cleanservice', cleanservice_command),
        CommandHandler('cleancommand', cleancommand_command),
    ]
