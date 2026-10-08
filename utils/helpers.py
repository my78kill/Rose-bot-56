from telegram import Update
from telegram.ext import ContextTypes
import datetime

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        chat_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        return chat_member.status in ['administrator', 'creator']
    except:
        return False

async def is_bot_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
        return bot_member.status == 'administrator'
    except:
        return False

def extract_time(time_str: str) -> datetime.datetime:
    num = int(time_str[:-1])
    unit = time_str[-1].lower()
    
    if unit == 'm':
        delta = datetime.timedelta(minutes=num)
    elif unit == 'h':
        delta = datetime.timedelta(hours=num)
    elif unit == 'd':
        delta = datetime.timedelta(days=num)
    elif unit == 'w':
        delta = datetime.timedelta(weeks=num)
    else:
        delta = datetime.timedelta(hours=1)
    
    return datetime.datetime.utcnow() + delta

def format_welcome(text: str, user, chat) -> str:
    replacements = {
        '{first}': user.first_name or '',
        '{last}': user.last_name or '',
        '{fullname}': f"{user.first_name} {user.last_name or ''}".strip(),
        '{username}': f"@{user.username}" if user.username else user.first_name,
        '{mention}': user.mention_html(),
        '{id}': str(user.id),
        '{chatname}': chat.title or 'this chat',
    }
    
    for key, value in replacements.items():
        text = text.replace(key, value)
    
    return text
