import os
from dotenv import load_dotenv
import anthropic

load_dotenv(r"D:\Multimodal Project\.env", override=True)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            base_url=os.getenv("ANTHROPIC_BASE_URL")
        )
    return _client


def web_search(query: str) -> str:
    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system="你是搜索助手，根据query用3条要点回答相关知识，每条一行",
            messages=[{
                "role": "user",
                "content": query
            }]
        )
        for block in response.content:
            if getattr(block, 'type', None) == 'text':
                return block.text
        return "No text response"
    except Exception as e:
        return f"Search failed: {e}"
