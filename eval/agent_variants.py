"""Restricted agent variants for ablation experiments.

Does NOT modify existing agent/tools code — wraps the existing agent
and adds tool restriction by filtering the system prompt.
"""
import os
import re
import time
from dotenv import load_dotenv
import anthropic

load_dotenv(r"D:\Multimodal Project\.env", override=True)

from agent.prompts import REACT_SYSTEM_PROMPT
from tools.ocr_tool import ocr_extract
from tools.detection_tool import detect_objects
from tools.vlm_tool import vlm_describe
from tools.search_tool import web_search

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            base_url=os.getenv("ANTHROPIC_BASE_URL")
        )
    return _client


_ALL_TOOLS = {
    "ocr": ocr_extract,
    "detect": detect_objects,
    "vlm": lambda inp: vlm_describe(*_split_vlm_input(inp)),
    "search": web_search,
}


def _split_vlm_input(action_input):
    parts = action_input.split("|", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return action_input, "Describe this image in detail."


def _build_restricted_prompt(disabled_tools):
    if not disabled_tools:
        return REACT_SYSTEM_PROMPT
    lines = REACT_SYSTEM_PROMPT.strip().split("\n")
    filtered = []
    for line in lines:
        keep = True
        for dt in disabled_tools:
            if line.strip().startswith(f"- {dt}:") or line.strip().startswith(f"- {dt} "):
                keep = False
                break
        filtered.append(line)
    return "\n".join(filtered)


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


def _execute_tool_restricted(action: str, action_input: str, disabled_tools) -> str:
    if action in disabled_tools:
        return f"Tool '{action}' is disabled for this experiment."
    tool_fn = _ALL_TOOLS.get(action)
    if tool_fn:
        return tool_fn(action_input)
    return f"Unknown tool: {action}"


def run_agent_restricted(image_path: str, question: str, disabled_tools=None) -> dict:
    """Run agent with optional tool restrictions.

    Args:
        image_path: Path to image file
        question: User question
        disabled_tools: Set of tool names to disable (e.g. {"search", "detect"})

    Returns:
        dict with keys: answer, trace, tools_used, latency, tokens
    """
    if disabled_tools is None:
        disabled_tools = set()
    disabled_tools = set(disabled_tools)

    trace = []
    tools_used = []
    total_tokens = 0
    start_time = time.time()

    system_prompt = _build_restricted_prompt(disabled_tools)

    messages = [
        {"role": "user", "content": f"图片路径: {image_path}\n问题: {question}"}
    ]

    max_steps = 4
    final_answer = ""

    for step in range(max_steps):
        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=messages
        )
        usage = getattr(response, 'usage', None)
        if usage:
            total_tokens += getattr(usage, 'input_tokens', 0) + getattr(usage, 'output_tokens', 0)

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
            latency = round(time.time() - start_time, 2)
            return {
                "answer": final_answer,
                "trace": trace,
                "tools_used": tools_used,
                "latency": latency,
                "tokens": total_tokens,
            }

        if action:
            observation = _execute_tool_restricted(action, action_input, disabled_tools)
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

    latency = round(time.time() - start_time, 2)
    return {
        "answer": final_answer or "Agent reached maximum steps without a final answer.",
        "trace": trace,
        "tools_used": tools_used,
        "latency": latency,
        "tokens": total_tokens,
    }
