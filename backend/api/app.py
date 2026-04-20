import uuid
import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer

from api.schemas import IndexRequest, IndexResponse, QueryRequest, QueryResponse, UserCreate, ConversationOut, MessageOut
from api.auth import get_password_hash, verify_password, get_current_user, create_access_token
from agents.orchestrator import RAGOrchestrator
from database import get_db, engine, Base
from models import IndexTask, DocumentChunk, User, Conversation, Message
from api.celery_worker import process_repo_task

BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "tmp"

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Connecting to database...")

    # Create the database tables
    Base.metadata.create_all(bind=engine)

    yield

    print("Shutting down...")

app = FastAPI(title="Codebase RAG API", lifespan=lifespan)

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
        print(existing_task.status)
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

    print(req.github_url)

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
def query_repo(
    req: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id if current_user else None

    repo_exists = db.execute(
        select(DocumentChunk.id).where(DocumentChunk.repo_name == req.repo_name)).first()

    if not repo_exists:
        raise HTTPException(status_code=404, detail=f"Repo '{req.repo_name}' not indexed yet.")
    
    try:
        answer, cited_chunks = orchestrator.process_query(
            req.query,
            repo_name=req.repo_name,
            db=db,
            conversation_id=req.conversation_id,
            guest_session_id=req.guest_session_id,
            user_id=user_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
    
    return QueryResponse(
        answer=answer,
        repo_name=req.repo_name,
        cited_chunks=cited_chunks
    )

@app.post("/query/stream", response_model=QueryResponse)
def query_repo(
    req: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id if current_user else None

    repo_exists = db.execute(
        select(DocumentChunk.id).where(DocumentChunk.repo_name == req.repo_name)).first()

    if not repo_exists:
        raise HTTPException(status_code=404, detail=f"Repo '{req.repo_name}' not indexed yet.")
    
    def event_generator():
        try:
            for event in orchestrator.process_query(
                req.query,
                repo_name=req.repo_name,
                db=db,
                conversation_id=req.conversation_id,
                guest_session_id=req.guest_session_id,
                user_id=user_id
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

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
    
@app.post("/auth/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.execute(
        select(User).where(User.email == user.email)
    ).scalar_one_or_none()

    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(name=user.name, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Auto login after registration
    access_token = create_access_token(data={"sub": new_user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "name": new_user.name,
            "email": new_user.email
        }
    }

@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(User.email == form_data.username)
    ).scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/conversations", response_model=list[ConversationOut])
def get_conversations(
    guest_session_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetches all conversations for the sidebar. 
    Prioritizes the authenticated user, falls back to the guest session.
    """
    if current_user:
        # Fetch logged-in user's history
        query = select(Conversation).where(
            Conversation.user_id == current_user.id
        ).order_by(Conversation.created_at.desc())
    
    elif guest_session_id:
        # Fetch anonymous guest's history
        query = select(Conversation).where(
            Conversation.guest_session_id == guest_session_id
        ).order_by(Conversation.created_at.desc())
        
    else:
        # No user and no guest ID provided
        return []

    conversations = db.execute(query).scalars().all()
    return conversations

@app.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    guest_session_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conv = db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    ).scalar_one_or_none()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if current_user:
        if conv.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorised")
    else:
        if conv.guest_session_id != guest_session_id:
            raise HTTPException(status_code=403, detail="Not authorised")
        
    db.delete(conv)
    db.commit()

    return {"status": "success", "message": "Conversation deleted"}

@app.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def get_messages(
    conversation_id: str, 
    db: Session = Depends(get_db)
):
    """
    Fetches the chronological message history for a specific chat.
    Includes the cited_chunks JSON so the UI Drawer can rehydrate.
    """

    # Fetch all messages in chronological order
    messages = db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    ).scalars().all()

    return messages

@app.get("/users/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "name": current_user.name,
        "email": current_user.email
    }

