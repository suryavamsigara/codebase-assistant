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
    
    def index_repo(self, repo_path: str, repo_name: str):
        self.walker = RepoWalker(repo_path, repo_name)

        all_chunks = []

        for file_data in self.walker.walk():
            print(f"Processing: {file_data['file_path']}")

            with open(file_data['absolute_path'], 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()

            chunks = self.chunker.chunk_python(
                code,
                file_data['file_path'])

            for chunk in chunks:
                chunk.update({
                    'repo_name': file_data['repo_name'],
                    'full_file_path': file_data['file_path']
                })

            all_chunks.extend(chunks)

            print(f"  Found {len(chunks)} chunks from this file. Total so far: {len(all_chunks)}")

        embedder = Embedder(chunks=all_chunks)
        embedder.embed_chunks()
        embedder.save(DB_PATH)
        embedder.load(DB_PATH)

        print("======================")
        print(embedder.search("backward propagation for matrix multiplication"))
        print("======================")
        print(embedder.search("to deposit money"))
        print("======================")
        print(embedder.search("How to build computation order?"))
        print("======================")
        print(embedder.search("compute n factorial recursively"))
