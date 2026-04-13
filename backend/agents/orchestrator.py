from retrieval.hybrid_search import HybridRetriever, BM25Index

class RAGOrchestrator:
    def __init__(self, chunks, hybrid_retriever):
        self.chunks = chunks
        self.retriever = hybrid_retriever
    
    def process_query(self, query: str):

        results = self.retriever.search(query, 3)

        for idx, score in results:
            chunk = self.chunks[idx]
            print(chunk, score)
        
        return results