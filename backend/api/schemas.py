from pydantic import BaseModel
from typing import Optional

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