import subprocess
from pathlib import Path
from indexing.pipeline import IndexingPipeline
from retrieval.hybrid_search import HybridRetriever, BM25Index
from agents.orchestrator import RAGOrchestrator
from agents.answer_agent import AnswerAgent

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "tmp"
TEMP_DIR.mkdir(exist_ok=True)

TEMP_REPO_PATH = BASE_DIR / "tmp" / "r1"

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

def main():
    github_url = "https://github.com/suryavamsigara/tenxar"
    repo_name = "tenxar"
    repo_path = clone_repo(github_url, repo_name)

    pipeline = IndexingPipeline(model_name="BAAI/bge-small-en-v1.5")

    pipeline.index_repo(
        repo_path=str(repo_path),
        repo_name=repo_name
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

    query = "How backpropagation was implemented? and what neural network layers are there? how does forward pass work?"
    response = orchestrator.process_query(query)
    print(response)

if __name__ == "__main__":
    main()
