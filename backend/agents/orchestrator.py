class RAGOrchestrator:
    def __init__(self, chunks, hybrid_retriever, answer_agent):
        self.chunks = chunks
        self.retriever = hybrid_retriever
        self.answer_agent = answer_agent
    
    def process_query(self, query: str):

        results = self.retriever.search(query, 10)

        retrieved_chunks = []

        for idx, score in results:
            print(f"Chunk: {idx}")
            chunk = self.chunks[idx]
            retrieved_chunks.append(chunk)
        
        print("\n===================================")
        print(retrieved_chunks)
        print("\n===================================")
        
        response = self.answer_agent.generate_answer(query, retrieved_chunks)
        
        return response