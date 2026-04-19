import json
from pathlib import Path
from indexing.walker import RepoWalker
from indexing.chunker import CodeChunker
from indexing.embeddings import Embedder

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

        self.embedder = Embedder(chunks=self.all_chunks)
        self.embedder.embed_chunks()

        print(f"Indexing complete.")