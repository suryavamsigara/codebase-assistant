from agents.deepseek import get_client

class AnswerAgent:
    def __init__(self):
        self.client = get_client()

    def generate_answer(self, query: str, retrieved_chunks: list[dict]) -> str:
        formatted_chunks = []
        for i, chunk in enumerate(retrieved_chunks):
            parent_str = f"Parent Class: {chunk['parent_class']}\n" if chunk.get('parent_class') else ""
            doc_str = f"Docstring: {chunk['docstring']}\n" if chunk.get('docstring') else ""

            formatted_chunks.append(
                f"""
                [CHUNK {i}]
                File: {chunk['file_path']}
                Lines: {chunk['start_line']}-{chunk['end_line']}
                Type: {chunk.get('type', 'code')}
                Name: {chunk.get('name', 'unknown')}
                {parent_str}{doc_str}
                Code:
                ```{chunk.get('language', 'python')}
                {chunk['code'][:1000] if chunk.get('code') else "no code in this chunk"}
                ```
                """
            )
        
        SYSTEM_PROMPT = """
        You are a codebase assistant. Answer the user's question using ONLY the code chunks provided.

        RULES:
        - If a chunk shows a function, explain what it does
        - If multiple chunks are relevant, synthesize them
        - DO NOT invent code or citations
        - Prefer citing the most relevant chunks instead of all chunks.

        CRITICAL CITATION RULE:
        Whenever you reference a file or piece of code, you MUST use a markdown link citing the CHUNK_ID. 
        Format it exactly like this: [filename](#chunk-ID)
        """

        USER_PROMPT = f"""
        User question:
        {query}

        Retrieved code chunks:
        {''.join(formatted_chunks)}
        """

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": USER_PROMPT
            }
        ]

        print("Querying LLM")
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.3
        )

        message = response.choices[0].message

        if message.content:
            return message.content
        return ""