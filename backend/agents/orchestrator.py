from agents.query_agent import QueryAgent

class RAGOrchestrator:
    def __init__(self, chunks, hybrid_retriever, answer_agent):
        self.chunks = chunks
        self.retriever = hybrid_retriever
        self.answer_agent = answer_agent
        self.query_agent = QueryAgent()
    
    def process_query(self, query: str):

        sub_queries = self.query_agent.rewrite_query(query) # list[str]
        print(f"============\nResponse: {sub_queries}\n============")

        all_results = []
        for sub_query in sub_queries:
            results = self.retriever.search(sub_query, 3)
            all_results.append(results)
        
        print("\nAppended results\n")

        seen = set()
        retrieved_chunks = []

        for results in all_results:
            for idx, score in results:
                if idx not in seen:
                    seen.add(idx)
                    retrieved_chunks.append(self.chunks[idx])
        
        print(f"\nRetrieved {len(retrieved_chunks)} unique chunks")
        print("\n===================================")
        print(retrieved_chunks)
        print("\n===================================")
        
        response = self.answer_agent.generate_answer(query, retrieved_chunks)
        
        return response