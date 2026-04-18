import uuid
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from sentence_transformers import SentenceTransformer

from api.schemas import IndexRequest, IndexResponse, QueryRequest, QueryResponse
from agents.orchestrator import RAGOrchestrator
from database import get_db, engine, Base
from models import IndexTask, DocumentChunk
from api.celery_worker import process_repo_task

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Codebase RAG API")

print("Loading Embedding Model...")
embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")

# Initialize stateless orchestrator
orchestrator = RAGOrchestrator(embedding_model=embedding_model)

@app.post("/index", status_code=202)
def index_repo(req: IndexRequest, db: Session = Depends(get_db)):
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
    # task = db.query(IndexTask).filter(IndexTask.id == task_id).first()
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
        answer = orchestrator.process_query(
            req.query,
            repo_name=req.repo_name,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
    
    return QueryResponse(
        answer=answer,
        repo_name=req.repo_name
    )

@app.get("/repos")
def list_repos(db: Session = Depends(get_db)):
    repos = db.execute(
        select(IndexTask.repo_name).distinct()
    ).scalars().all()

    return {"repos": repos}
