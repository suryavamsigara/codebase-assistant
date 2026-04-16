from fastapi import FastAPI, HTTPException
from pathlib import Path
import subprocess

from api.schemas import IndexRequest, IndexResponse, QueryRequest, QueryResponse
from indexing.pipeline import IndexingPipeline
from retrieval.hybrid_search import HybridRetriever, BM25Index
from agents.orchestrator import RAGOrchestrator
from agents.answer_agent import AnswerAgent

app = FastAPI(title="Codebase RAG API")

BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "tmp"
TEMP_DIR.mkdir(exist_ok=True)

orchestrators: dict[str, RAGOrchestrator] = {}

def clone_repo(github_url: str, repo_name: str) -> Path:
    """Clone a Github repository to a temporary directory"""
    repo_path = TEMP_DIR / repo_name

    if repo_path.exists():
        print(f"Repo already exists at {repo_path}")
        return repo_path
    
    print(f"Cloning {github_url} to {repo_path}")
    subprocess.run(
        ["git", "clone", github_url, str(repo_path)],
        check=True,
        capture_output=True
    )
    print("Clone complete")
    return repo_path

@app.post("/index", response_model=IndexResponse)
def index_repo(req: IndexRequest):
    try:
        repo_path = clone_repo(req.github_url, req.repo_name)

        pipeline = IndexingPipeline(model_name="BAAI/bge-small-en-v1.5")
        pipeline.index_repo(
            repo_path=str(repo_path),
            repo_name=req.repo_name
        )

        bm25_index = BM25Index(pipeline.all_chunks)
        hybrid_retriever = HybridRetriever(
            vector_index=pipeline.embedder,
            bm25_index=bm25_index
        )
        answer_agent = AnswerAgent()
        orchestrator = RAGOrchestrator(
            chunks=pipeline.all_chunks,
            hybrid_retriever=hybrid_retriever,
            answer_agent=answer_agent
        )

        orchestrators[req.repo_name] = orchestrator

        return IndexResponse(
            repo_name=req.repo_name,
            chunk_count=len(pipeline.all_chunks),
            message="Indexed Successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
def query_repo(req: QueryRequest):
    orchestrator = orchestrators.get(req.repo_name)
    
    if not orchestrator:
        raise HTTPException(status_code=404, detail=f"Repo '{req.repo_name}' not indexed yet.")
    
    answer = orchestrator.process_query(req.query)
    return QueryResponse(
        answer=answer,
        repo_name=req.repo_name
    )

@app.get("/repos")
def list_repos():
    return {"repos": list(orchestrators.keys())}
