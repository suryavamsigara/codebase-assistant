from agents.query_agent import QueryAgent

class RAGOrchestrator:
    def __init__(self, chunks, hybrid_retriever, answer_agent):
        self.chunks = chunks
        self.retriever = hybrid_retriever
        self.answer_agent = answer_agent
        self.query_agent = QueryAgent()
    
    def process_query(self, query: str):

        response = self.query_agent.rewrite_query(query)
        print(f"============\nResponse: {response}\n============")

        all_results = []
        for i in range(len(response)):
            results = self.retriever.search(response[i], 3)
            all_results.append(results)
        
        print("\nAppended results\n")

        retrieved_chunks = []

        for i in range(len(all_results)):
            for idx, score in all_results[i]:
                print(f"Chunk: {idx}")
                chunk = self.chunks[idx]
                retrieved_chunks.append(chunk)
        
        print("\n===================================")
        print(retrieved_chunks)
        print("\n===================================")
        
        response = self.answer_agent.generate_answer(query, retrieved_chunks)
        
        return response