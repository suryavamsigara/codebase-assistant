import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not API_KEY:
    raise EnvironmentError("DEEPSEEK_API_KEY not set.")

class AnswerAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=API_KEY,
            base_url="https://api.deepseek.com"
        )

    def generate_answer(self, query: str, retrieved_chunks: list[dict]):
        formatted_chunks = []
        for i, chunk in enumerate(retrieved_chunks):
            formatted_chunks.append(
                f"""
                [CHUNK {i}]
                File: {chunk['file_path']}
                Lines: {chunk['start_line']}-{chunk['end_line']}
                Type: {chunk.get('type', 'code')}
                Name: {chunk.get('name', 'unknown')}

                Code:
                ```{chunk.get('language', 'python')}
                {chunk['code'][:1000]}
                ```
                """
            )
        
        SYSTEM_PROMPT = """
        You are a codebase assistant. Answer the user's question using ONLY the code chunks provided.

        RULES:
        - Every claim MUST be backed by a citation in the format [file_path:lines]
        - If a chunk shows a function, explain what it does
        - If multiple chunks are relevant, synthesize them
        - If no chunks are relevant, say "I couldn't find relevant code for this question"
        - DO NOT invent code or citations
        - Prefer citing the most relevant chunks instead of all chunks.
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