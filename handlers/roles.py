from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.helpers import is_admin, has_permission, get_user_role
from database import get_session, UserRole
from config import ROLE_EMOJIS, ROLE_HIERARCHY

async def mod_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Assign moderator role"""
    if not await has_permission(update, context, update.effective_user.id, 'admin'):
        await update.message.reply_text("⚠️ Only Admins+ can assign Moderator role!")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a user to make them Moderator")
        return
    
    user = update.message.reply_to_message.from_user
    
    session = get_session()
    try:
        # Remove existing role
        session.query(UserRole).filter_by(
            chat_id=update.effective_chat.id,
            user_id=user.id
        ).delete()
        
        # Add new role
        role = UserRole(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            role='moderator',
            assigned_by=update.effective_user.id
        )
        session.add(role)
        session.commit()
        
        await update.message.reply_text(f"✅ {user.first_name} is now {ROLE_EMOJIS['moderator']} Moderator!")
    finally:
        session.close()

async def muter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Assign muter role"""
    if not await has_permission(update, context, update.effective_user.id, 'admin'):
        await update.message.reply_text("⚠️ Only Admins+ can assign Muter role!")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a user to make them Muter")
        return
    
    user = update.message.reply_to_message.from_user
    
    session = get_session()
    try:
        session.query(UserRole).filter_by(
            chat_id=update.effective_chat.id,
            user_id=user.id
        ).delete()
        
        role = UserRole(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            role='muter',
            assigned_by=update.effective_user.id
        )
        session.add(role)
        session.commit()
        
        await update.message.reply_text(f"✅ {user.first_name} is now {ROLE_EMOJIS['muter']} Muter!")
    finally:
        session.close()

async def cleaner_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Assign cleaner role"""
    if not await has_permission(update, context, update.effective_user.id, 'admin'):
        await update.message.reply_text("⚠️ Only Admins+ can assign Cleaner role!")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a user to make them Cleaner")
        return
    
    user = update.message.reply_to_message.from_user
    
    session = get_session()
    try:
        session.query(UserRole).filter_by(
            chat_id=update.effective_chat.id,
            user_id=user.id
        ).delete()
        
        role = UserRole(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            role='cleaner',
            assigned_by=update.effective_user.id
        )
        session.add(role)
        session.commit()
        
        await update.message.reply_text(f"✅ {user.first_name} is now {ROLE_EMOJIS['cleaner']} Chat Cleaner!")
    finally:
        session.close()

async def helper_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Assign helper role"""
    if not await has_permission(update, context, update.effective_user.id, 'admin'):
        await update.message.reply_text("⚠️ Only Admins+ can assign Helper role!")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a user to make them Helper")
        return
    
    user = update.message.reply_to_message.from_user
    
    session = get_session()
    try:
        session.query(UserRole).filter_by(
            chat_id=update.effective_chat.id,
            user_id=user.id
        ).delete()
        
        role = UserRole(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            role='helper',
            assigned_by=update.effective_user.id
        )
        session.add(role)
        session.commit()
        
        await update.message.reply_text(f"✅ {user.first_name} is now {ROLE_EMOJIS['helper']} Helper!")
    finally:
        session.close()

async def free_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Assign free role (immune to punishments)"""
    if not await has_permission(update, context, update.effective_user.id, 'admin'):
        await update.message.reply_text("⚠️ Only Admins+ can assign Free role!")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a user to make them Free")
        return
    
    user = update.message.reply_to_message.from_user
    
    session = get_session()
    try:
        session.query(UserRole).filter_by(
            chat_id=update.effective_chat.id,
            user_id=user.id
        ).delete()
        
        role = UserRole(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            role='free',
            assigned_by=update.effective_user.id
        )
        session.add(role)
        session.commit()
        
        await update.message.reply_text(f"✅ {user.first_name} is now {ROLE_EMOJIS['free']} Free (immune to punishments)!")
    finally:
        session.close()

async def unmod_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove custom role"""
    if not await has_permission(update, context, update.effective_user.id, 'admin'):
        await update.message.reply_text("⚠️ Only Admins+ can remove roles!")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a user to remove their role")
        return
    
    user = update.message.reply_to_message.from_user
    
    session = get_session()
    try:
        session.query(UserRole).filter_by(
            chat_id=update.effective_chat.id,
            user_id=user.id
        ).delete()
        session.commit()
        
        await update.message.reply_text(f"✅ Removed custom role from {user.first_name}")
    finally:
        session.close()

async def staff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all staff members"""
    session = get_session()
    try:
        roles = session.query(UserRole).filter_by(
            chat_id=update.effective_chat.id
        ).all()
        
        if not roles:
            await update.message.reply_text("ℹ️ No custom roles assigned")
            return
        
        # Group by role
        staff_by_role = {}
        for role in roles:
            if role.role not in staff_by_role:
                staff_by_role[role.role] = []
            staff_by_role[role.role].append(role.user_id)
        
        text = "👥 <b>Staff Members:</b>\n\n"
        
        for role_name, level in sorted(ROLE_HIERARCHY.items(), key=lambda x: x[1], reverse=True):
            if role_name in staff_by_role:
                emoji = ROLE_EMOJIS.get(role_name, '')
                text += f"<b>{emoji} {role_name.title()}s:</b>\n"
                for user_id in staff_by_role[role_name]:
                    try:
                        user = await context.bot.get_chat(user_id)
                        text += f"• {user.first_name}\n"
                    except:
                        text += f"• User {user_id}\n"
                text += "\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
    finally:
        session.close()

def get_handlers():
    return [
        CommandHandler('mod', mod_command),
        CommandHandler('muter', muter_command),
        CommandHandler('cleaner', cleaner_command),
        CommandHandler('helper', helper_command),
        CommandHandler('free', free_command),
        CommandHandler('unmod', unmod_command),
        CommandHandler('staff', staff_command),
    ]