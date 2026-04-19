import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import TSVECTOR
from pgvector.sqlalchemy import Vector

from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True) # null if guest
    guest_session_id = Column(String, index=True, nullable=True) # Local storage ID
    repo_name = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"))
    role = Column(String) # user / ai
    content = Column(String)
    cited_chunks = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class IndexTask(Base):
    __tablename__ = "index_tasks"
    id = Column(String, primary_key=True, index=True)
    repo_name = Column(String, index=True)
    status = Column(String, default="PENDING")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_name = Column(String, index=True)

    # Metadata from chunks
    file_path = Column(String)
    start_line = Column(Integer)
    end_line = Column(Integer)
    chunk_type = Column(String)
    language = Column(String)
    name = Column(String)
    docstring = Column(String, nullable=True)
    content = Column(String) # Code body
    parent_class = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True) # methods array for classes

    # Vector search
    embedding = Column(Vector(384))

    # Keyword search (BM25)
    search_tokens = Column(TSVECTOR)
    