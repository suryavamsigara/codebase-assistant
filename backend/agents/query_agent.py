import json
from agents.deepseek import get_client

class QueryAgent:
    """Rewrites user query into better search queries"""
    def __init__(self):
        self.client = get_client()

    def rewrite_query(self, original_query: str) -> list[str]:
        """Generates 3 subqueries from the original query."""
        SYSTEM_PROMPT = f"""You are a code search assistant. Given a question about a codebase, 
        generate 3 search queries that would help find relevant code. Each query should target 
        a different aspect (e.g. entry point, implementation detail, related config/middleware).

        Return ONLY a raw JSON array of 3 strings. No markdown, no explanation.
        Example: ["query1", "query2", "query3"]
        """


        USER_PROMPT = f"""
        User question: "{original_query}"
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

        raw = response.choices[0].message.content.strip()
        try:
            sub_queries = json.loads(raw)
            if not isinstance(sub_queries, list):
                raise ValueError("Expected a list")
            return sub_queries[:3]
        except:
            return [original_query]