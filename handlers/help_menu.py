from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from utils.buttons import help_menu_buttons, back_button, coming_soon_buttons

HELP_TEXTS = {
    'admin': """<b>👮 Admin Commands:</b>

/promote @user - Promote user to admin
/demote @user - Remove admin status
/adminlist - Show current admins
/admincache - Refresh admin cache
/anonadmin on/off - Allow anonymous admin commands
/adminerror on/off - Toggle permission error messages""",

    'bans': """<b>🔨 Ban/Mute/Kick Commands:</b>

/ban @user [reason] - Ban user permanently
/unban @user - Unban user
/tban @user 3d - Temp ban (m/h/d/w)
/kick @user - Kick user (can rejoin)
/mute @user - Mute user permanently
/unmute @user - Unmute user
/tmute @user 2h - Temp mute
/sbankick @user - Kick + ban spam account

<b>Roles:</b> Admin, Moderator, Muter can use these""",

    'warnings': """<b>⚠️ Warning Commands:</b>

/warn @user [reason] - Issue warning
/swarn @user - Silent warn
/dwarn @user - Warn + delete message
/rmwarn @user - Remove last warning
/resetwarn @user - Clear all warnings
/warns @user - Check warning history
/setwarnlimit 3 - Warnings before punishment
/setwarnmode ban/kick/mute - Set punishment

<b>Roles:</b> Admin, Moderator can use these""",

    'locks': """<b>🔒 Lock Commands:</b>

/lock url/invitelink/forward - Block message types
/unlock url/invitelink/forward - Remove lock
/locks - Show active locks
/locktypes - List all lockable types
/lockwarns on/off - Warn on lock violation
/allowlist domain.com - Whitelist URLs
/rmallowlist domain.com - Remove from whitelist

<b>Lock Types:</b> url, invitelink, forward, sticker, photo, video, gif, audio, document, voice, poll, contact, command, emoji, phone, email, cjk, cyrillic, rtl, zalgo, all

<b>Roles:</b> Admin only""",

    'approvals': """<b>✅ Approval Commands:</b>

/approve @user [reason] - Approve user (immune to auto-actions)
/approval @user - Check if user is approved
/approved - List all approved users
/unapprove @user - Remove approval

Approved users are immune to locks, antiflood, and blocklists.

<b>Roles:</b> Admin only""",

    'antiraid': """<b>🛡️ AntiRaid Commands:</b>

/antiraid - Check antiraid status
/antiraid on - Enable antiraid
/antiraid 3h - Enable for custom duration
/antiraid off - Disable antiraid
/raidtime 6h - Set antiraid duration
/raidactiontime 1h - Set ban duration for raiders
/autoantiraid 10 - Auto-enable if 10+ joins/min
/autoantiraid off - Disable auto antiraid

<b>Roles:</b> Admin only""",

    'greetings': """<b>👋 Greeting Commands:</b>

/welcome on/off - Toggle welcome messages
/setwelcome text - Set welcome message
/resetwelcome - Reset to default
/goodbye on/off - Toggle goodbye messages
/setgoodbye text - Set goodbye message

<b>Variables:</b> {first}, {last}, {fullname}, {username}, {mention}, {id}, {chatname}

<b>Roles:</b> Admin only""",

    'captcha': """<b>🤖 CAPTCHA Commands:</b>

/captcha on/off - Enable CAPTCHA
/captchamode button/math/text/text2 - Set difficulty
/captchakick on/off - Kick if fail CAPTCHA
/captchakicktime 1h - Time to solve (5m-24h)
/captcharules on/off - Require rules acceptance

<b>Modes:</b> button (easiest), math, text, text2 (hardest)

<b>Roles:</b> Admin only""",

    'filters': """<b>🔍 Filter Commands:</b>

/filter "word" reply - Add auto-reply filter
/stop "word" - Remove filter
/stopall - Remove all filters
/filters - List active filters

<b>Modifiers:</b>
prefix:word - Match start only
exact:word - Match whole message only
{replytag} - Reply to original recipient
{user} - Only non-admins trigger
{admin} - Only admins trigger

<b>Roles:</b> Admin only""",

    'blocklists': """<b>🚫 Blocklist Commands:</b>

/addblocklist "word" reason - Add blocked word
/blocklist - Show blocked words
/rmblocklist "word" - Remove from blocklist
/rmblocklistall - Clear all blocklists
/blocklistmode ban/kick/mute - Set action

Blocklists automatically delete messages containing blocked words.

<b>Roles:</b> Admin only""",

    'antiflood': """<b>🌊 AntiFlood Commands:</b>

/setflood 5 - Messages to trigger flood
/setfloodmode kick/ban/mute - Punishment
/flood - Show flood settings

<b>Roles:</b> Admin only""",

    'clean_command': """<b>🧹 Clean Command:</b>

/cleancommand all - Delete all command messages
/cleancommand admin user - Delete specific types
/keepcommand all - Stop deleting commands
/keepcommand admin - Stop deleting specific type
/cleancommandtypes - List available types

<b>Types:</b> all, admin, user, other

<b>Roles:</b> Admin only""",

    'clean_service': """<b>🧽 Clean Service:</b>

/cleanservice on/off - Delete service messages
/cleanservice join leave pin - Delete specific types
/nocleanservice join - Stop deleting specific type
/cleanservicetypes - List available types

<b>Types:</b> all, join, leave, pin, photo, title, videochat, other

<b>Roles:</b> Admin only""",

    'disabling': """<b>🚫 Disabling Commands:</b>

/disabled - List disabled commands
/disableable - List commands that can be disabled
/disable kickme - Disable a command
/enable kickme - Re-enable a command
/disabledel on/off - Delete disabled commands when sent
/disableadmin on/off - Apply disabled list to admins

<b>Roles:</b> Admin only""",

    'log_channels': """<b>📋 Log Channel Commands:</b>

/setlog - In channel, then forward to group
/unsetlog - Stop logging this group
/logchannel - Show current log channel
/logcategories - List log categories
/log admin user - Enable specific categories
/nolog settings - Disable specific categories

<b>Categories:</b> settings, admin, user, automated, reports, other

<b>Roles:</b> Admin only""",

    'pins': """<b>📌 Pin Commands:</b>

/pin (reply) - Pin message silently
/pin loud (reply) - Pin with notification
/permapin message - Pin new message
/unpin (reply) - Unpin specific message
/unpinall - Unpin all messages
/antichannelpin on/off - Unpin linked channel posts
/cleanlinked on/off - Delete linked channel posts

<b>Roles:</b> Admin only""",

    'reports': """<b>🚨 Reports Commands:</b>

/reports on/off - Toggle reports
/report (reply) - Report message to admins
@admin (reply) - Alternative report command

Reports notify all admins about problematic messages.

<b>Roles:</b> Anyone can report""",

    'languages': """<b>🌐 Language Commands:</b>

/lang - Show current language
/lang en - Set language

<b>Roles:</b> Admin only""",

    'privacy': """<b>🔒 Privacy Commands:</b>

/privacy - View and delete your data (PM only)

Rose respects your privacy. Use this command to see what data is stored.""",

    'formatting': """<b>✏️ Formatting Options:</b>

<b>Markdown:</b>
*bold*, _italic_, [link](url), `code`

<b>HTML:</b>
&lt;b&gt;bold&lt;/b&gt;, &lt;i&gt;italic&lt;/i&gt;, &lt;code&gt;code&lt;/code&gt;, &lt;a href="url"&gt;text&lt;/a&gt;

<b>Variables:</b>
{first}, {last}, {username}, {mention}, {chatname}""",

    # NEW HELP TEXTS
    'purge': """<b>🗑️ Purge Commands:</b>

/del (reply) - Delete single message
/purge (reply) - Purge from reply to current
/spurge (reply) - Silent purge (no confirmation)
/purgefrom (reply) - Mark purge start point
/purgeto (reply) - Mark purge end & execute

<b>Roles:</b> Cleaner, Admin, Moderator""",

    'blockbots': """<b>🤖 Block Bots:</b>

/blockbots on/off - Toggle bot blocking

When enabled:
• Non-admins adding bots get muted
• Added bot gets kicked immediately

<b>Roles:</b> Admin only""",

    'forwardblock': """<b>⏩ Block Forward:</b>

/blockforward on/off - Toggle forward blocking

When enabled:
• Deletes forwarded messages from non-admins
• Optional punishment (mute/ban)

<b>Roles:</b> Admin only""",

    'prefix': """<b>⚡ Command Prefix:</b>

/prefix - Show current prefixes
/setprefix ./! - Set command prefixes

Default: /
Examples: !ban, .kick, /mute all work!

<b>Roles:</b> Admin only""",

    'roles': """<b>👥 Role System:</b>

/mod @user - Make Moderator (ban, mute, warn)
/muter @user - Make Muter (mute/unmute only)
/cleaner @user - Make Cleaner (purge, delete)
/helper @user - Make Helper (visible in staff)
/free @user - Make Free (immune to punishments)
/unmod @user - Remove custom role

<b>Hierarchy:</b>
👑 Founder > ⚜️ Co-Founder > 👮 Admin > 👷 Moderator > 🛃 Cleaner > 🙊 Muter > ⛑ Helper > 🔓 Free

<b>Roles:</b> Admin+ can assign""",

    'staff': """<b>📋 Staff Command:</b>

/staff - List all staff members with roles

Shows: Founder, Co-Founders, Admins, Moderators, Cleaners, Muters, Helpers

<b>Roles:</b> Anyone can view""",
}

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help menu"""
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
    """Handle help button clicks"""
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