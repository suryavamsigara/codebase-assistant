from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class IndexRequest(BaseModel):
    github_url: str
    repo_name: str

class IndexResponse(BaseModel):
    repo_name: str
    chunk_count: int
    message: str

class QueryRequest(BaseModel):
    query: str
    repo_name: str
    conversation_id: str
    guest_session_id: Optional[str] = None

class CitedChunk(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    type: Optional[str] = None
    name: Optional[str] = None
    language: str
    code: str

class QueryResponse(BaseModel):
    answer: str
    repo_name: str
    cited_chunks: list[CitedChunk]

class ConversationOut(BaseModel):
    id: str
    name: str
    repo_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    cited_chunks: Optional[list[Any]] = []
    created_at: datetime
    
    class Config:
        from_attributes = True