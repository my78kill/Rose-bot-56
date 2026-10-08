from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.helpers import is_admin
from database import get_session, get_chat, ApprovedUser

async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a user to approve them")
        return
    
    user = update.message.reply_to_message.from_user
    reason = ' '.join(context.args) if context.args else "No reason"
    
    session = get_session()
    try:
        # Check if already approved
        existing = session.query(ApprovedUser).filter_by(
            chat_id=update.effective_chat.id,
            user_id=user.id
        ).first()
        
        if existing:
            await update.message.reply_text(f"ℹ️ {user.first_name} is already approved")
            return
        
        approval = ApprovedUser(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            reason=reason,
            approved_by=update.effective_user.id
        )
        session.add(approval)
        session.commit()
        await update.message.reply_text(f"✅ Approved {user.first_name}")
    finally:
        session.close()

async def unapprove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, update.effective_user.id):
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a user to unapprove them")
        return
    
    user = update.message.reply_to_message.from_user
    
    session = get_session()
    try:
        approval = session.query(ApprovedUser).filter_by(
            chat_id=update.effective_chat.id,
            user_id=user.id
        ).first()
        
        if approval:
            session.delete(approval)
            session.commit()
            await update.message.reply_text(f"✅ Unapproved {user.first_name}")
        else:
            await update.message.reply_text(f"ℹ️ {user.first_name} was not approved")
    finally:
        session.close()

async def approved_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    try:
        approvals = session.query(ApprovedUser).filter_by(
            chat_id=update.effective_chat.id
        ).all()
        
        if not approvals:
            await update.message.reply_text("ℹ️ No approved users")
            return
        
        text = "✅ <b>Approved Users:</b>\n\n"
        for app in approvals:
            try:
                user = await context.bot.get_chat(app.user_id)
                text += f"• {user.first_name}\n"
            except:
                text += f"• User ID: {app.user_id}\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
    finally:
        session.close()

def get_handlers():
    return [
        CommandHandler('approve', approve_command),
        CommandHandler('unapprove', unapprove_command),
        CommandHandler('approved', approved_command),
    ]
