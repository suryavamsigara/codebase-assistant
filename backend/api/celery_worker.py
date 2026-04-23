import subprocess
from pathlib import Path
from celery import Celery
from sqlalchemy import text
from database import SessionLocal
from models import IndexTask, DocumentChunk
from indexing.pipeline import IndexingPipeline
from logger import logger

"""
This worker runs the pipeline, generates the embeddings, saves everything to PostgreSQL, and triggers tsvector generation.
"""

celery_app = Celery(
    "codebase_rag",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "tmp"
TEMP_DIR.mkdir(exist_ok=True)

def clone_repo(github_url: str, repo_name: str) -> Path:
    """Clone a Github repository to a temporary directory"""
    repo_path = TEMP_DIR / repo_name

    if repo_path.exists():
        logger.info(f"Repo {repo_name} already exists. Skipping clone.")
        return repo_path
    
    logger.info(f"Cloning {github_url}...")

    try:
        subprocess.run(
            ["git", "clone", github_url, str(repo_path)],
            check=True,
            capture_output=True
        )
        logger.info(f"Successfully cloned {repo_name}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Git clone failed for {repo_name}: {e.stderr.decode()}")
        raise e
    return repo_path

@celery_app.task(bind=True)
def process_repo_task(self, task_id: str, github_url: str, repo_name: str):
    db = SessionLocal()
    task = db.query(IndexTask).filter(IndexTask.id == task_id).first()

    if not task:
        db.close()
        return
    
    task.status = "PROCESSING"
    db.commit()

    try:
        repo_path = clone_repo(github_url, repo_name)

        pipeline = IndexingPipeline(model_name="BAAI/bge-small-en-v1.5")
        pipeline.index_repo(
            repo_path=str(repo_path),
            repo_name=repo_name
        )

        # Save to database
        db_chunks = []
        for i, chunk in enumerate(pipeline.all_chunks):
            code_content = chunk.get('code', '')
            if chunk.get('type') == 'class' and not code_content:
                code_content = f"Methods: {', '.join(chunk.get('methods', []))}"
            
            db_chunks.append(
                DocumentChunk(
                    repo_name=repo_name,
                    file_path=chunk['file_path'],
                    start_line=chunk['start_line'],
                    end_line=chunk['end_line'],
                    chunk_type=chunk['type'],
                    language=chunk.get('language', 'unknown'),
                    name=chunk.get('name'),
                    parent_class=chunk.get('parent_class'),
                    docstring=chunk.get('docstring'),
                    content=code_content,
                    metadata_json={'methods': chunk.get('methods')} if chunk.get('methods') else None,
                    embedding=pipeline.embedder.embeddings[i].tolist()
                )
            )

        logger.info(f"Bulk saving {len(pipeline.all_chunks)} chunks to Postgres...")
        db.bulk_save_objects(db_chunks)
        db.commit()

        logger.info("Generating SQL tsvectors for keyword search...")
        db.execute(
            text("""
            UPDATE document_chunks
            SET search_tokens = to_tsvector('english',
                    COALESCE(name, '') || ' ' ||
                    COALESCE(docstring, '') || ' ' ||
                    COALESCE(content, '')
            )
            WHERE repo_name = :repo_name AND search_tokens IS NULL
            """),
            {"repo_name": repo_name}
        )
        db.commit()

        logger.info(f"Task {task_id} COMPLETED for {repo_name}")
        task.status = "COMPLETED"
        db.commit()

    except Exception as e:
        logger.error(f"Task {task_id} FAILED: {str(e)}", exc_info=True)
        task.status = "FAILED"
        db.commit()
    finally:
        db.close()
