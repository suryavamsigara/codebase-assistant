import json
from agents.deepseek import get_client

class QueryRouter:
    def __init__(self):
        self.client = get_client()
    
    def decide(self, user_message: str, history: list) -> str:
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

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": PROMPT}
            ]
        )

        result = json.loads(response.choices[0].message.content)
        return result.get("decision", "retrieve")