import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Dict

class Embedder:
    def __init__(self, model_name:str="BAAI/bge-small-en-v1.5", chunks: List[Dict]=None):
        self.embeddings = None
        self.index = None
        self.model = SentenceTransformer(model_name)
        self.chunks = chunks

    def create_contextual_header(self, chunk: Dict) -> str:
        header_parts = [
            f"Language: {chunk.get('language', 'unknown')}",
            f"File: {chunk.get('file_path', 'unknown')}",
            f"Type: {chunk.get('type', 'code')}"
        ]

        if chunk.get('name'):
            header_parts.append(f"Name: {chunk['name']}")
        
        if chunk.get('docstring'):
            header_parts.append(f"Purpose: {chunk['docstring'][:200]}")

        if chunk.get('parent_class'):
            header_parts.append(f"Part of class: {chunk['parent_class']}")
        
        header = " | ".join(header_parts)

        if chunk['type'] == 'class':
            return f"""
            This is a {chunk['language']} class named {chunk['name']},
            It contains methods: {', '.join(chunk.get('methods', []))}
            """
        else:
            return f"{header}\n---\n{chunk.get('code', '')}"
    
    def embed_chunks(self):
        print("Embedding chunks")
        texts_to_embed = [self.create_contextual_header(chunk) for chunk in self.chunks]
        # print(texts_to_embed[:3])
        self.embeddings = self.model.encode(texts_to_embed, show_progress_bar=False)
        print("Embeds: ", self.embeddings.shape)

        faiss.normalize_L2(self.embeddings)

        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(self.embeddings)

    def save(self, path):
        """Save index and metadata"""
        print("Saving index")
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path / "index.faiss"))

    def load(self, path):
        print("Loading index")
        path = Path(path)
        self.index = faiss.read_index(str(path / "index.faiss"))
    
    def search(self, query: str, k: int = 1):
        print("Searching query")
        query_embedding = self.model.encode([query]).astype('float32')
        faiss.normalize_L2(query_embedding)

        scores, indices = self.index.search(query_embedding, min(k, len(self.chunks)))

        results = []

        for score, idx in zip(scores[0], indices[0]):
            chunk = self.chunks[idx]

            results.append({
                'rank': len(results) + 1,
                'score': float(score),
                'code': chunk['code'],
                'file_path': chunk['file_path'],
                'start_line': chunk['start_line'],
                'end_line': chunk['end_line'],
                'parent_class': chunk['parent_class'],
                'docstring': chunk['docstring']
            })

            if len(results) >= k:
                break
        
        return results

