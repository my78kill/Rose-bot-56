from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from utils.buttons import help_menu_buttons, back_button, coming_soon_buttons

HELP_TEXTS = {
    'admin': """<b>Admin Commands:</b>

/promote @user - Promote user to admin
/demote @user - Remove admin status
/adminlist - Show current admins
/admincache - Refresh admin cache""",

    'bans': """<b>Ban/Mute/Kick Commands:</b>

/ban @user [reason] - Ban user permanently
/unban @user - Unban user
/tban @user 3d - Temp ban (m/h/d/w)
/kick @user - Kick user (can rejoin)
/mute @user - Mute user permanently
/unmute @user - Unmute user
/tmute @user 2h - Temp mute""",

    'warnings': """<b>Warning Commands:</b>

/warn @user [reason] - Issue warning
/swarn @user - Silent warn
/dwarn @user - Warn + delete message
/rmwarn @user - Remove last warning
/resetwarn @user - Clear all warnings
/warns @user - Check warning history
/setwarnlimit 3 - Warnings before punishment
/setwarnmode ban/kick/mute - Set punishment""",

    'locks': """<b>Lock Commands:</b>

/lock url/invitelink/forward - Block message types
/unlock url/invitelink/forward - Remove lock
/locks - Show active locks
/locktypes - List all lockable types

Lock Types: url, invitelink, forward, sticker, photo, video, gif, audio, document, voice, poll, contact, command, emoji, phone, email, all""",

    'approvals': """<b>Approval Commands:</b>

/approve @user [reason] - Approve user (immune to auto-actions)
/approval @user - Check if user is approved
/approved - List all approved users
/unapprove @user - Remove approval""",

    'antiraid': """<b>AntiRaid Commands:</b>

/antiraid - Check antiraid status
/antiraid on - Enable antiraid
/antiraid 3h - Enable for custom duration
/antiraid off - Disable antiraid
/raidtime 6h - Set antiraid duration
/raidactiontime 1h - Set ban duration for raiders""",

    'greetings': """<b>Greeting Commands:</b>

/welcome on/off - Toggle welcome messages
/setwelcome text - Set welcome message
/resetwelcome - Reset to default
/goodbye on/off - Toggle goodbye messages
/setgoodbye text - Set goodbye message

Variables: {first}, {last}, {fullname}, {username}, {mention}, {id}, {chatname}""",

    'captcha': """<b>CAPTCHA Commands:</b>

/captcha on/off - Enable CAPTCHA
/captchamode button/math/text/text2 - Set difficulty
/captchakick on/off - Kick if fail CAPTCHA
/captchakicktime 1h - Time to solve (5m-24h)""",

    'filters': """<b>Filter Commands:</b>

/filter "word" reply - Add auto-reply filter
/stop "word" - Remove filter
/stopall - Remove all filters
/filters - List active filters""",

    'blocklists': """<b>Blocklist Commands:</b>

/addblocklist "word" reason - Add blocked word
/blocklist - Show blocked words
/rmblocklist "word" - Remove from blocklist
/rmblocklistall - Clear all blocklists
/blocklistmode ban/kick/mute - Set action""",

    'antiflood': """<b>AntiFlood Commands:</b>

/setflood 5 - Messages to trigger flood
/setfloodmode kick/ban/mute - Punishment
/flood - Show flood settings""",

    'clean_command': """<b>Clean Command:</b>

/cleancommand all - Delete all command messages
/cleancommand admin user - Delete specific types
/keepcommand all - Stop deleting commands""",

    'clean_service': """<b>Clean Service:</b>

/cleanservice on/off - Delete service messages
/cleanservice join leave pin - Delete specific types""",

    'disabling': """<b>Disabling Commands:</b>

/disabled - List disabled commands
/disable kickme - Disable a command
/enable kickme - Re-enable a command""",

    'log_channels': """<b>Log Channel Commands:</b>

/setlog - In channel, then forward to group
/unsetlog - Stop logging this group
/logchannel - Show current log channel""",

    'pins': """<b>Pin Commands:</b>

/pin (reply) - Pin message silently
/pin loud (reply) - Pin with notification
/permapin message - Pin new message
/unpin (reply) - Unpin specific message
/unpinall - Unpin all messages""",

    'reports': """<b>Reports Commands:</b>

/reports on/off - Toggle reports
/report (reply) - Report message to admins
@admin (reply) - Alternative report command""",

    'languages': """<b>Language Commands:</b>

/lang - Show current language
/lang en - Set language""",

    'privacy': """<b>Privacy Commands:</b>

/privacy - View and delete your data (PM only)""",

    'formatting': """<b>Formatting Options:</b>

Markdown: *bold*, _italic_, [link](url), `code`
HTML: <b>bold</b>, <i>italic</i>, <code>code</code>
Variables: {first}, {last}, {username}, {mention}, {chatname}""",
}

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != 'private':
        await update.message.reply_text(
            f"👋 Contact me in PM to access the help menu!\n\nClick here: @{context.bot.username}"
        )
        return
    
    await update.message.reply_text(
        "<b>🌹 Rose Bot Help Menu</b>\n\nClick on any module below to see its commands:",
        reply_markup=help_menu_buttons(),
        parse_mode='HTML'
    )

async def help_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'help_back':
        await query.edit_message_text(
            "<b>🌹 Rose Bot Help Menu</b>\n\nClick on any module below to see its commands:",
            reply_markup=help_menu_buttons(),
            parse_mode='HTML'
        )
    elif data.startswith('coming_soon_'):
        feature = data.replace('coming_soon_', '').replace('_', ' ').title()
        await query.edit_message_text(
            f"⏳ <b>{feature}</b>\n\nThis feature is coming soon! Stay tuned for updates.",
            reply_markup=coming_soon_buttons(),
            parse_mode='HTML'
        )
    elif data.startswith('help_'):
        module = data.replace('help_', '')
        help_text = HELP_TEXTS.get(module, "Help text not found.")
        await query.edit_message_text(
            help_text,
            reply_markup=back_button(),
            parse_mode='HTML'
        )

def get_handlers():
    return [
        CommandHandler('help', help_command),
        CallbackQueryHandler(help_button_callback, pattern='^help_'),
        CallbackQueryHandler(help_button_callback, pattern='^coming_soon_')
    ]
