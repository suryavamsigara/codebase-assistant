from pydantic import BaseModel

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

class QueryResponse(BaseModel):
    answer: str
    repo_name: str