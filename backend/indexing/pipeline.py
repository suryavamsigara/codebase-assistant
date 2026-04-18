import json
import pickle
from pathlib import Path
from indexing.walker import RepoWalker
from indexing.chunker import CodeChunker
from indexing.embeddings import Embedder
from retrieval.hybrid_search import BM25Index

BASE_DIR = Path(__file__).resolve().parent.parent # backend
DB_PATH = BASE_DIR / "db"

class IndexingPipeline:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.walker = None
        self.chunker = CodeChunker()
        self.embedder = None
        self.all_chunks = []
    
    def index_repo(self, repo_path: str, repo_name: str):
        self.walker = RepoWalker(repo_path, repo_name)

        for file_data in self.walker.walk():
            print(f"Processing: {file_data['file_path']}")

            with open(file_data['absolute_path'], 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()

            chunks = self.chunker.chunk_file(
                code=code,
                file_path=file_data['file_path'],
            )

            for chunk in chunks:
                chunk.update({
                    'repo_name': str(file_data['repo_name']),
                })

            self.all_chunks.extend(chunks)

            print(f"  Found {len(chunks)} chunks from this file. Total so far: {len(self.all_chunks)}")
        
        repo_db_path = DB_PATH / repo_name
        repo_db_path.mkdir(parents=True, exist_ok=True)

        print("Saving chunks to disk...")
        with open(repo_db_path / "chunks.json", "w", encoding="utf-8") as f:
            json.dump(self.all_chunks, f)

        self.embedder = Embedder(chunks=self.all_chunks)
        self.embedder.embed_chunks()
        self.embedder.save(repo_db_path) # Saving index.faiss
        # self.embedder.load(DB_PATH)

        print("Saving BM25 index to disk...")
        bm25_index = BM25Index(self.all_chunks)
        with open(repo_db_path / "bm25.pkl", "wb") as f:
            pickle.dump(bm25_index, f)

        print(f"Indexing complete. All data saved to {repo_db_path}")