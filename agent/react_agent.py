import os
import re
from dotenv import load_dotenv
import anthropic

from agent.prompts import REACT_SYSTEM_PROMPT
from tools.ocr_tool import ocr_extract
from tools.detection_tool import detect_objects
from tools.vlm_tool import vlm_describe
from tools.search_tool import web_search

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


def _parse_action(text: str):
    thought_match = re.search(r'Thought:\s*(.*)', text)
    action_match = re.search(r'Action:\s*(\S+)', text)
    input_match = re.search(r'Action Input:\s*(.*)', text)
    final_match = re.search(r'Final Answer:\s*(.*)', text, re.DOTALL)

    thought = thought_match.group(1).strip() if thought_match else ""
    action = action_match.group(1).strip() if action_match else ""
    action_input = input_match.group(1).strip() if input_match else ""
    final_answer = final_match.group(1).strip() if final_match else ""

    return thought, action, action_input, final_answer


def _execute_tool(action: str, action_input: str) -> str:
    if action == "ocr":
        return ocr_extract(action_input)
    elif action == "detect":
        return detect_objects(action_input)
    elif action == "vlm":
        parts = action_input.split("|", 1)
        if len(parts) == 2:
            return vlm_describe(parts[0].strip(), parts[1].strip())
        return vlm_describe(action_input, "Describe this image in detail.")
    elif action == "search":
        return web_search(action_input)
    else:
        return f"Unknown tool: {action}"


def run_agent(image_path: str, question: str) -> dict:
    trace = []
    tools_used = []

    messages = [
        {
            "role": "user",
            "content": f"图片路径: {image_path}\n问题: {question}"
        }
    ]

    max_steps = 4
    final_answer = ""

    for step in range(max_steps):
        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=REACT_SYSTEM_PROMPT,
            messages=messages
        )
        text_blocks = [b for b in response.content if getattr(b, 'type', None) == 'text']
        output = text_blocks[0].text if text_blocks else ""
        thought, action, action_input, final_answer = _parse_action(output)

        if final_answer:
            trace.append({
                "thought": thought,
                "action": "final_answer",
                "input": "",
                "observation": final_answer
            })
            return {
                "answer": final_answer,
                "trace": trace,
                "tools_used": tools_used
            }

        if action:
            observation = _execute_tool(action, action_input)
            tools_used.append(action)
            trace.append({
                "thought": thought,
                "action": action,
                "input": action_input,
                "observation": observation
            })
            messages.append({"role": "assistant", "content": output})
            messages.append({"role": "user", "content": f"Observation: {observation}"})
        else:
            trace.append({
                "thought": thought,
                "action": "parse_error",
                "input": "",
                "observation": output
            })
            messages.append({"role": "assistant", "content": output})
            messages.append({"role": "user", "content": "Please continue with the required format."})

    return {
        "answer": final_answer or "Agent reached maximum steps without a final answer.",
        "trace": trace,
        "tools_used": tools_used
    }
