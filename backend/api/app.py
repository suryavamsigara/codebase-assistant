import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select
from sentence_transformers import SentenceTransformer

from api.schemas import IndexRequest, IndexResponse, QueryRequest, QueryResponse
from agents.orchestrator import RAGOrchestrator
from database import get_db, engine, Base
from models import IndexTask, DocumentChunk
from api.celery_worker import process_repo_task

BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "tmp"

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Codebase RAG API")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Loading Embedding Model...")
embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")

# Initialize stateless orchestrator
orchestrator = RAGOrchestrator(embedding_model=embedding_model)

@app.post("/index", status_code=202)
def index_repo(req: IndexRequest, db: Session = Depends(get_db)):
    existing_task = db.execute(
        select(IndexTask).where(
            IndexTask.repo_name == req.repo_name,
            IndexTask.status.in_(["COMPLETED", "PENDING", "PROCESSING"])
        )
    ).scalars().first()

    if existing_task:
        if existing_task.status == "COMPLETED":
            return {
                "task_id": existing_task.id,
                "repo_name": existing_task.repo_name,
                "message": "Repo is already indexed."
            }
        else:
            return {
                "task_id": existing_task.id,
                "repo_name": existing_task.repo_name,
                "message": "Repo is currently being indexed."
            }

    task_id = str(uuid.uuid4())

    new_task = IndexTask(id=task_id, repo_name=req.repo_name, status="PENDING")
    db.add(new_task)
    db.commit()

    process_repo_task.delay(task_id, req.github_url, req.repo_name)

    return {
        "task_id": task_id,
        "repo_name": req.repo_name,
        "message": "Indexing started in background."
    }

@app.get("/index/status/{task_id}")
def check_index_status(task_id: str, db: Session = Depends(get_db)):
    task = db.execute(
        select(IndexTask).where(IndexTask.id == task_id)
    ).scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    
    return {
        "task_id": task_id,
        "status": task.status
    }

@app.post("/query", response_model=QueryResponse)
def query_repo(req: QueryRequest, db: Session = Depends(get_db)):

    repo_exists = db.execute(
        select(DocumentChunk.id).where(DocumentChunk.repo_name == req.repo_name)).first()

    if not repo_exists:
        raise HTTPException(status_code=404, detail=f"Repo '{req.repo_name}' not indexed yet.")
    
    try:
        answer, cited_chunks = orchestrator.process_query(
            req.query,
            repo_name=req.repo_name,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
    
    return QueryResponse(
        answer=answer,
        repo_name=req.repo_name,
        cited_chunks=cited_chunks
    )

@app.get("/repos")
def list_repos(db: Session = Depends(get_db)):
    repos = db.execute(
        select(IndexTask.repo_name).distinct()
    ).scalars().all()

    return {"repos": repos}

@app.get("/file")
def get_full_file(repo_name: str, file_path: str):
    """
    Fetches the full raw text of a file from the cloned repository.
    Used by the frontend to display the complete file context.
    """
    # Construct the path to where the celery worker cloned the repo
    target_file = TEMP_DIR / repo_name / file_path
    
    if not target_file.exists():
        raise HTTPException(status_code=404, detail="File not found in the cloned repository.")
        
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        return {
            "repo_name": repo_name,
            "file_path": file_path,
            "content": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read file: {str(e)}")