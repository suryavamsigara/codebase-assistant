from sqlalchemy import Column, String, Integer, JSON
from sqlalchemy.dialects.postgresql import TSVECTOR
from pgvector.sqlalchemy import Vector

from database import Base

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
    