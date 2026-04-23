import time
from pathlib import Path
from sentence_transformers import SentenceTransformer
from transformers import logging
import faiss
from logger import logger

logging.set_verbosity_error()

class Embedder:
    def __init__(self, model_name:str="BAAI/bge-small-en-v1.5", chunks: list[dict]=None):
        self.embeddings = None
        self.model = SentenceTransformer(model_name)
        self.chunks = chunks

    def create_contextual_header(self, chunk: dict) -> str:
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
        if not self.chunks:
            logger.warning("Embedder called with an empty list of chunks.")
            return
        
        logger.info(f"Generating embeddings for {len(self.chunks)} chunks...")
        start_time = time.time()

        texts_to_embed = [self.create_contextual_header(chunk) for chunk in self.chunks]

        try:
            self.embeddings = self.model.encode(texts_to_embed, show_progress_bar=False)
            duration = time.time() - start_time
            logger.info(f"Successfully generated {self.embeddings.shape} embeddings in {duration:.2f}s")
        except Exception as e:
            logger.error(f"Embedding process failed: {str(e)}", exc_info=True)
