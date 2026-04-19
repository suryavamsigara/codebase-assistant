from sqlalchemy.orm import Session
from sqlalchemy import text, select
from typing import Generator

from agents.query_agent import QueryAgent
from agents.answer_agent import AnswerAgent
from agents.query_router import QueryRouter
from models import DocumentChunk, Conversation, Message
from retrieval.hybrid_search import reciprocal_rank_fusion

class RAGOrchestrator:
    def __init__(self, embedding_model: str):
        self.answer_agent = AnswerAgent()
        self.query_agent = QueryAgent()
        self.router = QueryRouter()
        self.embedding_model = embedding_model
    
    def process_query(
        self,
        query: str,
        repo_name: str,
        db: Session,
        conversation_id: str,
        guest_session_id: str,
        user_id: str
    ) -> Generator: #tuple[str, list[dict[str, any]]]:
        
        conv = db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        ).scalar_one_or_none()

        if not conv:
            chat_title = self.router.generate_title(query)

            new_conv = Conversation(
                id=conversation_id,
                name=chat_title,
                user_id=user_id,
                guest_session_id=guest_session_id,
                repo_name=repo_name
            )
            db.add(new_conv)
            db.flush()
        
        history = db.execute(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
        ).scalars().all()

        new_user_message = Message(conversation_id=conversation_id, role="user", content=query)
        db.add(new_user_message)
        db.flush()

        decision = self.router.decide(query, history)

        retrieved_chunks = []
        answer_text = ""

        try:
            if decision == "retrieve":
                yield {"type": "status", "message": "Searching codebase"}

                print("Router Decision: Searching codebase...")

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

                yield {"type": "citations", "chunks": retrieved_chunks}

                yield {"type": "status", "message": "Synthesizing answer.."}

                # response = self.answer_agent.generate_answer(query, retrieved_chunks, history)

                for token in self.answer_agent.stream_answer(query, retrieved_chunks, history):
                    answer_text += token
                    yield {"type": "token", "content": token}
                        
            else:
                yield {"type": "status", "message": "Recalling context"}
                print("Router Decision: Conversing using history...")

                for token in self.answer_agent.stream_answer(query, [], history):
                    answer_text += token
                    yield {"type": "token", "content": token}

            new_assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=answer_text,
                cited_chunks=retrieved_chunks
            )

            db.add(new_assistant_message)
            db.commit()

            yield {"type": "done"}

            # return response, retrieved_chunks

        except Exception as e:
            print(f"Stream interrupted: {str(e)}")
            yield {"type": "error", "message": "Connection lost or LLM failed."}

        finally:
            if answer_text:
                new_assistant_message = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=answer_text,
                    cited_chunks=retrieved_chunks
                )
                db.add(new_assistant_message)
                db.commit()
            
            yield {"type": "done"}
