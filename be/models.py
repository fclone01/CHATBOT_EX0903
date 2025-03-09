from fastapi import FastAPI, UploadFile, Form, APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey, SmallInteger, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from uuid import uuid4
from datetime import datetime
import shutil
import os
from sqlalchemy.dialects.postgresql import UUID
import config


Base = declarative_base()
engine = create_engine(config.POSTGRES_URI)

class Chat(Base):
    __tablename__ = "chat"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="chat", cascade="all, delete")
    files = relationship("File", back_populates="chat", cascade="all, delete")

class Message(Base):
    __tablename__ = "message"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chat.id", ondelete="CASCADE"))
    content = Column(Text, nullable=False)
    role = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")
    votes = relationship("Vote", back_populates="message", cascade="all, delete")

class File(Base):
    __tablename__ = "file"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chat.id", ondelete="CASCADE"))
    file_name = Column(Text, nullable=False)
    description = Column(Text, default="")
    embedding_infor = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="files")

class Vote(Base):
    __tablename__ = "vote"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("message.id", ondelete="CASCADE"))
    type = Column(SmallInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("Message", back_populates="votes")

Base.metadata.create_all(bind=engine)
