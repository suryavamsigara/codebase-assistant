import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import IndexTask
from api.schemas import IndexRequest
from api.celery_worker import process_repo_task
from logger import logger
from api.limiter import limiter
from api.utils import get_github_repo_stats, sanitize_github_url

router = APIRouter(prefix="/index", tags=["index"])

MAX_REPO_SIZE_KB = 20000

@router.post("/", status_code=202)
@limiter.limit("3/minute") # 3 indexes per minute per IP
def index_repo(request: Request, req: IndexRequest, db: Session = Depends(get_db)):
    clean_url = sanitize_github_url(req.github_url)

    if not clean_url:
        logger.warning(f"Rejected invalid GitHub URL from user: {req.github_url}")
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub URL. Must be a valid public github.com repository."
        )
    
    size_kb, eta_seconds = get_github_repo_stats(clean_url)

    if size_kb == -1:
        logger.warning(f"Rejected {req.repo_name}: Repository not found or is private.")
        raise HTTPException(
            status_code=404, 
            detail="Repository not found. Please ensure the URL is correct and the repository is public."
        )

    if size_kb > MAX_REPO_SIZE_KB:
        logger.warning(f"Rejected {req.repo_name}: Size: {size_kb}KB exceeds limit.")
        raise HTTPException(
            status_code=400,
            detail=f"Repository is too large ({size_kb / 1024:.1f} MB). The maximum allowed size is {MAX_REPO_SIZE_KB / 1024:.1f} MB"
        )

    logger.info(f"Indexing request received for repo: {req.repo_name} ({clean_url})")

    try:
        existing_task = db.execute(
            select(IndexTask).where(
                IndexTask.repo_name == req.repo_name,
                IndexTask.status.in_(["COMPLETED", "PENDING", "PROCESSING"])
            )
        ).scalars().first()

        if existing_task:
            logger.info(f"Duplicate indexing request. Repo {req.repo_name} status: {existing_task.status}")
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

        # sanitize

        logger.info(f"Dispatched background task {task_id} for repo: {req.repo_name}")
        process_repo_task.delay(task_id, clean_url, req.repo_name)

        return {
            "task_id": task_id,
            "repo_name": req.repo_name.lower().strip(),
            "message": "Indexing started in background.",
            "estimated_seconds": eta_seconds
        }
    except Exception as e:
        logger.error(f"Failed to initiate indexing for {req.repo_name}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not start indexing task")

@router.get("/status/{task_id}")
def check_index_status(task_id: str, db: Session = Depends(get_db)):
    task = db.execute(
        select(IndexTask).where(IndexTask.id == task_id)
    ).scalar_one_or_none()

    if not task:
        logger.warning(f"Status check failed: Task ID {task_id} not found")
        raise HTTPException(status_code=404, detail="Task not found.")
    
    return {
        "task_id": task_id,
        "status": task.status
    }

@router.get("/repos")
def list_repos(db: Session = Depends(get_db)):
    logger.info("Fetching list of all indexed repositories")
    repos = db.execute(
        select(IndexTask.repo_name).distinct()
    ).scalars().all()

    return {"repos": repos}