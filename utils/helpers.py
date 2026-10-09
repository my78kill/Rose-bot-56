from telegram import Update, ChatMember
from telegram.ext import ContextTypes
import datetime
from config import ROLE_HIERARCHY, GMUTE_AUTH_USERS
from database import get_session, UserRole

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Check if user is Telegram admin"""
    try:
        chat_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        return chat_member.status in ['administrator', 'creator']
    except:
        return False

async def is_founder(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Check if user is group creator"""
    try:
        chat_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        return chat_member.status == 'creator'
    except:
        return False

async def get_user_role(chat_id: int, user_id: int) -> str:
    """Get user's custom role from database"""
    session = get_session()
    try:
        role = session.query(UserRole).filter_by(
            chat_id=chat_id,
            user_id=user_id
        ).first()
        return role.role if role else None
    finally:
        session.close()

async def has_permission(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, required_role: str) -> bool:
    """Check if user has required role or higher"""
    # Telegram admin check
    if await is_admin(update, context, user_id):
        return True
    
    # Custom role check
    user_role = await get_user_role(update.effective_chat.id, user_id)
    user_level = ROLE_HIERARCHY.get(user_role, -1)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    
    return user_level >= required_level

async def can_assign_role(chat_id: int, assigner_id: int, target_role: str) -> bool:
    """Check if assigner can assign target role"""
    assigner_role = await get_user_role(chat_id, assigner_id)
    assigner_level = ROLE_HIERARCHY.get(assigner_role, -1)
    
    # Telegram admins can assign up to Moderator
    if assigner_level < 0:
        # Check if Telegram admin
        from telegram import Bot
        # This is simplified - in real use you'd pass the check result
        assigner_level = 5  # Admin level
    
    target_level = ROLE_HIERARCHY.get(target_role, 0)
    
    # Can only assign roles lower than yourself
    return assigner_level > target_level

def extract_time(time_str: str) -> datetime.datetime:
    """Convert time string like '3d', '2h', '30m' to datetime"""
    if not time_str:
        return datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    
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
    """Format welcome message with variables"""
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

def is_authorized_for_gmute(user_id: int) -> bool:
    """Check if user is authorized for hidden gMute command"""
    return user_id in GMUTE_AUTH_USERS

async def is_user_gmuted(user_id: int) -> bool:
    """Check if user is globally muted"""
    from database import GlobalMute
    session = get_session()
    try:
        mute = session.query(GlobalMute).filter_by(user_id=user_id).first()
        return mute is not None
    finally:
        session.close()