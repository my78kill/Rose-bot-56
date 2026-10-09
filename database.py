from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, BigInteger, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(BigInteger, primary_key=True)
    title = Column(String(255))
    username = Column(String(100))
    
    # Welcome settings
    welcome_enabled = Column(Boolean, default=False)
    welcome_message = Column(Text, default="Welcome {first}!")
    goodbye_enabled = Column(Boolean, default=False)
    goodbye_message = Column(Text, default="Goodbye {first}!")
    
    # CAPTCHA
    captcha_enabled = Column(Boolean, default=False)
    captcha_mode = Column(String(20), default='button')
    
    # Anti-flood
    antiflood_limit = Column(Integer, default=5)
    antiflood_mode = Column(String(20), default='mute')
    
    # Reports
    reports_enabled = Column(Boolean, default=True)
    
    # Warnings
    warn_limit = Column(Integer, default=3)
    warn_mode = Column(String(20), default='ban')
    
    # Anti-raid
    antiraid_enabled = Column(Boolean, default=False)
    antiraid_time = Column(Integer, default=6)
    antiraid_action_time = Column(Integer, default=1)
    autoantiraid = Column(Integer, default=0)
    
    # Clean settings
    clean_service_enabled = Column(Boolean, default=False)
    clean_service_types = Column(String(500), default='')
    clean_command_enabled = Column(Boolean, default=False)
    clean_command_types = Column(String(500), default='')
    
    # Disabling
    disabled_commands = Column(String(1000), default='')
    disabled_del = Column(Boolean, default=False)
    
    # NEW: Prefix support
    command_prefixes = Column(String(100), default='/')
    
    # NEW: Block bots
    block_bots = Column(Boolean, default=False)
    
    # NEW: Block forward
    block_forward = Column(Boolean, default=False)
    block_forward_mode = Column(String(20), default='delete')
    
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatUser(Base):
    __tablename__ = 'chat_users'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id'))
    user_id = Column(BigInteger, ForeignKey('users.id'))
    is_admin = Column(Boolean, default=False)
    warn_count = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.utcnow)


class ChatLock(Base):
    __tablename__ = 'chat_locks'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id'))
    lock_type = Column(String(50))


class ChatFilter(Base):
    __tablename__ = 'chat_filters'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id'))
    trigger = Column(String(200))
    response = Column(Text)
    is_media = Column(Boolean, default=False)


class BlockList(Base):
    __tablename__ = 'blocklists'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id'))
    trigger = Column(String(200))
    reason = Column(String(500))


class Warning(Base):
    __tablename__ = 'warnings'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger)
    user_id = Column(BigInteger)
    reason = Column(String(500))
    warned_by = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)


class ApprovedUser(Base):
    __tablename__ = 'approved_users'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger)
    user_id = Column(BigInteger)
    reason = Column(String(500))
    approved_by = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)


# NEW: LogChannel table (FIXED)
class LogChannel(Base):
    __tablename__ = 'log_channels'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id'))
    channel_id = Column(BigInteger)
    log_settings = Column(String(500), default='admin,user,automated,reports,settings,other')


# NEW: Role Hierarchy
class UserRole(Base):
    __tablename__ = 'user_roles'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger)
    user_id = Column(BigInteger)
    role = Column(String(50))  # founder, cofounder, admin, moderator, cleaner, muter, helper, free
    assigned_by = Column(BigInteger)
    assigned_at = Column(DateTime, default=datetime.utcnow)


# NEW: Global Mute (Hidden feature)
class GlobalMute(Base):
    __tablename__ = 'global_mutes'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    reason = Column(String(500))
    muted_by = Column(BigInteger)
    muted_at = Column(DateTime, default=datetime.utcnow)


# Create all tables
Base.metadata.create_all(engine)


def get_session():
    """Get database session"""
    return Session()


def get_chat(session, chat_id):
    """Get or create chat"""
    chat = session.query(Chat).filter_by(id=chat_id).first()
    if not chat:
        chat = Chat(id=chat_id)
        session.add(chat)
        session.commit()
    return chat
