from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def help_menu_buttons():
    keyboard = [
        [InlineKeyboardButton("Admin", callback_data='help_admin'),
         InlineKeyboardButton("Bans", callback_data='help_bans')],
        [InlineKeyboardButton("Warnings", callback_data='help_warnings'),
         InlineKeyboardButton("Locks", callback_data='help_locks')],
        [InlineKeyboardButton("Approvals", callback_data='help_approvals'),
         InlineKeyboardButton("AntiRaid", callback_data='help_antiraid')],
        [InlineKeyboardButton("Greetings", callback_data='help_greetings'),
         InlineKeyboardButton("CAPTCHA", callback_data='help_captcha')],
        [InlineKeyboardButton("Federations", callback_data='coming_soon_federations'),
         InlineKeyboardButton("Notes", callback_data='coming_soon_notes')],
        [InlineKeyboardButton("Filters", callback_data='help_filters'),
         InlineKeyboardButton("Blocklists", callback_data='help_blocklists')],
        [InlineKeyboardButton("AntiFlood", callback_data='help_antiflood'),
         InlineKeyboardButton("Clean Command", callback_data='help_clean_command')],
        [InlineKeyboardButton("Clean Service", callback_data='help_clean_service'),
         InlineKeyboardButton("Disabling", callback_data='help_disabling')],
        [InlineKeyboardButton("Log Channels", callback_data='help_log_channels'),
         InlineKeyboardButton("Pins", callback_data='help_pins')],
        [InlineKeyboardButton("Reports", callback_data='help_reports'),
         InlineKeyboardButton("Topics", callback_data='coming_soon_topics')],
        [InlineKeyboardButton("Import/Export", callback_data='coming_soon_import_export'),
         InlineKeyboardButton("Languages", callback_data='help_languages')],
        [InlineKeyboardButton("Privacy", callback_data='help_privacy'),
         InlineKeyboardButton("Formatting", callback_data='help_formatting')],
    ]
    return InlineKeyboardMarkup(keyboard)

def start_buttons(bot_username):
    keyboard = [
        [InlineKeyboardButton("📢 Support Channel", url="https://t.me/Umm_ohk")],
        [InlineKeyboardButton("➕ Add Me to Group", url=f"https://t.me/{bot_username}?startgroup=true")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    keyboard = [[InlineKeyboardButton("◀️ Back to Help", callback_data='help_back')]]
    return InlineKeyboardMarkup(keyboard)

def coming_soon_buttons():
    keyboard = [[InlineKeyboardButton("◀️ Back to Help", callback_data='help_back')]]
    return InlineKeyboardMarkup(keyboard)
