from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()
engine = create_engine('sqlite:///psychobot.db')
SessionLocal = sessionmaker(bind=engine)


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)


def init_db():
    Base.metadata.create_all(engine)


def save_message(user_id: int, role: str, content: str):
    session = SessionLocal()
    msg = Message(user_id=user_id, role=role, content=content)
    session.add(msg)
    session.commit()
    session.close()


def get_history(user_id: int, limit: int = 20):
    session = SessionLocal()
    messages = session.query(Message).filter(
        Message.user_id == user_id
    ).order_by(Message.timestamp.desc()).limit(limit).all()
    session.close()
    return list(reversed(messages))


def clear_history(user_id: int):
    session = SessionLocal()
    session.query(Message).filter(Message.user_id == user_id).delete()
    session.commit()
    session.close()