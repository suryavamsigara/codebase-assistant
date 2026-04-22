import json
from agents.deepseek import get_client
from logger import logger

class QueryRouter:
    def __init__(self):
        self.client = get_client()
    
    async def decide(self, user_message: str, history: list) -> str:
        """
        Returns 'chat_only' or 'retrieve'
        """
        recent_context = "\n".join([f"{m.role}: {m.content}" for m in history[-3:]])

        SYSTEM_PROMPT = """
        You are a routing agent for a codebase assistant. 
        Determine if the user's latest message requires searching the codebase for new files/code, or if it can be answered using the ongoing conversation history.
        
        RULES:
        - If they ask about a specific file, function, bug, or architecture, output "retrieve".
        - If they ask a follow-up about the code you JUST showed them, ask for clarification, or make general conversation, output "chat_only".
        
        Respond with ONLY a strict JSON object: {"decision": "retrieve"} or {"decision": "chat_only"}
        """

        PROMPT = f"Recent History:\n{recent_context}\n\nUser Message: {user_message}"

        response = await self.client.chat.completions.create(
            model="deepseek-chat",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": PROMPT}
            ]
        )

        try:
            result = json.loads(response.choices[0].message.content)
            return result.get("decision", "retrieve")
        except Exception as e:
            logger.error(f"Router decision failed: {e}")
            return "retrieve"
    
    async def generate_title(self, first_query: str) -> str:
        """Generates a 4-5 word title for a new conversation."""

        system_prompt = "You are a title generator. Create a brief, 4-5 word summary title for a conversation starting with the user's message. Return ONLY the title string, no quotes, no extra text."
        
        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": first_query}
                ],
                temperature=0.3,
                timeout=5
            )
            title = response.choices[0].message.content.strip()
            logger.info(f"Title generated: '{title}'")

            return title.strip('"').strip("'")
        except Exception as e:
            logger.warning(f"Failed to generate title: {e}")
            return "New Conversation"
        