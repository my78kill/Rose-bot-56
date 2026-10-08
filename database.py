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
    welcome_enabled = Column(Boolean, default=False)
    welcome_message = Column(Text, default="Welcome {first}!")
    goodbye_enabled = Column(Boolean, default=False)
    captcha_enabled = Column(Boolean, default=False)
    antiflood_limit = Column(Integer, default=5)
    reports_enabled = Column(Boolean, default=True)
    warn_limit = Column(Integer, default=3)
    warn_mode = Column(String(20), default='ban')

class User(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True)
    username = Column(String(100))
    first_name = Column(String(100))

class Warning(Base):
    __tablename__ = 'warnings'
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger)
    user_id = Column(BigInteger)
    reason = Column(String(500))
    warned_by = Column(BigInteger)

Base.metadata.create_all(engine)

def get_session():
    return Session()
