from pathlib import Path
from indexing.pipeline import IndexingPipeline

# walker = RepoWalker("tmp/r1", "r1")
# chunker = CodeChunker()

BASE_DIR = Path(__file__).resolve().parent
TEMP_REPO_PATH = BASE_DIR / "tmp" / "r1"


def main():
    pipeline = IndexingPipeline(model_name="BAAI/bge-small-en-v1.5")

    pipeline.index_repo(
        repo_path=str(TEMP_REPO_PATH),
        repo_name="r1"
    )

if __name__ == "__main__":
    main()
