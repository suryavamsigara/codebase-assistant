from pathlib import Path
from indexing.pipeline import IndexingPipeline
from retrieval.hybrid_search import HybridRetriever, BM25Index
from agents.orchestrator import RAGOrchestrator

BASE_DIR = Path(__file__).resolve().parent
TEMP_REPO_PATH = BASE_DIR / "tmp" / "r1"


def main():
    pipeline = IndexingPipeline(model_name="BAAI/bge-small-en-v1.5")

    pipeline.index_repo(
        repo_path=str(TEMP_REPO_PATH),
        repo_name="r1"
    )

    bm25_index = BM25Index(pipeline.all_chunks)

    hybrid_retriever = HybridRetriever(
        vector_index=pipeline.embedder,
        bm25_index=bm25_index
    )

    query = "compute n factorial recursively"

    orchestrator = RAGOrchestrator(
        chunks=pipeline.all_chunks,
        hybrid_retriever=hybrid_retriever
    )

    result = orchestrator.process_query(query)
    print(result)

if __name__ == "__main__":
    main()
