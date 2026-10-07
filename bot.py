import copy
import json
import os
import re
import time
import asyncio
from datetime import datetime, timedelta, timezone

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatPermissions,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "PASTE-YOUR-BOTFATHER-TOKEN-HERE")
SUPPORT_CHANNEL = os.environ.get("SUPPORT_CHANNEL", "https://t.me/YourSupportChannel")
DATA_FILE = "rose_data.json"

# ------------------------------------------------------------------
# DATA STORAGE (saved to JSON file)
# ------------------------------------------------------------------
DEFAULT_CHAT = {
    "welcome": "",
    "welcome_on": True,
    "goodbye": "",
    "goodbye_on": True,
    "rules": "",
    "locks": [],
    "allowlist": [],
    "blocklist": [],
    "blocklistmode": "delete",
    "flood": 0,
    "floodmode": "mute",
    "warnlimit": 3,
    "warnmode": "ban",
    "warns": {},
    "filters": {},
    "reports": True,
}


def load_data():
    global DATA
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                DATA = json.load(f)
        except Exception:
            DATA = {}
    else:
        DATA = {}


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(DATA, f, ensure_ascii=False, indent=2)


def get_chat_data(chat_id):
    key = str(chat_id)
    if key not in DATA:
        DATA[key] = copy.deepcopy(DEFAULT_CHAT)
    return DATA[key]


DATA = {}
load_data()

FLOOD_TRACK = {}   # (chat_id, user_id) -> [timestamps]
FLOOD_COOLDOWN = set()

# ------------------------------------------------------------------
# HELP SECTIONS (button based /help)
# ------------------------------------------------------------------
HELP_SECTIONS = {
    "admins": [
        "<b>👤 Admins</b>",
        "",
        "/promote - promote a user to admin (reply or @user)",
        "/demote - remove admin rights",
        "/adminlist - list all admins",
        "/title name - set custom admin title (reply to admin)",
        "/pin - pin the replied message",
        "/unpin - unpin the replied message",
    ],
    "bans": [
        "<b>🔨 Bans, Kicks &amp; Mutes</b>",
        "",
        "/ban - ban a user permanently",
        "/tban 3d - ban for 3 days (m/h/d/w)",
        "/unban - unban a user",
        "/kick - remove user (can rejoin)",
        "/mute - mute a user",
        "/tmute 2h - mute for 2 hours",
        "/unmute - unmute a user",
        "/kickme - kick yourself",
        "/dban - delete message + ban",
        "/dtmute - delete message + mute",
        "/sban - silent ban (no confirmation)",
    ],
    "warns": [
        "<b>⚠️ Warnings</b>",
        "",
        "/warn - warn a user (optionally + reason)",
        "/dwarn - warn + delete the message",
        "/swarn - silent warn",
        "/warns - view a user's warnings",
        "/rmwarn - remove the last warning",
        "/resetwarn - clear all warnings",
        "/setwarnlimit 5 - warnings before action",
        "/setwarnmode ban - ban / kick / mute / tmute 1d / tban 1d",
    ],
    "rules": [
        "<b>📜 Rules</b>",
        "",
        "/rules - view the group rules",
        "/setrules your text - set the rules",
        "/clearrules - delete the rules",
    ],
    "welcome": [
        "<b>👋 Welcome / Goodbye</b>",
        "",
        "/welcome on - enable welcome messages",
        "/welcome off - disable welcome messages",
        "/welcome - view current welcome message",
        "/setwelcome text - set welcome message",
        "/resetwelcome - restore default",
        "/goodbye on/off - toggle goodbye",
        "/setgoodbye text - set goodbye message",
        "/resetgoodbye - restore default",
        "",
        "Fillings: {first} {last} {fullname} {username} {id} {chatname} {count}",
    ],
    "locks": [
        "<b>🔒 Locks</b>",
        "",
        "/lock url - lock a message type",
        "/unlock url - unlock it",
        "/locks - show active locks",
        "/locktypes - all lockable types",
        "/allowlist @user or domain - allow exceptions",
        "/rmallowlist @user - remove exception",
        "",
        "Types: url, forward, sticker, photo, video, gif, voice,",
        "audio, document, video_note, contact, location, poll,",
        "command, button, bot",
    ],
    "blocklist": [
        "<b>🚫 Blocklist</b>",
        "",
        "/addblocklist word - add blocked word(s)",
        "/blocklist - view blocked words",
        "/rmblocklist word - remove a word",
        "/rmblocklistall - clear the whole list",
        "/blocklistmode delete - delete / warn / mute / tmute 1d / ban / tban 1d",
    ],
    "antiflood": [
        "<b>🌊 Antiflood</b>",
        "",
        "/setflood 5 - max messages before action (0 = off)",
        "/setfloodmode mute - mute / kick / ban / tmute 1d / tban 1d",
        "/flood - view current settings",
    ],
    "filters": [
        "<b>🧲 Filters</b>",
        "",
        "/filter trigger - reply to a message to auto-answer that word",
        "/filter trigger text - set a text filter",
        "/stop trigger - remove a filter",
        "/stopall - remove all filters",
        "/filters - list all filters",
    ],
    "purge": [
        "<b>🧹 Purge &amp; Delete</b>",
        "",
        "/del - delete the replied message",
        "/purge - delete all messages from the replied one until now",
        "/purge 10 - delete the last 10 messages",
        "/spurge - silent purge",
    ],
    "misc": [
        "<b>ℹ️ Info &amp; Misc</b>",
        "",
        "/id - get chat/user ID (reply for user ID)",
        "/info - user info + warning count",
        "/report - reply to report a message to admins",
        "/reports on/off - toggle reports (admin)",
    ],
}

HELP_BUTTONS = [
    [InlineKeyboardButton("👤 Admins", callback_data="help:admins"),
     InlineKeyboardButton("🔨 Bans & Mutes", callback_data="help:bans")],
    [InlineKeyboardButton("⚠️ Warnings", callback_data="help:warns"),
     InlineKeyboardButton("📜 Rules", callback_data="help:rules")],
    [InlineKeyboardButton("👋 Welcome", callback_data="help:welcome"),
     InlineKeyboardButton("🔒 Locks", callback_data="help:locks")],
    [InlineKeyboardButton("🚫 Blocklist", callback_data="help:blocklist"),
     InlineKeyboardButton("🌊 Antiflood", callback_data="help:antiflood")],
    [InlineKeyboardButton("🧲 Filters", callback_data="help:filters"),
     InlineKeyboardButton("🧹 Purge", callback_data="help:purge")],
    [InlineKeyboardButton("ℹ️ Info & Misc", callback_data="help:misc")],
]

LOCK_TYPES = ["url", "forward", "sticker", "photo", "video", "gif", "voice",
              "audio", "document", "video_note", "contact", "location",
              "poll", "command", "button", "bot"]

# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------
def parse_time(text):
    m = re.fullmatch(r"(\d+)([mhdw])", (text or "").lower().strip())
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    return {"m": timedelta(minutes=n), "h": timedelta(hours=n),
            "d": timedelta(days=n), "w": timedelta(weeks=n)}[unit]


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id=None):
    chat = update.effective_chat
    user = user_id or update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat.id, user)
        return member.status in ("administrator", "creator")
    except BadRequest:
        return False


def admin_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type not in ("group", "supergroup"):
            return
        if not await is_admin(update, context):
            await update.effective_message.reply_text("You need to be an admin to do that.")
            return
        return await func(update, context)
    return wrapper


def bot_reply(msg, text):
    return msg.reply_text(text)


async def get_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user
    if context.args:
        arg = context.args[0]
        try:
            if arg.lstrip("@").isdigit():
                return await context.bot.get_chat(int(arg))
            if arg.startswith("@"):
                return await context.bot.get_chat(arg)
        except BadRequest:
            return None
    return None


async def apply_punishment(context, chat_id, user_id, mode):
    try:
        now = datetime.now(timezone.utc)
        if mode == "ban":
            await context.bot.ban_chat_member(chat_id, user_id)
        elif mode == "kick":
            await context.bot.ban_chat_member(chat_id, user_id)
            await context.bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
        elif mode == "mute":
            await context.bot.restrict_chat_member(
                chat_id, user_id, permissions=ChatPermissions.no_permissions())
        elif mode.startswith("tmute") or mode.startswith("tban"):
            parts = mode.split()
            delta = parse_time(parts[1]) if len(parts) > 1 else timedelta(hours=1)
            if not delta:
                return
            if mode.startswith("tmute"):
                await context.bot.restrict_chat_member(
                    chat_id, user_id, permissions=ChatPermissions.no_permissions(),
                    until_date=now + delta)
            else:
                await context.bot.ban_chat_member(chat_id, user_id, until_date=now + delta)
    except BadRequest as e:
        print(f"Punishment error: {e}")


def fill_text(text, user, chat):
    username = f"@{user.username}" if user.username else user.first_name
    return (text
            .replace("{first}", user.first_name or "")
            .replace("{last}", user.last_name or "")
            .replace("{fullname}", f"{user.first_name or ''} {user.last_name or ''}".strip())
            .replace("{username}", username)
            .replace("{id}", str(user.id))
            .replace("{chatname}", chat.title or "")
            .replace("{count}", str(chat.id and "" or "")))


def check_locks(msg, locks):
    hit = []
    ent_types = set()
    if msg.entities:
        ent_types |= {e.type for e in msg.entities}
    if msg.caption_entities:
        ent_types |= {e.type for e in msg.caption_entities}
    for lock in locks:
        if lock == "url" and ("url" in ent_types or "text_link" in ent_types):
            hit.append(lock)
        elif lock == "forward" and (getattr(msg, "forward_origin", None) or
                                    getattr(msg, "forward_from", None) or
                                    getattr(msg, "forward_from_chat", None)):
            hit.append(lock)
        elif lock == "sticker" and msg.sticker:
            hit.append(lock)
        elif lock == "photo" and msg.photo:
            hit.append(lock)
        elif lock == "video" and msg.video:
            hit.append(lock)
        elif lock == "gif" and msg.animation:
            hit.append(lock)
        elif lock == "voice" and msg.voice:
            hit.append(lock)
        elif lock == "audio" and msg.audio:
            hit.append(lock)
        elif lock == "document" and msg.document:
            hit.append(lock)
        elif lock == "video_note" and msg.video_note:
            hit.append(lock)
        elif lock == "contact" and msg.contact:
            hit.append(lock)
        elif lock == "location" and msg.location:
            hit.append(lock)
        elif lock == "poll" and msg.poll:
            hit.append(lock)
        elif lock == "command" and "bot_command" in ent_types:
            hit.append(lock)
        elif lock == "button" and msg.reply_markup:
            hit.append(lock)
        elif lock == "bot" and msg.via_bot:
            hit.append(lock)
    return hit


def extract_content(reply):
    """Turn a replied-to message into storable filter content."""
    if reply.text:
        return {"type": "text", "text": reply.text}
    if reply.photo:
        return {"type": "photo", "file_id": reply.photo[-1].file_id, "caption": reply.caption or ""}
    if reply.sticker:
        return {"type": "sticker", "file_id": reply.sticker.file_id}
    if reply.video:
        return {"type": "video", "file_id": reply.video.file_id, "caption": reply.caption or ""}
    if reply.animation:
        return {"type": "animation", "file_id": reply.animation.file_id, "caption": reply.caption or ""}
    if reply.audio:
        return {"type": "audio", "file_id": reply.audio.file_id, "caption": reply.caption or ""}
    if reply.voice:
        return {"type": "voice", "file_id": reply.voice.file_id}
    if reply.video_note:
        return {"type": "video_note", "file_id": reply.video_note.file_id}
    if reply.document:
        return {"type": "document", "file_id": reply.document.file_id, "caption": reply.caption or ""}
    return None


async def send_content(msg, content):
    ftype = content.get("type", "text")
    if ftype == "text":
        await msg.reply_text(content["text"])
    elif ftype == "sticker":
        await msg.reply_sticker(content["file_id"])
    elif ftype == "voice":
        await msg.reply_voice(content["file_id"])
    elif ftype == "video_note":
        await msg.reply_video_note(content["file_id"])
    else:
        method = getattr(msg, f"reply_{ftype}", None)
        if method:
            await method(content["file_id"], caption=content.get("caption") or None)


# ------------------------------------------------------------------
# START & HELP (buttons)
# ------------------------------------------------------------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if chat.type in ("group", "supergroup"):
        await update.effective_message.reply_text(
            "Hey! I'm alive. Use /help to see my commands (in buttons).")
        return

    name = user.first_name or "there"
    text = (
        f"Hi {name}! 👋\n\n"
        "I'm Rose, your group management bot.\n"
        "Add me to your group and make me an admin, and I'll protect "
        "your chat with bans, mutes, warnings, locks, antiflood, filters "
        "and much more.\n\n"
        "Tap Help to see all my commands in buttons."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me To Group",
                              url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("📣 Support Channel", url=SUPPORT_CHANNEL)],
        [InlineKeyboardButton("📖 Help", callback_data="help:main")],
    ])
    await update.effective_message.reply_text(text, reply_markup=keyboard)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup(HELP_BUTTONS)
    await update.effective_message.reply_text(
        "📖 Choose a section:\n\nAll Rose commands are inside the buttons.",
        reply_markup=keyboard)


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "help:main":
        await query.edit_message_text(
            "📖 Choose a section:\n\nAll Rose commands are inside the buttons.",
            reply_markup=InlineKeyboardMarkup(HELP_BUTTONS))
    elif query.data.startswith("help:"):
        section = query.data.split(":", 1)[1]
        text = "\n".join(HELP_SECTIONS.get(section, ["Nothing here."]))
        back = InlineKeyboardMarkup(
            [[InlineKeyboardButton("⬅️ Back", callback_data="help:main")]])
        try:
            await query.edit_message_text(text, reply_markup=back,
                                          parse_mode=ParseMode.HTML)
        except BadRequest:
            await query.edit_message_text(
                "\n".join(HELP_SECTIONS.get(section, ["Nothing here."])),
                reply_markup=back)


# ------------------------------------------------------------------
# ADMIN COMMANDS
# ------------------------------------------------------------------
@admin_required
async def cmd_promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target(update, context)
    if not target:
        return await bot_reply(msg, "Reply to a user or give @username / ID.")
    try:
        await context.bot.promote_chat_member(
            msg.chat_id, target.id,
            can_delete_messages=True, can_restrict_members=True,
            can_pin_messages=True, can_invite_users=True)
        await bot_reply(msg, f"✅ Promoted {target.first_name}!")
    except BadRequest as e:
        await bot_reply(msg, f"Failed: {e.message}")


@admin_required
async def cmd_demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target(update, context)
    if not target:
        return await bot_reply(msg, "Reply to a user or give @username / ID.")
    try:
        await context.bot.promote_chat_member(
            msg.chat_id, target.id,
            can_delete_messages=False, can_restrict_members=False,
            can_promote_members=False, can_pin_messages=False)
        await bot_reply(msg, f"✅ Demoted {target.first_name}.")
    except BadRequest as e:
        await bot_reply(msg, f"Failed: {e.message}")


@admin_required
async def cmd_adminlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins = await update.effective_chat.get_administrators()
    lines = ["👑 Admins:\n"]
    for a in admins:
        if a.user.is_bot:
            continue
        title = getattr(a, "custom_title", None) or a.status
        lines.append(f"• {a.user.first_name} ({title})")
    await bot_reply(update.effective_message, "\n".join(lines))


@admin_required
async def cmd_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target(update, context)
    title = " ".join(context.args[1:]) if len(context.args) > 1 else None
    if not target or not title:
        return await bot_reply(msg, "Usage: /title NewTitle (reply to an admin)")
    try:
        await context.bot.set_chat_administrator_custom_title(msg.chat_id, target.id, title)
        await bot_reply(msg, f"✅ Title set to '{title}'.")
    except BadRequest as e:
        await bot_reply(msg, f"Failed: {e.message}")


@admin_required
async def cmd_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg.reply_to_message:
        return await bot_reply(msg, "Reply to a message to pin it.")
    try:
        await context.bot.pin_chat_message(msg.chat_id, msg.reply_to_message.message_id)
    except BadRequest as e:
        await bot_reply(msg, f"Failed: {e.message} (do I have pin permission?)")


@admin_required
async def cmd_unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg.reply_to_message:
        return await bot_reply(msg, "Reply to a pinned message to unpin it.")
    try:
        await context.bot.unpin_chat_message(msg.chat_id, message_id=msg.reply_to_message.message_id)
    except BadRequest as e:
        await bot_reply(msg, f"Failed: {e.message}")


# ------------------------------------------------------------------
# BANS, KICKS, MUTES
# ------------------------------------------------------------------
@admin_required
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target(update, context)
    if not target:
        return await bot_reply(msg, "Reply to a user or give @username / ID.")
    if await is_admin(update, context, target.id):
        return await bot_reply(msg, "I can't ban an admin!")
    try:
        await context.bot.ban_chat_member(msg.chat_id, target.id)
        await bot_reply(msg, f"🔨 Banned {target.first_name}.")
    except BadRequest as e:
        await bot_reply(msg, f"Failed: {e.message} (do I have ban permission?)")


@admin_required
async def cmd_tban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    delta = parse_time(context.args[0] if context.args else "")
    if not delta:
        return await bot_reply(msg, "Usage: /tban 3d (m/h/d/w)")
    target = await get_target(update, context)
    if not target:
        return await bot_reply(msg, "Reply to a user or give @username / ID.")
    try:
        await context.bot.ban_chat_member(
            msg.chat_id, target.id, until_date=datetime.now(timezone.utc) + delta)
        await bot_reply(msg, f"⏳ Banned {target.first_name} for {context.args[0]}.")
    except BadRequest as e:
        await bot_reply(msg, f"Failed: {e.message}")


@admin_required
async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target(update, context)
    if not target:
        return await bot_reply(msg, "Reply to a user or give @username / ID.")
    await context.bot.unban_chat_member(msg.chat_id, target.id, only_if_banned=True)
    await bot_reply(msg, f"✅ Unbanned {target.first_name}.")


@admin_required
async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target(update, context)
    if not target:
        return await bot_reply(msg, "Reply to a user or give @username / ID.")
    try:
        await context.bot.ban_chat_member(msg.chat_id, target.id)
        await context.bot.unban_chat_member(msg.chat_id, target.id, only_if_banned=True)
        await bot_reply(msg, f"👢 Kicked {target.first_name}.")
    except BadRequest as e:
        await bot_reply(msg, f"Failed: {e.message}")


@admin_required
async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target(update, context)
    if not target:
        return await bot_reply(msg, "Reply to a user or give @username / ID.")
    if await is_admin(update, context, target.id):
        return await bot_reply(msg, "I can't mute an admin!")
    try:
        await context.bot.restrict_chat_member(
            msg.chat_id, target.id, permissions=ChatPermissions.no_permissions())
        await bot_reply(msg, f"🔇 Muted {target.first_name}.")
    except BadRequest as e:
        await bot_reply(msg, f"Failed: {e.message}")


@admin_required
async def cmd_tmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    delta = parse_time(context.args[0] if context.args else "")
    if not delta:
        return await bot_reply(msg, "Usage: /tmute 2h (m/h/d/w)")
    target = await get_target(update, context)
    if not target:
        return await bot_reply(msg, "Reply to a user or give @username / ID.")
    try:
        await context.bot.restrict_chat_member(
            msg.chat_id, target.id, permissions=ChatPermissions.no_permissions(),
            until_date=datetime.now(timezone.utc) + delta)
        await bot_reply(msg, f"🔇 Muted {target.first_name} for {context.args[0]}.")
    except BadRequest as e:
        await bot_reply(msg, f"Failed: {e.message}")


@admin_required
async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target(update, context)
    if not target:
        return await bot_reply(msg, "Reply to a user or give @username / ID.")
    await context.bot.restrict_chat_member(
        msg.chat_id, target.id, permissions=ChatPermissions.all_permissions())
    await bot_reply(msg, f"🔊 Unmuted {target.first_name}.")


@admin_required
async def cmd_dban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target(update, context)
    if not target:
        return await bot_reply(msg, "Reply to a user.")
    try:
        if msg.reply_to_message:
            await msg.reply_to_message.delete()
        await context.bot.ban_chat_member(msg.chat_id, target.id)
        await bot_reply(msg, f"🔨 Message deleted + {target.first_name} banned.")
    except BadRequest as e:
        await bot_reply(msg, f"Failed: {e.message}")


@admin_required
async def cmd_dtmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    delta = parse_time(context.args[0] if context.args else "") or timedelta(hours=1)
    target = await get_target(update, context)
    if not target:
        return await bot_reply(msg, "Reply to a user.")
    try:
        if msg.reply_to_message:
            await msg.reply_to_message.delete()
        await context.bot.restrict_chat_member(
            msg.chat_id, target.id, permissions=ChatPermissions.no_permissions(),
            until_date=datetime.now(timezone.utc) + delta)
        await bot_reply(msg, f"🔇 Message deleted + {target.first_name} muted.")
    except BadRequest as e:
        await bot_reply(msg, f"Failed: {e.message}")


@admin_required
async def cmd_sban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target(update, context)
    if target:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        except BadRequest:
            pass


async def cmd_kickme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    await bot_reply(msg, "nop u can't kick me")
    try:
        await context.bot.ban_chat_member(msg.chat_id, user.id)
        await context.bot.unban_chat_member(msg.chat_id, user.id, only_if_banned=True)
    except BadRequest:
        pass


# ------------------------------------------------------------------
# WARNINGS
# ------------------------------------------------------------------
async def warn_user(update, context, silent=False, delete=False):
    msg = update.effective_message
    target = await get_target(update, context)
    if not target:
        return await bot_reply(msg, "Reply to a user or give @username / ID.")
    data = get_chat_data(msg.chat_id)
    reason = " ".join(context.args) if context.args else "No reason given."
    if msg.reply_to_message and context.args:
        reason = " ".join(context.args)
    key = str(target.id)
    data["warns"].setdefault(key, [])
    data["warns"][key].append(reason)
    count = len(data["warns"][key])
    limit = data.get("warnlimit", 3)
    mode = data.get("warnmode", "ban")
    save_data()

    text = (f"⚠️ {target.first_name} has been warned ({count}/{limit}).\n"
            f"Reason: {reason}")
    if not silent:
        await bot_reply(msg, text)
    if delete and msg.reply_to_message:
        try:
            await msg.reply_to_message.delete()
        except BadRequest:
            pass
    if count >= limit:
        data["warns"][key] = []
        save_data()
        await apply_punishment(context, msg.chat_id, target.id, mode)
        if not silent:
            await bot_reply(msg, f"⛔ {target.first_name} reached the warn limit ({limit}). Action: {mode}")


@admin_required
async def cmd_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await warn_user(update, context)


@admin_required
async def cmd_dwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await warn_user(update, context, delete=True)


@admin_required
async def cmd_swarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await warn_user(update, context, silent=True)


@admin_required
async def cmd_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target(update, context)
    if not target:
        return await bot_reply(msg, "Reply to a user or give @username / ID.")
    data = get_chat_data(msg.chat_id)
    warns = data["warns"].get(str(target.id), [])
    if not warns:
        return await bot_reply(msg, f"{target.first_name} has no warnings. 🎉")
    lines = [f"⚠️ {target.first_name} has {len(warns)} warning(s):"]
    lines += [f"{i}. {w}" for i, w in enumerate(warns, 1)]
    await bot_reply(msg, "\n".join(lines))


@admin_required
async def cmd_rmwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target(update, context)
    if not target:
        return await bot_reply(msg, "Reply to a user.")
    data = get_chat_data(msg.chat_id)
    warns = data["warns"].get(str(target.id), [])
    if warns:
        warns.pop()
        data["warns"][str(target.id)] = warns
        save_data()
    await bot_reply(msg, f"✅ Last warning removed for {target.first_name}.")


@admin_required
async def cmd_resetwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target(update, context)
    if not target:
        return await bot_reply(msg, "Reply to a user.")
    data = get_chat_data(msg.chat_id)
    data["warns"][str(target.id)] = []
    save_data()
    await bot_reply(msg, f"♻️ All warnings cleared for {target.first_name}.")


@admin_required
async def cmd_setwarnlimit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args or not context.args[0].isdigit():
        return await bot_reply(msg, "Usage: /setwarnlimit 3")
    data = get_chat_data(msg.chat_id)
    data["warnlimit"] = int(context.args[0])
    save_data()
    await bot_reply(msg, f"✅ Warn limit set to {context.args[0]}.")


@admin_required
async def cmd_setwarnmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        return await bot_reply(msg,
            "Usage: /setwarnmode ban  (ban / kick / mute / tmute 1d / tban 1d)")
    data = get_chat_data(msg.chat_id)
    data["warnmode"] = " ".join(context.args).lower()
    save_data()
    await bot_reply(msg, f"✅ Warn mode set to: {data['warnmode']}")


# ------------------------------------------------------------------
# RULES
# ------------------------------------------------------------------
async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_chat_data(update.effective_chat.id)
    if data["rules"]:
        await bot_reply(update.effective_message, f"📜 Rules:\n\n{data['rules']}")
    else:
        await bot_reply(update.effective_message, "No rules set for this chat yet.")


@admin_required
async def cmd_setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await bot_reply(update.effective_message, "Usage: /setrules your rules here")
    data = get_chat_data(update.effective_chat.id)
    data["rules"] = " ".join(context.args)
    save_data()
    await bot_reply(update.effective_message, "✅ Rules saved!")


@admin_required
async def cmd_clearrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_chat_data(update.effective_chat.id)
    data["rules"] = ""
    save_data()
    await bot_reply(update.effective_message, "✅ Rules cleared.")


# ------------------------------------------------------------------
# WELCOME / GOODBYE
# ------------------------------------------------------------------
@admin_required
async def cmd_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    data = get_chat_data(msg.chat_id)
    if context.args and context.args[0].lower() in ("on", "off"):
        data["welcome_on"] = context.args[0].lower() == "on"
        save_data()
        return await bot_reply(msg, f"Welcome messages: {'ON' if data['welcome_on'] else 'OFF'}")
    if data["welcome"]:
        await bot_reply(msg, f"Current welcome:\n\n{data['welcome']}")
    else:
        await bot_reply(msg, "No welcome set. Use /setwelcome to create one.")


@admin_required
async def cmd_setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await bot_reply(update.effective_message, "Usage: /setwelcome Welcome {first}!")
    data = get_chat_data(update.effective_chat.id)
    data["welcome"] = " ".join(context.args)
    data["welcome_on"] = True
    save_data()
    await bot_reply(update.effective_message, "✅ Welcome message saved and enabled!")


@admin_required
async def cmd_resetwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_chat_data(update.effective_chat.id)
    data["welcome"] = ""
    save_data()
    await bot_reply(update.effective_message, "✅ Welcome reset.")


@admin_required
async def cmd_goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    data = get_chat_data(msg.chat_id)
    if context.args and context.args[0].lower() in ("on", "off"):
        data["goodbye_on"] = context.args[0].lower() == "on"
        save_data()
        return await bot_reply(msg, f"Goodbye messages: {'ON' if data['goodbye_on'] else 'OFF'}")
    if data["goodbye"]:
        await bot_reply(msg, f"Current goodbye:\n\n{data['goodbye']}")
    else:
        await bot_reply(msg, "No goodbye set. Use /setgoodbye to create one.")


@admin_required
async def cmd_setgoodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await bot_reply(update.effective_message, "Usage: /setgoodbye Bye {first}!")
    data = get_chat_data(update.effective_chat.id)
    data["goodbye"] = " ".join(context.args)
    save_data()
    await bot_reply(update.effective_message, "✅ Goodbye message saved!")


@admin_required
async def cmd_resetgoodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_chat_data(update.effective_chat.id)
    data["goodbye"] = ""
    save_data()
    await bot_reply(update.effective_message, "✅ Goodbye reset.")


async def on_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    data = get_chat_data(chat.id)
    for user in msg.new_chat_members:
        if user.id == context.bot.id:
            await msg.reply_text(
                "Thanks for adding me! Make me admin, then use /help for commands.")
            continue
        if data.get("welcome_on") and data.get("welcome"):
            await msg.reply_text(fill_text(data["welcome"], user, chat))


async def on_left_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    data = get_chat_data(chat.id)
    user = msg.left_chat_member
    if user and data.get("goodbye_on") and data.get("goodbye"):
        try:
            await msg.reply_text(fill_text(data["goodbye"], user, chat))
        except BadRequest:
            pass


# ------------------------------------------------------------------
# LOCKS
# ------------------------------------------------------------------
@admin_required
async def cmd_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        return await bot_reply(msg, f"Usage: /lock url\nTypes: {', '.join(LOCK_TYPES)}")
    data = get_chat_data(msg.chat_id)
    added = []
    for t in context.args:
        t = t.lower()
        if t in LOCK_TYPES and t not in data["locks"]:
            data["locks"].append(t)
            added.append(t)
    save_data()
    await bot_reply(msg, f"🔒 Locked: {', '.join(added)}" if added else "Already locked or unknown type.")


@admin_required
async def cmd_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        return await bot_reply(msg, "Usage: /unlock url")
    data = get_chat_data(msg.chat_id)
    removed = [t for t in context.args if t.lower() in data["locks"]]
    data["locks"] = [t for t in data["locks"] if t not in [x.lower() for x in context.args]]
    save_data()
    await bot_reply(msg, f"🔓 Unlocked: {', '.join(removed)}" if removed else "That type wasn't locked.")


@admin_required
async def cmd_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_chat_data(update.effective_chat.id)
    if data["locks"]:
        await bot_reply(update.effective_message, "🔒 Currently locked:\n" + ", ".join(data["locks"]))
    else:
        await bot_reply(update.effective_message, "Nothing is locked in this chat.")


@admin_required
async def cmd_locktypes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await bot_reply(update.effective_message,
                    "Lockable types:\n" + ", ".join(LOCK_TYPES))


@admin_required
async def cmd_allowlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        data = get_chat_data(update.effective_chat.id)
        if data["allowlist"]:
            return await bot_reply(update.effective_message,
                                   "Allowlist:\n" + "\n".join(data["allowlist"]))
        return await bot_reply(update.effective_message, "Allowlist is empty. Usage: /allowlist @user")
    data = get_chat_data(update.effective_chat.id)
    data["allowlist"].extend(context.args)
    save_data()
    await bot_reply(update.effective_message, "✅ Added to allowlist.")


@admin_required
async def cmd_rmallowlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await bot_reply(update.effective_message, "Usage: /rmallowlist @user")
    data = get_chat_data(update.effective_chat.id)
    data["allowlist"] = [a for a in data["allowlist"] if a not in context.args]
    save_data()
    await bot_reply(update.effective_message, "✅ Removed from allowlist.")


# ------------------------------------------------------------------
# BLOCKLIST
# ------------------------------------------------------------------
@admin_required
async def cmd_addblocklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await bot_reply(update.effective_message, "Usage: /addblocklist word1 word2")
    data = get_chat_data(update.effective_chat.id)
    data["blocklist"].extend(context.args)
    save_data()
    await bot_reply(update.effective_message, f"🚫 Added to blocklist: {', '.join(context.args)}")


@admin_required
async def cmd_blocklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_chat_data(update.effective_chat.id)
    if data["blocklist"]:
        await bot_reply(update.effective_message,
                        "🚫 Blocked words:\n" + ", ".join(data["blocklist"]))
    else:
        await bot_reply(update.effective_message, "Blocklist is empty.")


@admin_required
async def cmd_rmblocklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await bot_reply(update.effective_message, "Usage: /rmblocklist word")
    data = get_chat_data(update.effective_chat.id)
    data["blocklist"] = [w for w in data["blocklist"] if w not in context.args]
    save_data()
    await bot_reply(update.effective_message, "✅ Removed.")


@admin_required
async def cmd_rmblocklistall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_chat_data(update.effective_chat.id)
    data["blocklist"] = []
    save_data()
    await bot_reply(update.effective_message, "✅ Blocklist cleared.")


@admin_required
async def cmd_blocklistmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await bot_reply(update.effective_message,
            "Usage: /blocklistmode delete (delete / warn / mute / tmute 1d / ban / tban 1d)")
    data = get_chat_data(update.effective_chat.id)
    data["blocklistmode"] = " ".join(context.args).lower()
    save_data()
    await bot_reply(update.effective_message, f"✅ Blocklist mode: {data['blocklistmode']}")


# ------------------------------------------------------------------
# ANTIFLOOD
# ------------------------------------------------------------------
@admin_required
async def cmd_setflood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].lstrip("-").isdigit():
        return await bot_reply(update.effective_message, "Usage: /setflood 5 (0 = off)")
    data = get_chat_data(update.effective_chat.id)
    data["flood"] = int(context.args[0])
    save_data()
    await bot_reply(update.effective_message,
                    f"✅ Antiflood set to {context.args[0]} messages (0 = off).")


@admin_required
async def cmd_setfloodmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await bot_reply(update.effective_message,
            "Usage: /setfloodmode mute (mute / kick / ban / tmute 1d / tban 1d)")
    data = get_chat_data(update.effective_chat.id)
    data["floodmode"] = " ".join(context.args).lower()
    save_data()
    await bot_reply(update.effective_message, f"✅ Flood mode: {data['floodmode']}")


@admin_required
async def cmd_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_chat_data(update.effective_chat.id)
    await bot_reply(update.effective_message,
        f"🌊 Antiflood settings:\nLimit: {data['flood']} messages\nMode: {data['floodmode']}")


# ------------------------------------------------------------------
# FILTERS
# ------------------------------------------------------------------
@admin_required
async def cmd_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        return await bot_reply(msg, "Usage: /filter trigger (reply to content, or add text after trigger)")
    trigger = context.args[0]
    content = None
    if msg.reply_to_message:
        content = extract_content(msg.reply_to_message)
    if content is None and len(context.args) > 1:
        content = {"type": "text", "text": " ".join(context.args[1:])}
    if content is None:
        return await bot_reply(msg, "Reply to a message or add text: /filter trigger your text")
    data = get_chat_data(msg.chat_id)
    data["filters"][trigger.lower()] = content
    save_data()
    await bot_reply(msg, f"🧲 Filter '{trigger}' saved!")


@admin_required
async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await bot_reply(update.effective_message, "Usage: /stop trigger")
    data = get_chat_data(update.effective_chat.id)
    removed = data["filters"].pop(context.args[0].lower(), None)
    save_data()
    await bot_reply(update.effective_message,
                    "✅ Filter removed." if removed else "No such filter.")


@admin_required
async def cmd_stopall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_chat_data(update.effective_chat.id)
    data["filters"] = {}
    save_data()
    await bot_reply(update.effective_message, "✅ All filters removed.")


@admin_required
async def cmd_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_chat_data(update.effective_chat.id)
    if data["filters"]:
        await bot_reply(update.effective_message,
                        "🧲 Active filters:\n" + ", ".join(data["filters"].keys()))
    else:
        await bot_reply(update.effective_message, "No filters in this chat.")


# ------------------------------------------------------------------
# PURGE
# ------------------------------------------------------------------
@admin_required
async def cmd_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg.reply_to_message:
        return await bot_reply(msg, "Reply to a message to delete it.")
    try:
        await msg.reply_to_message.delete()
        await msg.delete()
    except BadRequest:
        await bot_reply(msg, "Failed: do I have delete permission?")


@admin_required
async def cmd_purge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg.reply_to_message:
        return await bot_reply(msg, "Reply to a message to purge from there.")
    start = msg.reply_to_message.message_id
    end = msg.message_id
    if context.args and context.args[0].isdigit():
        end = start + int(context.args[0])
    count = 0
    for mid in range(start, min(end, start + 200) + 1):
        try:
            await context.bot.delete_message(msg.chat_id, mid)
            count += 1
        except BadRequest:
            pass
    if not context.args or context.args[0] != "silent":
        sent = await msg.chat.send_message(f"🧹 Deleted {count} messages.")
        await asyncio.sleep(3)
        try:
            await sent.delete()
        except BadRequest:
            pass


async def cmd_spurge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_purge(update, context)


# ------------------------------------------------------------------
# INFO & MISC
# ------------------------------------------------------------------
async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.from_user:
        u = msg.reply_to_message.from_user
        return await bot_reply(msg, f"User ID: {u.id}")
    await bot_reply(msg, f"Chat ID: {msg.chat_id}\nYour ID: {update.effective_user.id}")


async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target(update, context) or update.effective_user
    data = get_chat_data(msg.chat_id)
    warns = len(data["warns"].get(str(target.id), []))
    admin = await is_admin(update, context, target.id)
    username = f"@{target.username}" if getattr(target, "username", None) else "none"
    await bot_reply(msg,
        f"ℹ️ User Info\n\n"
        f"Name: {target.first_name}\n"
        f"ID: {target.id}\n"
        f"Username: {username}\n"
        f"Admin: {'Yes' if admin else 'No'}\n"
        f"Warnings: {warns}")


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    data = get_chat_data(msg.chat_id)
    if not data.get("reports", True):
        return
    if not msg.reply_to_message:
        return await bot_reply(msg, "Reply to a message to report it.")
    try:
        admins = await msg.chat.get_administrators()
        mentions = " ".join(a.user.mention_html() for a in admins if not a.user.is_bot)
        await msg.reply_text(
            f"⚠️ Report! {update.effective_user.mention_html()} reported "
            f"{msg.reply_to_message.from_user.mention_html()}.\n"
            f"Admins: {mentions}", parse_mode=ParseMode.HTML)
    except BadRequest:
        pass


@admin_required
async def cmd_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    data = get_chat_data(msg.chat_id)
    if context.args and context.args[0].lower() in ("on", "off"):
        data["reports"] = context.args[0].lower() == "on"
        save_data()
        return await bot_reply(msg, f"Reports: {'ON' if data['reports'] else 'OFF'}")
    await bot_reply(msg, "Usage: /reports on or /reports off")


# ------------------------------------------------------------------
# GROUP MESSAGE HANDLER (filters, blocklist, locks, antiflood)
# ------------------------------------------------------------------
async def on_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in ("group", "supergroup") or not user or user.is_bot:
        return

    data = get_chat_data(chat.id)
    text = msg.text or msg.caption or ""
    low = text.lower()

    # 1. FILTERS
    for trigger, content in data.get("filters", {}).items():
        if trigger in low:
            try:
                await send_content(msg, content)
            except BadRequest:
                pass
            break

    # admin messages skip moderation
    if await is_admin(update, context):
        return

    # 2. BLOCKLIST
    for word in data.get("blocklist", []):
        if word.lower() in low:
            try:
                await msg.delete()
            except BadRequest:
                pass
            await apply_punishment(context, chat.id, user.id, data.get("blocklistmode", "delete"))
            return

    # 3. LOCKS (allowlist check for urls)
    violations = check_locks(msg, data.get("locks", []))
    if violations:
        allowed = any(a.lower() in low for a in data.get("allowlist", []))
        if violations == ["url"] and allowed:
            return
        try:
            await msg.delete()
        except BadRequest:
            pass
        return

    # 4. ANTIFLOOD
    limit = data.get("flood", 0)
    if limit > 0:
        now = time.time()
        key = (chat.id, user.id)
        stamps = [t for t in FLOOD_TRACK.get(key, []) if now - t < 10]
        stamps.append(now)
        FLOOD_TRACK[key] = stamps
        if len(stamps) > limit and key not in FLOOD_COOLDOWN:
            FLOOD_COOLDOWN.add(key)
            await apply_punishment(context, chat.id, user.id, data.get("floodmode", "mute"))
            await msg.chat.send_message(f"🌊 {user.first_name} flooded and got: {data.get('floodmode', 'mute')}")
            async def clear_cd():
                await asyncio.sleep(30)
                FLOOD_COOLDOWN.discard(key)
            asyncio.create_task(clear_cd())


# ------------------------------------------------------------------
# BUILD APP
# ------------------------------------------------------------------
def build_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CallbackQueryHandler(on_button))

    # admins
    app.add_handler(CommandHandler("promote", cmd_promote))
    app.add_handler(CommandHandler("demote", cmd_demote))
    app.add_handler(CommandHandler("adminlist", cmd_adminlist))
    app.add_handler(CommandHandler("title", cmd_title))
    app.add_handler(CommandHandler("pin", cmd_pin))
    app.add_handler(CommandHandler("unpin", cmd_unpin))

    # bans
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("tban", cmd_tban))
    app.add_handler(CommandHandler("unban", cmd_unban))
    app.add_handler(CommandHandler("kick", cmd_kick))
    app.add_handler(CommandHandler("mute", cmd_mute))
    app.add_handler(CommandHandler("tmute", cmd_tmute))
    app.add_handler(CommandHandler("unmute", cmd_unmute))
    app.add_handler(CommandHandler("kickme", cmd_kickme))
    app.add_handler(CommandHandler("dban", cmd_dban))
    app.add_handler(CommandHandler("dtmute", cmd_dtmute))
    app.add_handler(CommandHandler("sban", cmd_sban))

    # warnings
    app.add_handler(CommandHandler("warn", cmd_warn))
    app.add_handler(CommandHandler("dwarn", cmd_dwarn))
    app.add_handler(CommandHandler("swarn", cmd_swarn))
    app.add_handler(CommandHandler("warns", cmd_warns))
    app.add_handler(CommandHandler("rmwarn", cmd_rmwarn))
    app.add_handler(CommandHandler("resetwarn", cmd_resetwarn))
    app.add_handler(CommandHandler("setwarnlimit", cmd_setwarnlimit))
    app.add_handler(CommandHandler("setwarnmode", cmd_setwarnmode))

    # rules
    app.add_handler(CommandHandler("rules", cmd_rules))
    app.add_handler(CommandHandler("setrules", cmd_setrules))
    app.add_handler(CommandHandler("clearrules", cmd_clearrules))

    # welcome / goodbye
    app.add_handler(CommandHandler("welcome", cmd_welcome))
    app.add_handler(CommandHandler("setwelcome", cmd_setwelcome))
    app.add_handler(CommandHandler("resetwelcome", cmd_resetwelcome))
    app.add_handler(CommandHandler("goodbye", cmd_goodbye))
    app.add_handler(CommandHandler("setgoodbye", cmd_setgoodbye))
    app.add_handler(CommandHandler("resetgoodbye", cmd_resetgoodbye))

    # locks
    app.add_handler(CommandHandler("lock", cmd_lock))
    app.add_handler(CommandHandler("unlock", cmd_unlock))
    app.add_handler(CommandHandler("locks", cmd_locks))
    app.add_handler(CommandHandler("locktypes", cmd_locktypes))
    app.add_handler(CommandHandler("allowlist", cmd_allowlist))
    app.add_handler(CommandHandler("rmallowlist", cmd_rmallowlist))

    # blocklist
    app.add_handler(CommandHandler("addblocklist", cmd_addblocklist))
    app.add_handler(CommandHandler("blocklist", cmd_blocklist))
    app.add_handler(CommandHandler("rmblocklist", cmd_rmblocklist))
    app.add_handler(CommandHandler("rmblocklistall", cmd_rmblocklistall))
    app.add_handler(CommandHandler("blocklistmode", cmd_blocklistmode))

    # antiflood
    app.add_handler(CommandHandler("setflood", cmd_setflood))
    app.add_handler(CommandHandler("setfloodmode", cmd_setfloodmode))
    app.add_handler(CommandHandler("flood", cmd_flood))

    # filters
    app.add_handler(CommandHandler("filter", cmd_filter))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("stopall", cmd_stopall))
    app.add_handler(CommandHandler("filters", cmd_filters))

    # purge
    app.add_handler(CommandHandler("del", cmd_del))
    app.add_handler(CommandHandler("purge", cmd_purge))
    app.add_handler(CommandHandler("spurge", cmd_spurge))

    # info
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("info", cmd_info))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("reports", cmd_reports))

    # members join/leave
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBERS, on_left_member))

    # all group messages (must be last)
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, on_group_message))

    return app


async def error_handler(update, context):
    print(f"Error: {context.error}")


if __name__ == "__main__":
    app = build_app()
    app.add_error_handler(error_handler)
    app.run_polling(drop_pending_updates=True)
