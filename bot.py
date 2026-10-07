import os, re, json, html, time, random
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque

from live import keep_alive

from telegram import Update, User, ChatPermissions
from telegram.constants import ParseMode
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          ContextTypes, filters as ptb_filters)

TOKEN = os.environ.get("BOT_TOKEN", "PASTE_YOUR_TOKEN_HERE")
DB_DIR = "data"
ADMIN_CACHE_TTL = 300

LOCK_TYPES = [
    "url", "invitelink", "botlink", "forward", "sticker", "photo", "video",
    "videonote", "voice", "audio", "document", "gif", "album", "poll",
    "contact", "location", "command", "bot", "anonchannel", "all",
]

DEFAULT_DATA = {
    "welcome_on": True, "welcome": "", "goodbye_on": False, "goodbye": "",
    "rules": "", "cleanservice": False,
    "warn_limit": 3, "warn_mode": ("ban", 0), "warn_time": 0,
    "warns": {}, "locks": [], "lockwarns": False, "allowlist": [],
    "blocklist": {}, "blocklist_mode": ("delete", 0),
    "flood_limit": 0, "flood_mode": ("mute", 0),
    "filters": {}, "reports": True,
}


# ---------------- storage ----------------

class Store:
    def __init__(self):
        os.makedirs(DB_DIR, exist_ok=True)
        self.data = {}

    def _path(self, chat_id):
        return os.path.join(DB_DIR, f"{chat_id}.json")

    def get(self, chat_id):
        if chat_id not in self.data:
            if os.path.exists(self._path(chat_id)):
                try:
                    with open(self._path(chat_id)) as f:
                        raw = json.load(f)
                    # tuples come back as lists from JSON
                    if isinstance(raw.get("warn_mode"), list):
                        raw["warn_mode"] = tuple(raw["warn_mode"])
                    if isinstance(raw.get("blocklist_mode"), list):
                        raw["blocklist_mode"] = tuple(raw["blocklist_mode"])
                    if isinstance(raw.get("flood_mode"), list):
                        raw["flood_mode"] = tuple(raw["flood_mode"])
                    self.data[chat_id] = raw
                except Exception:
                    self.data[chat_id] = {}
            else:
                self.data[chat_id] = {}
        for k, v in DEFAULT_DATA.items():
            self.data[chat_id].setdefault(k, v)
        return self.data[chat_id]

    def save(self, chat_id):
        with open(self._path(chat_id), "w") as f:
            json.dump(self.data[chat_id], f)


store = Store()
_admin_cache = {}
_flood_track = defaultdict(lambda: deque(maxlen=50))


# ---------------- helpers ----------------

def parse_duration(text):
    m = re.fullmatch(r"(\d+)([mhdw])", (text or "").strip().lower())
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    return n * {"m": 60, "h": 3600, "d": 86400, "w": 604800}[unit]


def mention(user):
    if getattr(user, "username", None):
        return f"@{user.username}"
    name = html.escape(getattr(user, "first_name", "") or str(user.id))
    return f'<a href="tg://user?id={user.id}">{name}</a>'


def name_user(user):
    return mention(user) + f" [<code>{user.id}</code>]"


async def get_admin_ids(context, chat_id):
    now = time.time()
    cached = _admin_cache.get(chat_id)
    if cached and now - cached[1] < ADMIN_CACHE_TTL:
        return cached[0]
    admins = await context.bot.get_chat_administrators(chat_id)
    ids = {a.user.id for a in admins}
    _admin_cache[chat_id] = (ids, now)
    return ids


async def is_admin(context, chat_id, user_id):
    return user_id in await get_admin_ids(context, chat_id)


async def get_target(update, context):
    msg = update.effective_message
    if msg and msg.reply_to_message:
        u = msg.reply_to_message.from_user
        if u and not u.is_bot:
            return u
    if context.args:
        arg = context.args[0]
        if arg.lstrip("-").isdigit():
            return User(id=int(arg), first_name=arg, is_bot=False)
        if arg.startswith("@"):
            try:
                return await context.bot.get_chat(arg)
            except Exception:
                return None
    return None


def msg_type(msg):
    if msg.forward_origin or msg.forward_from or msg.forward_date or msg.forward_sender_name:
        return "forward"
    if msg.photo: return "photo"
    if msg.video: return "video"
    if msg.video_note: return "videonote"
    if msg.sticker: return "sticker"
    if msg.voice: return "voice"
    if msg.audio: return "audio"
    if msg.document:
        if (msg.document.mime_type or "").startswith("image/") and \
           (msg.document.file_name or "").endswith(".gif"):
            return "gif"
        return "document"
    if msg.animation: return "gif"
    if msg.media_group_id: return "album"
    if msg.poll: return "poll"
    if msg.contact: return "contact"
    if msg.location: return "location"
    if msg.text and msg.text.startswith("/"): return "command"
    return None


def url_allowed(text, allowlist):
    if not allowlist:
        return False
    for url in re.findall(r"https?://\S+", text or ""):
        for allowed in allowlist:
            if allowed.lower() in url.lower():
                return True
    return False


def fmt_mode(mode):
    action, dur = mode
    if dur and action.startswith("t"):
        return f"{action} for {dur // 60}m" if dur < 86400 else f"{action} for {dur // 86400}d"
    return action


async def punish(update, context, uid, mode):
    cid = update.effective_chat.id
    action, dur = mode
    try:
        if action == "kick":
            await context.bot.ban_chat_member(cid, uid)
            await context.bot.unban_chat_member(cid, uid)
        elif action == "ban":
            await context.bot.ban_chat_member(cid, uid)
        elif action == "tban":
            until = datetime.now(timezone.utc) + timedelta(seconds=dur)
            await context.bot.ban_chat_member(cid, uid, until_date=until)
        elif action == "mute":
            await context.bot.restrict_chat_member(
                cid, uid, permissions=ChatPermissions(can_send_messages=False))
        elif action == "tmute":
            until = datetime.now(timezone.utc) + timedelta(seconds=dur)
            await context.bot.restrict_chat_member(
                cid, uid, permissions=ChatPermissions(can_send_messages=False),
                until_date=until)
    except Exception as e:
        print(f"punish error: {e}")


def parse_mode_args(args, default_action="ban"):
    if not args:
        return (default_action, 0), " ".join(args)
    parts = " ".join(args).split()
    action = parts[0].lower()
    dur = parse_duration(parts[1]) if len(parts) > 1 else 0
    if action.startswith("t") and not dur:
        return None, " ".join(args)
    if action not in ("kick", "ban", "tban", "mute", "tmute", "delete"):
        return None, " ".join(args)
    return (action, dur or 0), " ".join(args)


# ---------------- basic ----------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "👋 I'm Rose-Lite, a group management bot.\n"
        "Add me to your group and make me admin.\n"
        "Type /help for the full command list.")

HELP = """<b>Rose-Lite Commands</b>

<b>Admin:</b>
/promote, /demote, /title, /adminlist, /admincache

<b>Moderation:</b>
/ban, /sban, /tban 3d, /unban, /kick, /skick, /kickme
/mute, /smute, /tmute 2h, /unmute, /mutehour, /muteweek

<b>Warnings:</b>
/warn, /dwarn, /swarn, /warns, /rmwarn, /resetwarn
/setwarnlimit 3, /setwarnmode ban|kick|mute|tmute 1d, /setwarntime 30d, /warnings

<b>Welcome / Goodbye:</b>
/welcome on|off, /setwelcome, /resetwelcome
/goodbye on|off, /setgoodbye, /resetgoodbye, /cleanservice on|off

<b>Locks:</b>
/lock url, /unlock url, /locks, /locktypes
/lockwarns on|off, /allowlist, /rmallowlist, /rmallowlistall

<b>Blocklist:</b>
/addblocklist word reason, /blocklist, /rmblocklist, /rmblocklistall
/blocklistmode delete|kick|ban|mute|tmute 5d

<b>Antiflood:</b>
/setflood 10, /setfloodmode mute|kick|ban|tmute 1h, /flood

<b>Filters (auto-reply):</b>
/filter word reply, /stop word, /stopall, /filters

<b>Cleanup:</b>
/del, /purge, /spurge, /purge 10

<b>Rules &amp; Pins:</b>
/setrules, /rules, /clearrules
/pin, /permapin, /unpin, /unpinall

<b>Reports &amp; Info:</b>
/reports on|off, /report, /id, /info, /settings, /help"""


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(HELP, parse_mode=ParseMode.HTML)


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cd = store.get(update.effective_chat.id)
    txt = (f"<b>Settings</b>\n"
           f"Welcome: {'on' if cd['welcome_on'] else 'off'}\n"
           f"Goodbye: {'on' if cd['goodbye_on'] else 'off'}\n"
           f"Warnings: limit {cd['warn_limit']}, mode {fmt_mode(cd['warn_mode'])}\n"
           f"Locks: {', '.join(cd['locks']) or 'none'}\n"
           f"Blocklist: {len(cd['blocklist'])} entries, mode {fmt_mode(cd['blocklist_mode'])}\n"
           f"Antiflood: {cd['flood_limit'] or 'off'}, mode {fmt_mode(cd['flood_mode'])}\n"
           f"Filters: {len(cd['filters'])}\n"
           f"Reports: {'on' if cd['reports'] else 'off'}")
    await update.effective_message.reply_text(txt)


async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.effective_message.reply_text(
        f"Your ID: <code>{u.id}</code>\nChat ID: <code>{update.effective_chat.id}</code>")


async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target(update, context)
    if not target:
        return await update.effective_message.reply_text("Reply to a user or give an ID.")
    cd = store.get(update.effective_chat.id)
    warns = cd["warns"].get(str(target.id), [])
    await update.effective_message.reply_text(
        f"<b>User info</b>\nName: {name_user(target)}\n"
        f"Username: @{target.username if target.username else 'none'}\n"
        f"Warnings here: {len(warns)}")


# ---------------- admin management ----------------

async def cmd_promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target(update, context)
    if not target:
        return await update.effective_message.reply_text("Reply to a user or give an ID/username.")
    try:
        await context.bot.promote_chat_member(
            update.effective_chat.id, target.id,
            can_delete_messages=True, can_restrict_members=True)
        title = " ".join(context.args[1:]) if context.args and context.args[0].startswith("@") else " ".join(context.args)
        if title and not title.lstrip("-").isdigit() and not title.startswith("@"):
            try:
                await context.bot.set_chat_administrator_custom_title(
                    update.effective_chat.id, target.id, title[:16])
            except Exception:
                pass
        await update.effective_message.reply_text(f"✅ Promoted {mention(target)}.")
    except Exception as e:
        await update.effective_message.reply_text(f"Failed: {e}")


async def cmd_demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target(update, context)
    if not target:
        return await update.effective_message.reply_text("Reply to a user or give an ID/username.")
    try:
        await context.bot.promote_chat_member(
            update.effective_chat.id, target.id,
            can_delete_messages=False, can_restrict_messages=False,
            can_promote_members=False, can_change_info=False,
            can_invite_users=False, can_pin_messages=False,
            can_delete_messages=False, can_restrict_members=False)
        await update.effective_message.reply_text(f"✅ Demoted {mention(target)}.")
    except Exception as e:
        await update.effective_message.reply_text(f"Failed: {e}")


async def cmd_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target(update, context)
    title = " ".join(context.args[1:]) if context.args and context.args[0].startswith("@") else " ".join(context.args)
    if not target or not title:
        return await update.effective_message.reply_text("Reply to an admin and give a title: /title Moderator")
    await context.bot.set_chat_administrator_custom_title(
        update.effective_chat.id, target.id, title[:16])
    await update.effective_message.reply_text(f"✅ Title set: {html.escape(title[:16])}")


async def cmd_adminlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    lines = [f"• {mention(a.user)}" for a in admins]
    await update.effective_message.reply_text("<b>Admins:</b>\n" + "\n".join(lines))


async def cmd_admincache(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _admin_cache.pop(update.effective_chat.id, None)
    await update.effective_message.reply_text("Admin cache refreshed.")


# ---------------- ban / kick / mute ----------------

async def do_ban(update, context, silent=False):
    target = await get_target(update, context)
    if not target:
        return await update.effective_message.reply_text("Reply to a user or give an ID/username.")
    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    if not silent:
        await update.effective_message.reply_text(f"🔨 Banned {mention(target)}.")


async def do_kick(update, context, silent=False):
    target = await get_target(update, context)
    if not target:
        return await update.effective_message.reply_text("Reply to a user or give an ID/username.")
    cid = update.effective_chat.id
    await context.bot.ban_chat_member(cid, target.id)
    await context.bot.unban_chat_member(cid, target.id)
    if not silent:
        await update.effective_message.reply_text(f"👟 Kicked {mention(target)}.")


async def do_mute(update, context, dur=0, silent=False):
    target = await get_target(update, context)
    if not target:
        return await update.effective_message.reply_text("Reply to a user or give an ID/username.")
    kwargs = {"permissions": ChatPermissions(can_send_messages=False)}
    if dur:
        kwargs["until_date"] = datetime.now(timezone.utc) + timedelta(seconds=dur)
    await context.bot.restrict_chat_member(update.effective_chat.id, target.id, **kwargs)
    if not silent:
        t = f" for {dur // 60}m" if dur else ""
        await update.effective_message.reply_text(f"🔇 Muted {mention(target)}{t}.")


async def do_unban(update, context):
    target = await get_target(update, context)
    if target:
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.effective_message.reply_text(f"✅ Unbanned {mention(target)}.")


async def do_unmute(update, context):
    target = await get_target(update, context)
    if target:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, target.id,
            permissions=ChatPermissions.can_send_messages)
        await update.effective_message.reply_text(f"🔊 Unmuted {mention(target)}.")


async def cmd_ban(update, context): await do_ban(update, context)
async def cmd_sban(update, context): await do_ban(update, context, silent=True)

async def cmd_tban(update, context):
    dur = parse_duration(context.args[1] if len(context.args) > 1 else context.args[0] if context.args and not context.args[0].startswith("@") else "")
    target = await get_target(update, context)
    if not target or not dur:
        return await update.effective_message.reply_text("Usage: /tban 3d (or reply + /tban 3d)")
    until = datetime.now(timezone.utc) + timedelta(seconds=dur)
    await context.bot.ban_chat_member(update.effective_chat.id, target.id, until_date=until)
    await update.effective_message.reply_text(f"🔨 Banned {mention(target)} for {dur // 3600}h." if dur < 86400 else f"🔨 Banned {mention(target)} for {dur // 86400}d.")


async def cmd_unban(update, context): await do_unban(update, context)
async def cmd_kick(update, context): await do_kick(update, context)
async def cmd_skick(update, context): await do_kick(update, context, silent=True)

async def cmd_kickme(update, context):
    cid, uid = update.effective_chat.id, update.effective_user.id
    if await is_admin(context, cid, uid):
        return await update.effective_message.reply_text("You're an admin, kick yourself 😏")
    await context.bot.ban_chat_member(cid, uid)
    await context.bot.unban_chat_member(cid, uid)


async def cmd_mute(update, context): await do_mute(update, context)
async def cmd_smute(update, context): await do_mute(update, context, silent=True)

async def cmd_tmute(update, context):
    dur = parse_duration(context.args[1] if len(context.args) > 1 else context.args[0] if context.args and not context.args[0].startswith("@") else "")
    target = await get_target(update, context)
    if not target or not dur:
        return await update.effective_message.reply_text("Usage: /tmute 2h (or reply + /tmute 2h)")
    await do_mute(update, context, dur=dur)


async def cmd_unmute(update, context): await do_unmute(update, context)

async def cmd_mutehour(update, context): await do_mute(update, context, dur=3600)
async def cmd_muteweek(update, context): await do_mute(update, context, dur=604800)


# ---------------- warnings ----------------

def get_warns(cd, uid):
    now = time.time()
    entries = [(r, t) for r, t in cd["warns"].get(str(uid), []) if not cd["warn_time"] or now - t < cd["warn_time"]]
    cd["warns"][str(uid)] = entries
    return entries


async def issue_warn(update, context, silent=False, delete=False):
    cd = store.get(update.effective_chat.id)
    target = await get_target(update, context)
    if not target:
        return await update.effective_message.reply_text("Reply to a user or give an ID/username.")
    if await is_admin(context, update.effective_chat.id, target.id):
        return await update.effective_message.reply_text("Can't warn an admin.")
    offset = 1 if (context.args and not update.effective_message.reply_to_message) else 0
    reason = " ".join(context.args[offset:]) or "No reason given"
    cd["warns"].setdefault(str(target.id), []).append((reason, time.time()))
    store.save(update.effective_chat.id)
    if delete:
        try:
            await update.effective_message.reply_to_message.delete()
        except Exception:
            pass
    warns = get_warns(cd, target.id)
    n = len(warns)
    if n >= cd["warn_limit"]:
        cd["warns"][str(target.id)] = []
        store.save(update.effective_chat.id)
        await punish(update, context, target.id, cd["warn_mode"])
        await update.effective_message.reply_text(
            f"⚠️ Final warning! {mention(target)} reached {cd['warn_limit']} warnings "
            f"→ {fmt_mode(cd['warn_mode'])}. Reason: {html.escape(reason)}")
    elif not silent:
        await update.effective_message.reply_text(
            f"⚠️ Warning {n}/{cd['warn_limit']} for {mention(target)}. Reason: {html.escape(reason)}")


async def cmd_warn(update, context): await issue_warn(update, context)
async def cmd_dwarn(update, context): await issue_warn(update, context, delete=True)
async def cmd_swarn(update, context): await issue_warn(update, context, silent=True)


async def cmd_warns(update, context):
    target = await get_target(update, context)
    if not target:
        return await update.effective_message.reply_text("Reply to a user or give an ID.")
    cd = store.get(update.effective_chat.id)
    warns = get_warns(cd, target.id)
    if not warns:
        return await update.effective_message.reply_text(f"{mention(target)} has no warnings. 🎉")
    lines = [f"{i}. {html.escape(r)}" for i, (r, t) in enumerate(warns, 1)]
    await update.effective_message.reply_text(f"<b>Warnings for {mention(target)}:</b>\n" + "\n".join(lines))


async def cmd_rmwarn(update, context):
    target = await get_target(update, context)
    if not target:
        return await update.effective_message.reply_text("Reply to a user or give an ID.")
    cd = store.get(update.effective_chat.id)
    warns = cd["warns"].get(str(target.id), [])
    if warns:
        warns.pop()
        store.save(update.effective_chat.id)
        await update.effective_message.reply_text(f"✅ Last warning removed for {mention(target)}.")
    else:
        await update.effective_message.reply_text("No warnings to remove.")


async def cmd_resetwarn(update, context):
    target = await get_target(update, context)
    if not target:
        return await update.effective_message.reply_text("Reply to a user or give an ID.")
    cd = store.get(update.effective_chat.id)
    cd["warns"][str(target.id)] = []
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text(f"✅ All warnings cleared for {mention(target)}.")


async def cmd_setwarnlimit(update, context):
    if context.args and context.args[0].isdigit():
        cd = store.get(update.effective_chat.id)
        cd["warn_limit"] = int(context.args[0])
        store.save(update.effective_chat.id)
        await update.effective_message.reply_text(f"✅ Warn limit set to {cd['warn_limit']}.")
    else:
        await update.effective_message.reply_text("Usage: /setwarnlimit 3")


async def cmd_setwarnmode(update, context):
    mode, _ = parse_mode_args(context.args)
    if not mode:
        return await update.effective_message.reply_text("Usage: /setwarnmode ban|kick|mute|tban 3d|tmute 1d")
    cd = store.get(update.effective_chat.id)
    cd["warn_mode"] = mode
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text(f"✅ Warn mode: {fmt_mode(mode)}")


async def cmd_setwarntime(update, context):
    cd = store.get(update.effective_chat.id)
    if context.args and context.args[0].lower() == "off":
        cd["warn_time"] = 0
        store.save(update.effective_chat.id)
        return await update.effective_message.reply_text("✅ Warnings never expire.")
    dur = parse_duration(context.args[0] if context.args else "")
    if dur:
        cd["warn_time"] = dur
        store.save(update.effective_chat.id)
        await update.effective_message.reply_text(f"✅ Warnings expire after {dur // 86400}d." if dur >= 86400 else f"✅ Warnings expire after {dur // 3600}h.")
    else:
        await update.effective_message.reply_text("Usage: /setwarntime 30d | /setwarntime off")


async def cmd_warnings(update, context):
    cd = store.get(update.effective_chat.id)
    await update.effective_message.reply_text(
        f"Limit: {cd['warn_limit']}\nMode: {fmt_mode(cd['warn_mode'])}\n"
        f"Expire: {str(cd['warn_time'] // 86400) + 'd' if cd['warn_time'] else 'never'}")


# ---------------- welcome / goodbye ----------------

def format_text(text, user, chat, count=None):
    if count is None:
        try:
            count = 0
        except Exception:
            count = 0
    return (text or "").replace("{first}", user.first_name or "") \
        .replace("{last}", user.last_name or "") \
        .replace("{fullname}", ((user.first_name or "") + " " + (user.last_name or "")).strip()) \
        .replace("{username}", "@" + user.username if user.username else user.first_name or "") \
        .replace("{id}", str(user.id)) \
        .replace("{chatname}", chat.title or "") \
        .replace("{count}", str(count or ""))


async def on_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cd = store.get(update.effective_chat.id)
    chat = update.effective_chat
    for member in update.effective_message.new_chat_members:
        if member.id == context.bot.id:
            await update.effective_message.reply_text(
                "👋 Thanks for adding me! Make me admin so I can manage the group. /help")
            continue
        if cd["cleanservice"]:
            try:
                await update.effective_message.delete()
            except Exception:
                pass
        if cd["welcome_on"] and cd["welcome"]:
            try:
                count = await context.bot.get_chat_member_count(chat.id)
            except Exception:
                count = 0
            await context.bot.send_message(chat.id, format_text(cd["welcome"], member, chat, count))


async def on_left_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cd = store.get(update.effective_chat.id)
    if cd["cleanservice"]:
        try:
            await update.effective_message.delete()
        except Exception:
            pass
    member = update.effective_message.left_chat_member
    if cd["goodbye_on"] and cd["goodbye"] and member and member.id != context.bot.id:
        await context.bot.send_message(update.effective_chat.id, format_text(cd["goodbye"], member, update.effective_chat))


async def cmd_welcome(update, context):
    cd = store.get(update.effective_chat.id)
    if context.args and context.args[0].lower() in ("on", "yes", "true"):
        cd["welcome_on"] = True
        store.save(update.effective_chat.id)
        return await update.effective_message.reply_text("✅ Welcome messages on.")
    if context.args and context.args[0].lower() in ("off", "no", "false"):
        cd["welcome_on"] = False
        store.save(update.effective_chat.id)
        return await update.effective_message.reply_text("✅ Welcome messages off.")
    if cd["welcome"]:
        await update.effective_message.reply_text(f"<b>Current welcome:</b>\n{html.escape(cd['welcome'])}")
    else:
        await update.effective_message.reply_text(
            "No welcome set. Use /setwelcome (as reply or with text).\n"
            "Variables: {first} {last} {fullname} {username} {id} {chatname} {count}")


async def cmd_setwelcome(update, context):
    cd = store.get(update.effective_chat.id)
    if update.effective_message.reply_to_message:
        cd["welcome"] = update.effective_message.reply_to_message.text or update.effective_message.reply_to_message.caption or ""
    else:
        cd["welcome"] = " ".join(context.args)
    if not cd["welcome"]:
        return await update.effective_message.reply_text("Give me text or reply to a message.")
    cd["welcome_on"] = True
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text("✅ Welcome message saved and enabled.")


async def cmd_resetwelcome(update, context):
    cd = store.get(update.effective_chat.id)
    cd["welcome"] = ""
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text("✅ Welcome cleared.")


async def cmd_goodbye(update, context):
    cd = store.get(update.effective_chat.id)
    if context.args and context.args[0].lower() in ("on", "yes", "true"):
        cd["goodbye_on"] = True
        store.save(update.effective_chat.id)
        return await update.effective_message.reply_text("✅ Goodbye messages on.")
    if context.args and context.args[0].lower() in ("off", "no", "false"):
        cd["goodbye_on"] = False
        store.save(update.effective_chat.id)
        return await update.effective_message.reply_text("✅ Goodbye messages off.")
    await update.effective_message.reply_text("Usage: /goodbye on|off — then /setgoodbye")


async def cmd_setgoodbye(update, context):
    cd = store.get(update.effective_chat.id)
    if update.effective_message.reply_to_message:
        cd["goodbye"] = update.effective_message.reply_to_message.text or update.effective_message.reply_to_message.caption or ""
    else:
        cd["goodbye"] = " ".join(context.args)
    if not cd["goodbye"]:
        return await update.effective_message.reply_text("Give me text or reply to a message.")
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text("✅ Goodbye message saved.")


async def cmd_resetgoodbye(update, context):
    cd = store.get(update.effective_chat.id)
    cd["goodbye"] = ""
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text("✅ Goodbye cleared.")


async def cmd_cleanservice(update, context):
    if not context.args:
        return await update.effective_message.reply_text("Usage: /cleanservice on|off")
    cd = store.get(update.effective_chat.id)
    cd["cleanservice"] = context.args[0].lower() in ("on", "yes", "true")
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text(f"✅ Clean service messages: {'on' if cd['cleanservice'] else 'off'}")


# ---------------- locks ----------------

async def cmd_lock(update, context):
    if not context.args:
        return await update.effective_message.reply_text("Usage: /lock url (see /locktypes)")
    t = context.args[0].lower()
    cd = store.get(update.effective_chat.id)
    if t == "all":
        cd["locks"] = [x for x in LOCK_TYPES if x != "all"]
    elif t in LOCK_TYPES and t not in cd["locks"]:
        cd["locks"].append(t)
    else:
        return await update.effective_message.reply_text("Unknown or already locked type. See /locktypes")
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text(f"🔒 Locked: {t}")


async def cmd_unlock(update, context):
    if not context.args:
        return await update.effective_message.reply_text("Usage: /unlock url")
    t = context.args[0].lower()
    cd = store.get(update.effective_chat.id)
    if t == "all":
        cd["locks"] = []
    else:
        cd["locks"] = [x for x in cd["locks"] if x != t]
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text(f"🔓 Unlocked: {t}")


async def cmd_locks(update, context):
    cd = store.get(update.effective_chat.id)
    await update.effective_message.reply_text("Active locks: " + (", ".join(cd["locks"]) or "none"))


async def cmd_locktypes(update, context):
    await update.effective_message.reply_text("Lock types:\n" + ", ".join(LOCK_TYPES))


async def cmd_lockwarns(update, context):
    if not context.args:
        return await update.effective_message.reply_text("Usage: /lockwarns on|off")
    cd = store.get(update.effective_chat.id)
    cd["lockwarns"] = context.args[0].lower() in ("on", "yes", "true")
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text(f"✅ Lock warnings: {'on' if cd['lockwarns'] else 'off'}")


async def cmd_allowlist(update, context):
    cd = store.get(update.effective_chat.id)
    if context.args:
        cd["allowlist"].extend(context.args)
        store.save(update.effective_chat.id)
        return await update.effective_message.reply_text(f"✅ Added to allowlist: {', '.join(context.args)}")
    await update.effective_message.reply_text("Allowlist:\n" + ("\n".join(cd["allowlist"]) or "empty"))


async def cmd_rmallowlist(update, context):
    cd = store.get(update.effective_chat.id)
    cd["allowlist"] = [a for a in cd["allowlist"] if a not in context.args]
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text("✅ Removed.")


async def cmd_rmallowlistall(update, context):
    cd = store.get(update.effective_chat.id)
    cd["allowlist"] = []
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text("✅ Allowlist cleared.")


# ---------------- blocklist ----------------

async def cmd_addblocklist(update, context):
    if not context.args:
        return await update.effective_message.reply_text("Usage: /addblocklist word reason (phrases in \"quotes\")")
    cd = store.get(update.effective_chat.id)
    trigger = context.args[0].lower()
    reason = " ".join(context.args[1:]) or "Blocked word"
    cd["blocklist"][trigger] = reason
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text(f"✅ Blocklisted: {html.escape(trigger)}")


async def cmd_blocklist(update, context):
    cd = store.get(update.effective_chat.id)
    if not cd["blocklist"]:
        return await update.effective_message.reply_text("Blocklist is empty.")
    lines = [f"• {html.escape(k)} — {html.escape(v)}" for k, v in cd["blocklist"].items()]
    await update.effective_message.reply_text("<b>Blocklist:</b>\n" + "\n".join(lines))


async def cmd_rmblocklist(update, context):
    cd = store.get(update.effective_chat.id)
    for a in context.args:
        cd["blocklist"].pop(a.lower(), None)
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text("✅ Removed.")


async def cmd_rmblocklistall(update, context):
    cd = store.get(update.effective_chat.id)
    cd["blocklist"] = {}
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text("✅ Blocklist cleared.")


async def cmd_blocklistmode(update, context):
    mode, _ = parse_mode_args(context.args, default_action="delete")
    if not mode:
        return await update.effective_message.reply_text("Usage: /blocklistmode delete|kick|ban|mute|tmute 5d")
    cd = store.get(update.effective_chat.id)
    cd["blocklist_mode"] = mode
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text(f"✅ Blocklist mode: {fmt_mode(mode)}")


# ---------------- antiflood ----------------

async def cmd_setflood(update, context):
    if not context.args or not context.args[0].isdigit():
        return await update.effective_message.reply_text("Usage: /setflood 10 (0 = off)")
    cd = store.get(update.effective_chat.id)
    cd["flood_limit"] = int(context.args[0])
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text(f"✅ Antiflood: {cd['flood_limit'] or 'off'}")


async def cmd_setfloodmode(update, context):
    mode, _ = parse_mode_args(context.args, default_action="mute")
    if not mode:
        return await update.effective_message.reply_text("Usage: /setfloodmode mute|kick|ban|tmute 1h")
    cd = store.get(update.effective_chat.id)
    cd["flood_mode"] = mode
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text(f"✅ Flood mode: {fmt_mode(mode)}")


async def cmd_flood(update, context):
    cd = store.get(update.effective_chat.id)
    await update.effective_message.reply_text(
        f"Antiflood: {cd['flood_limit'] or 'off'} messages\nMode: {fmt_mode(cd['flood_mode'])}")


# ---------------- filters ----------------

async def cmd_filter(update, context):
    if not context.args:
        return await update.effective_message.reply_text('Usage: /filter word reply (or /filter "exact phrase" reply)')
    cd = store.get(update.effective_chat.id)
    if update.effective_message.reply_to_message:
        trigger = " ".join(context.args)
        reply = update.effective_message.reply_to_message.text or update.effective_message.reply_to_message.caption or ""
    else:
        m = re.match(r'^"(.+?)"\s+(.+)$', " ".join(context.args))
        if m:
            trigger, reply = m.group(1), m.group(2)
        else:
            parts = " ".join(context.args).split(None, 1)
            if len(parts) < 2:
                return await update.effective_message.reply_text("Give a trigger and a reply.")
            trigger, reply = parts
    cd["filters"][trigger.lower()] = reply
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text(f"✅ Filter saved for: {html.escape(trigger)}")


async def cmd_stop(update, context):
    cd = store.get(update.effective_chat.id)
    for a in context.args:
        cd["filters"].pop(a.lower(), None)
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text("✅ Filter(s) removed.")


async def cmd_stopall(update, context):
    cd = store.get(update.effective_chat.id)
    cd["filters"] = {}
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text("✅ All filters removed.")


async def cmd_filters(update, context):
    cd = store.get(update.effective_chat.id)
    await update.effective_message.reply_text(
        "Filters:\n" + ("\n".join(html.escape(k) for k in cd["filters"]) or "none"))


# ---------------- purge ----------------

async def cmd_del(update, context):
    msg = update.effective_message
    if msg.reply_to_message:
        try:
            await msg.reply_to_message.delete()
            await msg.delete()
        except Exception as e:
            await msg.reply_text(f"Failed: {e}")


async def do_purge(update, context, silent=False):
    msg = update.effective_message
    chat = update.effective_chat
    ids = []
    if context.args and context.args[0].isdigit():
        count = min(int(context.args[0]), 100)
        mid = msg.message_id
        ids = list(range(max(1, mid - count + 1), mid + 1))
    elif msg.reply_to_message:
        ids = list(range(msg.reply_to_message.message_id, msg.message_id + 1))
    else:
        return await msg.reply_text("Reply to a message to purge from, or use /purge 10")
    if len(ids) > 2 and not silent:
        await msg.reply_text(f"Purging {len(ids)} messages...")
    try:
        await context.bot.delete_messages(chat.id, ids)
    except Exception as e:
        await msg.reply_text(f"Purge failed: {e} (messages older than 48h can't be deleted)")


async def cmd_purge(update, context): await do_purge(update, context)
async def cmd_spurge(update, context): await do_purge(update, context, silent=True)


# ---------------- rules & pins ----------------

async def cmd_setrules(update, context):
    cd = store.get(update.effective_chat.id)
    cd["rules"] = " ".join(context.args)
    if not cd["rules"]:
        return await update.effective_message.reply_text("Give the rules text.")
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text("✅ Rules saved.")


async def cmd_rules(update, context):
    cd = store.get(update.effective_chat.id)
    if cd["rules"]:
        await update.effective_message.reply_text(f"<b>Rules:</b>\n{html.escape(cd['rules'])}")
    else:
        await update.effective_message.reply_text("No rules set. Use /setrules")


async def cmd_clearrules(update, context):
    cd = store.get(update.effective_chat.id)
    cd["rules"] = ""
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text("✅ Rules cleared.")


async def cmd_pin(update, context):
    msg = update.effective_message
    if msg.reply_to_message:
        await context.bot.pin_chat_message(update.effective_chat.id, msg.reply_to_message.message_id)


async def cmd_permapin(update, context):
    text = " ".join(context.args)
    if update.effective_message.reply_to_message:
        text = update.effective_message.reply_to_message.text or ""
    if not text:
        return
    sent = await context.bot.send_message(update.effective_chat.id, text)
    await context.bot.pin_chat_message(update.effective_chat.id, sent.message_id)


async def cmd_unpin(update, context):
    msg = update.effective_message
    if msg.reply_to_message:
        await context.bot.unpin_chat_message(update.effective_chat.id, msg.reply_to_message.message_id)
    else:
        await context.bot.unpin_chat_message(update.effective_chat.id)


async def cmd_unpinall(update, context):
    await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    await update.effective_message.reply_text("✅ All pins removed.")


# ---------------- reports ----------------

async def cmd_reports(update, context):
    if not context.args:
        return await update.effective_message.reply_text("Usage: /reports on|off")
    cd = store.get(update.effective_chat.id)
    cd["reports"] = context.args[0].lower() in ("on", "yes", "true")
    store.save(update.effective_chat.id)
    await update.effective_message.reply_text(f"✅ Reports: {'on' if cd['reports'] else 'off'}")


async def cmd_report(update, context):
    cd = store.get(update.effective_chat.id)
    msg = update.effective_message
    if not cd["reports"] or not msg.reply_to_message:
        return
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    tags = " ".join(mention(a.user) for a in admins if not a.user.is_bot)
    await msg.reply_text(f"⚠️ Reported to admins: {tags}")


# ---------------- message pipeline ----------------

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.from_user or msg.from_user.is_bot:
        return
    chat, user = update.effective_chat, update.effective_user
    if chat.type not in ("group", "supergroup"):
        return
    if await is_admin(context, chat.id, user.id):
        return  # admins are exempt, like Rose

    cd = store.get(chat.id)
    text = msg.text or msg.caption or ""

    # antiflood
    if cd["flood_limit"] > 0:
        key = (chat.id, user.id)
        now = time.time()
        dq = _flood_track[key]
        dq.append(now)
        while dq and now - dq[0] > 10:
            dq.popleft()
        if len(dq) > cd["flood_limit"]:
            dq.clear()
            await punish(update, context, user.id, cd["flood_mode"])
            await msg.reply_text(f"🌊 {mention(user)} flooded → {fmt_mode(cd['flood_mode'])}")
            return

    # locks
    mtype = msg_type(msg)
    if cd["locks"] and (mtype in cd["locks"] or "all" in cd["locks"]):
        if mtype == "url" and url_allowed(text, cd["allowlist"]):
            pass
        else:
            try:
                await msg.delete()
            except Exception:
                pass
            if cd["lockwarns"]:
                cd["warns"].setdefault(str(user.id), []).append(("Lock violation: " + mtype, time.time()))
                store.save(chat.id)
                n = len(get_warns(cd, user.id))
                if n >= cd["warn_limit"]:
                    cd["warns"][str(user.id)] = []
                    store.save(chat.id)
                    await punish(update, context, user.id, cd["warn_mode"])
                else:
                    await context.bot.send_message(chat.id, f"🔒 {mention(user)}, {mtype} is locked here. Warning {n}/{cd['warn_limit']}")
            return

    # blocklist
    low = text.lower()
    for trigger, reason in cd["blocklist"].items():
        if trigger in low:
            try:
                await msg.delete()
            except Exception:
                pass
            await punish(update, context, user.id, cd["blocklist_mode"])
            return

    # filters (auto-reply)
    if cd["filters"]:
        for trigger, reply in cd["filters"].items():
            if trigger.startswith("exact:"):
                if low == trigger[6:]:
                    await msg.reply_text(reply)
                    return
            elif trigger.startswith("prefix:"):
                if low.startswith(trigger[7:]):
                    await msg.reply_text(reply)
                    return
            elif trigger in low:
                await msg.reply_text(reply)
                return


# ---------------- main ----------------

def main():
    keep_alive()  # Flask web server for Render

    app = Application.builder().token(TOKEN).build()

    cmds = [
        ("start", cmd_start), ("help", cmd_help), ("settings", cmd_settings),
        ("id", cmd_id), ("info", cmd_info),
        ("promote", cmd_promote), ("demote", cmd_demote), ("title", cmd_title),
        ("adminlist", cmd_adminlist), ("admincache", cmd_admincache),
        ("ban", cmd_ban), ("sban", cmd_sban), ("tban", cmd_tban), ("unban", cmd_unban),
        ("kick", cmd_kick), ("skick", cmd_skick), ("kickme", cmd_kickme),
        ("mute", cmd_mute), ("smute", cmd_smute), ("tmute", cmd_tmute),
        ("unmute", cmd_unmute), ("mutehour", cmd_mutehour), ("muteweek", cmd_muteweek),
        ("warn", cmd_warn), ("dwarn", cmd_dwarn), ("swarn", cmd_swarn),
        ("warns", cmd_warns), ("rmwarn", cmd_rmwarn), ("resetwarn", cmd_resetwarn),
        ("setwarnlimit", cmd_setwarnlimit), ("setwarnmode", cmd_setwarnmode),
        ("setwarntime", cmd_setwarntime), ("warnings", cmd_warnings),
        ("welcome", cmd_welcome), ("setwelcome", cmd_setwelcome), ("resetwelcome", cmd_resetwelcome),
        ("goodbye", cmd_goodbye), ("setgoodbye", cmd_setgoodbye), ("resetgoodbye", cmd_resetgoodbye),
        ("cleanservice", cmd_cleanservice),
        ("lock", cmd_lock), ("unlock", cmd_unlock), ("locks", cmd_locks),
        ("locktypes", cmd_locktypes), ("lockwarns", cmd_lockwarns),
        ("allowlist", cmd_allowlist), ("rmallowlist", cmd_rmallowlist), ("rmallowlistall", cmd_rmallowlistall),
        ("addblocklist", cmd_addblocklist), ("blocklist", cmd_blocklist),
        ("rmblocklist", cmd_rmblocklist), ("rmblocklistall", cmd_rmblocklistall),
        ("blocklistmode", cmd_blocklistmode),
        ("setflood", cmd_setflood), ("setfloodmode", cmd_setfloodmode), ("flood", cmd_flood),
        ("filter", cmd_filter), ("stop", cmd_stop), ("stopall", cmd_stopall), ("filters", cmd_filters),
        ("del", cmd_del), ("purge", cmd_purge), ("spurge", cmd_spurge),
        ("setrules", cmd_setrules), ("rules", cmd_rules), ("clearrules", cmd_clearrules),
        ("pin", cmd_pin), ("permapin", cmd_permapin), ("unpin", cmd_unpin), ("unpinall", cmd_unpinall),
        ("reports", cmd_reports), ("report", cmd_report),
    ]
    for name, fn in cmds:
        app.add_handler(CommandHandler(name, fn))

    app.add_handler(MessageHandler(ptb_filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_member))
    app.add_handler(MessageHandler(ptb_filters.StatusUpdate.LEFT_CHAT_MEMBER, on_left_member))
    app.add_handler(MessageHandler(ptb_filters.ALL & ~ptb_filters.COMMAND, on_message))

    print("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()