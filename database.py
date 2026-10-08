from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, BigInteger, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()

# PostgreSQL URLs used by Render may start with postgres:// on older setups.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine, expire_on_commit=False)


class Chat(Base):
    __tablename__ = "chats"

    id = Column(BigInteger, primary_key=True)
    title = Column(String(255), default="")
    type = Column(String(20), default="supergroup")

    welcome_enabled = Column(Boolean, default=False)
    welcome_message = Column(Text, default="Welcome {first}!")
    goodbye_enabled = Column(Boolean, default=False)

    captcha_enabled = Column(Boolean, default=False)
    reports_enabled = Column(Boolean, default=True)

    warn_limit = Column(Integer, default=3)
    warn_mode = Column(String(20), default="ban")

    antiflood_limit = Column(Integer, default=5)
    antiflood_mode = Column(String(20), default="ban")

    antiraid_enabled = Column(Boolean, default=False)
    antiraid_time = Column(Integer, default=6)
    antiraid_action_time = Column(Integer, default=1)
    autoantiraid = Column(Integer, default=0)

    clean_service_enabled = Column(Boolean, default=False)
    clean_service_types = Column(Text, default="")
    clean_command_enabled = Column(Boolean, default=False)
    clean_command_types = Column(Text, default="")
    disabled_commands = Column(Text, default="")


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    username = Column(String(100))
    first_name = Column(String(100))


class Warning(Base):
    __tablename__ = "warnings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    reason = Column(String(500))
    warned_by = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)


class ApprovedUser(Base):
    __tablename__ = "approved_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    reason = Column(String(500), default="No reason")
    approved_by = Column(BigInteger)


class BlockList(Base):
    __tablename__ = "blocklist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    trigger = Column(String(255), nullable=False)
    reason = Column(String(500), default="Blacklisted")


class ChatFilter(Base):
    __tablename__ = "chat_filters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    trigger = Column(String(255), nullable=False)
    response = Column(Text, nullable=False)


class ChatLock(Base):
    __tablename__ = "chat_locks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    lock_type = Column(String(50), nullable=False)


class LogChannel(Base):
    __tablename__ = "log_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False, unique=True, index=True)
    channel_id = Column(BigInteger, nullable=False)



Base.metadata.create_all(engine)


def get_session():
    return Session()


def get_chat(session, chat_id, title=None, chat_type=None):
    """Return the stored chat, creating it if this is the first time we see it."""
    chat = session.query(Chat).filter_by(id=chat_id).first()

    if chat is None:
        chat = Chat(
            id=chat_id,
            title=title or "",
            type=chat_type or "supergroup",
        )
        session.add(chat)
        session.commit()
    else:
        changed = False
        if title is not None and chat.title != title:
            chat.title = title
            changed = True
        if chat_type is not None and chat.type != chat_type:
            chat.type = chat_type
            changed = True
        if changed:
            session.commit()

    return chat
