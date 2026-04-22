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

        RULES:
        - If a chunk shows a function, explain what it does
        - If multiple chunks are relevant, synthesize them
        - DO NOT invent code or citations
        - Prefer citing the most relevant chunks instead of all chunks.

        CRITICAL CITATION RULE:
        Whenever you reference a file or piece of code, you MUST use a markdown link citing the CHUNK_ID. 
        Format it exactly like this: [filename](#chunk-ID)

        CRITICAL FORMATTING RULES:
        You must structure your response strictly using this Markdown hierarchy:

        1. HEADINGS: Use `### ` for all major sections.
        2. LISTS: Use `- ` for bullets. Do not write dense paragraphs. Use bullet points heavily.
        3. BOLDING: Use `**text**` to highlight key concepts at the start of bullets.

        BAD EXAMPLE:
        The linear layer forward pass computes output. Layer Initialization creates weight and bias.

        GOOD EXAMPLE:
        ### Gradient Flow
        - **Layer Initialization:** The linear layer creates weight and bias as Tensor objects [nn/layers.py](#chunk-0).
        - **Forward Pass:** The matrix multiplication is computed [nn/layers.py](#chunk-1).

        If code chunks are not provided with the question, DO NOT cite.
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