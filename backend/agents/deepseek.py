import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def get_client() -> OpenAI:
    API_KEY = os.getenv("DEEPSEEK_API_KEY")
    if not API_KEY:
        raise EnvironmentError("DEEPSEEK_API_KEY not set.")
    return OpenAI(
            api_key=API_KEY,
            base_url="https://api.deepseek.com"
        )
