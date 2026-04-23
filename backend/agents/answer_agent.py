from agents.deepseek import get_client
from typing import AsyncGenerator
from logger import logger

class AnswerAgent:
    def __init__(self):
        self.client = get_client()

    async def stream_answer(self, query: str, retrieved_chunks: list[dict], history: list) -> AsyncGenerator:
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
        You are a codebase assistant. Answer the user's question using the code chunks provided and conversation history.

        <rules>
        - If a chunk shows a function, explain what it does.
        - If multiple chunks are relevant, synthesize them.
        - DO NOT invent code or citations.
        - Prefer citing the most relevant chunks instead of all chunks.
        - If code chunks are not provided with the question, DO NOT cite.
        </rules>

        <formatting_rules>
        You must structure your response strictly using this Markdown hierarchy. DO NOT deviate.
        1. HEADINGS: Use `### ` for all major sections. DO NOT use numbered lists (e.g., "1. Forward Pass").
        2. LISTS: Use `- ` for bullets. Do not write dense paragraphs. Use bullet points heavily.
        3. BOLDING: Use `**text**:` to highlight key concepts at the start of every bullet point.
        </formatting_rules>

        <citation_rules>
        Whenever you reference a file, code snippet, or concept from the context, you MUST append a markdown link citing the CHUNK_ID.
        THE ONLY ACCEPTABLE FORMAT: [exact_filename](#exact-chunk-id)

        CRITICAL CONSTRAINTS:
        - NEVER output a raw filename like `nn/layers.py` or `tensor.py` without the markdown link formatting.
        - NEVER use a closing bracket `]` where a parenthesis `)` belongs.
        - NEVER combine multiple chunk IDs into one link.
        </citation_rules>

        <examples>
        BAD RESPONSE (DO NOT DO THIS):
        1. Gradient Flow
        Parameter Registration: The linear layer creates weight and bias nn/layers.py.
        The backward method builds the order [tensor.py](#chunk-0] [tensor.py](#chunk-1, chunk-2).

        GOOD RESPONSE (DO THIS STRICTLY):
        ### Gradient Flow
        - **Parameter Registration:** The linear layer creates weight and bias [nn/layers.py](#chunk-0).
        - **Forward Pass:** The matrix multiplication is computed [nn/layers.py](#chunk-1).
        - **Backward Method:** The backward method builds the order [tensor.py](#chunk-0) [tensor.py](#chunk-1) [tensor.py](#chunk-2).
        </examples>
        """

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        for msg in history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        if retrieved_chunks:
            USER_PROMPT = f"""
            User question:
            {query}

            Retrieved code chunks:
            {''.join(formatted_chunks)}
            """
        
        else:
            USER_PROMPT = query
        
        messages.append({
            "role": "user",
            "content": USER_PROMPT
        })
        
        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.3,
                stream=True
            )
            logger.info(f"Stream started for query: {query[:50]}...")

            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content is not None:
                    yield content

        except Exception as e:
            logger.error(f"LLLM provider error: {str(e)}", exc_info=True)
            yield "Sorry, I encountered an error connecting to the AI service."
                    


        # message = response.choices[0].message

        # if message.content:
        #     return message.content
        # return ""