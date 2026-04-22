import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from api.auth import get_current_user
from api.schemas import QueryRequest, QueryResponse
from models import User, DocumentChunk
from api.dependencies import get_orchestrator
from logger import logger
from api.limiter import limiter

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMP_DIR = BASE_DIR / "tmp"

router = APIRouter(prefix="/query", tags=["query"])

@router.post("/stream", response_model=QueryResponse)
@limiter.limit("6/minute")
def query_repo(
    request: Request,
    req: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    orchestrator = Depends(get_orchestrator)
):
    user_id = current_user.id if current_user else None

    logger.info(
        f"Query Request Received | Repo: '{req.repo_name}' | "
        f"Conv_ID: {req.conversation_id} | User: {user_id or 'Guest'}"
    )

    repo_exists = db.execute(
        select(DocumentChunk.id).where(DocumentChunk.repo_name == req.repo_name)).first()

    if not repo_exists:
        logger.warning(f"Query Rejected: Repo '{req.repo_name}' is not indexed.")
        raise HTTPException(status_code=404, detail=f"Repo '{req.repo_name}' not indexed yet.")
    
    def event_generator():
        logger.info(f"Starting SSE stream for Conv_ID: {req.conversation_id}")
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
            
            logger.info(f"Stream successfully completed for Conv_ID: {req.conversation_id}")
        except Exception as e:
            logger.error(f"Stream crashed for Conv_ID: {req.conversation_id}. Error: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/file")
def get_full_file(repo_name: str, file_path: str):
    """
    Fetches the full raw text of a file from the cloned repository.
    Used by the frontend to display the complete file context.
    """
    # Construct the path to where the celery worker cloned the repo
    target_file = TEMP_DIR / repo_name / file_path

    logger.info(f"File access requested: {repo_name}/{file_path}")
    
    if not target_file.exists():
        logger.warning(f"File not found on disk: {target_file}")
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
        logger.error(f"Unexpected error reading {file_path}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error reading the file.")
    




# ========================== OLD ===============================
@router.post("/", response_model=QueryResponse)
def query_repo(
    req: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    orchestrator = Depends(get_orchestrator)
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