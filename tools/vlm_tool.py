import base64
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


def vlm_describe(image_path: str, question: str) -> str:
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        ext = os.path.splitext(image_path)[1].lower()
        if ext in ('.jpg', '.jpeg'):
            media_type = "image/jpeg"
        elif ext == '.png':
            media_type = "image/png"
        elif ext == '.gif':
            media_type = "image/gif"
        elif ext == '.webp':
            media_type = "image/webp"
        else:
            media_type = "image/jpeg"

        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        }
                    },
                    {
                        "type": "text",
                        "text": question
                    }
                ]
            }]
        )
        for block in response.content:
            if getattr(block, 'type', None) == 'text':
                return block.text
        return "No text response"
    except Exception as e:
        return f"VLM failed: {e}"
