import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import IndexTask
from api.schemas import IndexRequest
from api.celery_worker import process_repo_task

router = APIRouter(prefix="/index", tags=["index"])

@router.post("/", status_code=202)
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
        "repo_name": req.repo_name.lower().strip(),
        "message": "Indexing started in background."
    }

@router.get("/status/{task_id}")
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

@router.get("/repos")
def list_repos(db: Session = Depends(get_db)):
    repos = db.execute(
        select(IndexTask.repo_name).distinct()
    ).scalars().all()

    return {"repos": repos}