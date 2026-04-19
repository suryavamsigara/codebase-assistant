from sqlalchemy.orm import Session
from sqlalchemy import text, select

from agents.query_agent import QueryAgent
from agents.answer_agent import AnswerAgent
from models import DocumentChunk
from retrieval.hybrid_search import reciprocal_rank_fusion

class RAGOrchestrator:
    def __init__(self, embedding_model: str):
        self.answer_agent = AnswerAgent()
        self.query_agent = QueryAgent()
        self.embedding_model = embedding_model
    
    def process_query(self, query: str, repo_name: str, db: Session) -> str:

        sub_queries = self.query_agent.rewrite_query(query) # list[str]
        print(f"============\nResponse: {sub_queries}\n============")

        all_unique_chunk_ids = set()

        for sub_query in sub_queries:
            query_vector = self.embedding_model.encode([sub_query])[0].tolist()

            vector_results = db.execute(
                text("""
                SELECT id, 1 - (embedding <=> :vector) AS similarity
                FROM document_chunks
                WHERE repo_name = :repo_name
                ORDER BY embedding <=> :vector
                LIMIT 8
                """),
                {"vector": str(query_vector), "repo_name": repo_name}
            ).fetchall()
            vector_list = [(row.id, row.similarity) for row in vector_results]

            keyword_results = db.execute(
                text("""
                SELECT id, ts_rank(search_tokens, websearch_to_tsquery('english', :query)) AS rank
                FROM document_chunks
                WHERE repo_name = :repo_name 
                AND search_tokens @@ websearch_to_tsquery('english', :query)
                ORDER BY rank DESC
                LIMIT 8
                """),
                {"query": sub_query, "repo_name": repo_name}
            ).fetchall()
            keyword_list = [(row.id, row.rank) for row in keyword_results]

            ranked_lists = [l for l in (vector_list, keyword_list) if l]
            if ranked_lists:
                fused_results = reciprocal_rank_fusion(ranked_lists)

                for doc_id, score in fused_results[:6]:
                    all_unique_chunk_ids.add(doc_id)

        print(f"\nRetrieved {len(all_unique_chunk_ids)} unique chunks")

        if not all_unique_chunk_ids:
            return "I couldn't find relevant code for this question."

        top_chunks_db = db.execute(
            select(DocumentChunk).where(DocumentChunk.id.in_(all_unique_chunk_ids))
        ).scalars().all()
        
        retrieved_chunks = [
            {
                "file_path": c.file_path,
                "start_line": c.start_line,
                "end_line": c.end_line,
                "type": c.chunk_type,
                "name": c.name,
                "language": c.language,
                "code": c.content,
                "parent_class": c.parent_class,
                "docstring": c.docstring
            }
            for c in top_chunks_db
        ]

        print("\n===================================")

        for c in retrieved_chunks:
            print(f"File: {c['file_path']} | Lines: {c['start_line']}-{c['end_line']}")
        print("===================================\n")
        
        response = self.answer_agent.generate_answer(query, retrieved_chunks)
        return response, retrieved_chunks
