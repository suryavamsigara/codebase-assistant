import math
import faiss
from collections import defaultdict

class HybridRetriever:
    def __init__(self, vector_index, bm25_index=None):
        self.vector_index = vector_index
        self.bm25_index = bm25_index
        self.k = 60
    
    def reciprocal_rank_fusion(self, ranked_lists: list[list[tuple[int, float]]]):
        """Combines vector and bm25 search"""
        # RR(d) = sum(1 / (1 + rank(d)))

        rrf_scores = defaultdict(float)
        
        for ranked_list in ranked_lists:
            for rank, (doc_id, _) in enumerate(ranked_list, start=1):
                rrf_scores[doc_id] += 1.0 / (self.k + rank)
        
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [(doc_id, score) for doc_id, score in sorted_docs]

    def search(self, query: str, top_k: int = 10):
        """
        Peforms hybrid search: vector + BM25
        """
        ranked_lists = []

        if self.vector_index:
            vector_search_results = self.vector_search(query, top_k) # list of tuples
            if vector_search_results:
                ranked_lists.append(vector_search_results)
            
        if self.bm25_index:
            bm25_search_results = self.bm25_search(query, top_k) # list of tuples
            if bm25_search_results:
                ranked_lists.append(bm25_search_results)
        
        return ranked_lists

    def vector_search(self, query: str, top_k: int = 5):
        query_embedding = self.vector_index.model.encode([query])
        faiss.normalize_L2(query_embedding)

        scores, indices = self.vector_index.index.search(query_embedding, min(top_k, len(self.vector_index.chunks)))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1:
                results.append((int(idx), float(score)))
        
        return results
    
    def bm25_search(self, query: str, top_k: int = 5):
        query_tokens = query.lower().split()

        scores = []
        for doc_id, doc_tokens in enumerate(self.bm25_index.documents):
            score = self._bm25_score(query_tokens, doc_tokens)
            scores.append((int(doc_id), float(score)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def _bm25_score(self, query_tokens: list[str], doc_tokens: list[str]):
        """Calculates bM25 score for a single document"""
        k1 = 1.5
        b = 0.75

        doc_len = len(doc_tokens)
        avg_doc_len = self.bm25_index.avg_doc_len

        score = 0

        for token in set(query_tokens):
            if token in self.bm25_index.idf:
                idf = self.bm25_index.idf.get(token)
                tf = doc_tokens.count(token)

                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_len/avg_doc_len))

                score += idf * (numerator / denominator)
        
        return score

class BM25Index:
    def __init__(self, chunks: list[dict]):
        """Build BM25 index from chunks"""
        self.chunks = chunks
        self.documents = []
        self.idf = {}
        self.avg_doc_len = 0
        self._build_index()

    def _build_index(self):
        self.documents = [] # list of list of tokens

        for chunk in self.chunks:
            text  =f"{chunk.get('name', '')} {chunk.get('docstring', '')} {chunk.get('code', '')}".lower()
            tokens = text.split()
            self.documents.append(tokens)
        
        # Calculating IDF
        doc_count = len(self.documents)
        doc_token_freq = {}

        for doc in self.documents:
            unique_tokens = set(doc)
            
            for token in unique_tokens:
                doc_token_freq[token] = doc_token_freq.get(token, 0) + 1
        
        for token, freq in doc_token_freq.items():
            self.idf[token] = math.log((doc_count - freq + 0.5) / (freq + 0.5) + 1)
        
        self.avg_doc_len = sum(len(doc) for doc in self.documents) / doc_count
    