from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ChatMemberHandler
from utils.helpers import is_admin, extract_time
from database import get_session, get_chat
import datetime
import time

# Track joins for auto-antiraid
join_tracker = {}

async def antiraid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        
        if not context.args:
            status = "enabled" if chat.antiraid_enabled else "disabled"
            await update.message.reply_text(f"Antiraid is currently {status}")
            return
        
        setting = context.args[0].lower()
        
        if setting in ['on', 'yes', 'true']:
            chat.antiraid_enabled = True
            session.commit()
            await update.message.reply_text(
                f"🛡️ Antiraid enabled for {chat.antiraid_time} hours!\n"
                f"New members will be temporarily banned for {chat.antiraid_action_time} hours."
            )
        elif setting in ['off', 'no', 'false']:
            chat.antiraid_enabled = False
            session.commit()
            await update.message.reply_text("🛡️ Antiraid disabled")
        elif setting.endswith('h'):
            # Custom duration
            hours = int(setting[:-1])
            chat.antiraid_enabled = True
            chat.antiraid_time = hours
            session.commit()
            await update.message.reply_text(f"🛡️ Antiraid enabled for {hours} hours!")
    finally:
        session.close()

async def raidtime_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /raidtime 6h")
        return
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        time_str = context.args[0]
        if time_str.endswith('h'):
            chat.antiraid_time = int(time_str[:-1])
            session.commit()
            await update.message.reply_text(f"✅ Raid time set to {chat.antiraid_time} hours")
    finally:
        session.close()

async def raidactiontime_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /raidactiontime 1h")
        return
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        time_str = context.args[0]
        if time_str.endswith('h'):
            chat.antiraid_action_time = int(time_str[:-1])
            session.commit()
            await update.message.reply_text(f"✅ Raid action time set to {chat.antiraid_action_time} hours")
    finally:
        session.close()

async def autoantiraid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /autoantiraid 10 (or off)")
        return
    
    setting = context.args[0].lower()
    
    session = get_session()
    try:
        chat = get_chat(session, update.effective_chat.id)
        if setting == 'off':
            chat.autoantiraid = 0
            await update.message.reply_text("✅ Auto-antiraid disabled")
        else:
            chat.autoantiraid = int(setting)
            await update.message.reply_text(f"✅ Auto-antiraid set to {setting} joins/minute")
        session.commit()
    finally:
        session.close()

async def handle_new_member_antiraid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if should trigger antiraid"""
    if not update.chat_member:
        return
    
    new_status = update.chat_member.new_chat_member.status
    old_status = update.chat_member.old_chat_member.status
    
    if old_status in ['left', 'kicked'] and new_status == 'member':
        chat_id = update.chat_member.chat.id
        user_id = update.chat_member.new_chat_member.user.id
        
        session = get_session()
        try:
            chat = get_chat(session, chat_id)
            
            # Check if antiraid enabled
            if chat.antiraid_enabled:
                # Temp ban the user
                until = datetime.datetime.utcnow() + datetime.timedelta(hours=chat.antiraid_action_time)
                await context.bot.ban_chat_member(chat_id, user_id, until_date=until)
                return
            
            # Check autoantiraid
            if chat.autoantiraid > 0:
                now = time.time()
                key = f"joins:{chat_id}"
                
                if key not in join_tracker:
                    join_tracker[key] = []
                
                join_tracker[key].append(now)
                join_tracker[key] = [t for t in join_tracker[key] if now - t < 60]
                
                if len(join_tracker[key]) >= chat.autoantiraid:
                    # Trigger antiraid
                    chat.antiraid_enabled = True
                    session.commit()
                    await context.bot.send_message(
                        chat_id,
                        f"🚨 Auto-antiraid triggered! {chat.autoantiraid} joins in 1 minute.\n"
                        f"New members will be temporarily banned."
                    )
        finally:
            session.close()

def get_handlers():
    return [
        CommandHandler('antiraid', antiraid_command),
        CommandHandler('raidtime', raidtime_command),
        CommandHandler('raidactiontime', raidactiontime_command),
        CommandHandler('autoantiraid', autoantiraid_command),
        ChatMemberHandler(handle_new_member_antiraid, ChatMemberHandler.CHAT_MEMBER),
    ]
