import re
import string


def _normalize(text: str) -> str:
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def exact_match(pred: str, answers: list) -> int:
    pred_norm = _normalize(pred)
    for ans in answers:
        if _normalize(ans) == pred_norm:
            return 1
    return 0


def contains_match(pred: str, answers: list) -> int:
    pred_norm = _normalize(pred)
    for ans in answers:
        ans_norm = _normalize(ans)
        if ans_norm and ans_norm in pred_norm:
            return 1
    return 0


def _tool_used_in_answer(tool_name: str, answer: str, observation: str) -> bool:
    """Check if tool output keywords appear in final answer."""
    obs_norm = _normalize(observation)
    ans_norm = _normalize(answer)
    if not obs_norm or not ans_norm:
        return False
    words = obs_norm.split()
    keywords = [w for w in words if len(w) > 2]
    match_count = sum(1 for kw in keywords if kw in ans_norm)
    return match_count >= 2


def compute_stats(results: list) -> dict:
    total = len(results)
    if total == 0:
        return {"em": 0.0, "contains": 0.0, "avg_latency": 0.0,
                "avg_tokens": 0, "tool_precision": 0.0}

    em_sum = sum(r.get("em", 0) for r in results)
    contains_sum = sum(r.get("contains", 0) for r in results)
    latencies = [r.get("latency", 0) for r in results]
    tokens = [r.get("tokens", 0) for r in results]
    avg_latency = sum(latencies) / total
    avg_tokens = int(sum(tokens) / total)

    # tool_precision: effective tool calls / total tool calls
    effective = 0
    total_calls = 0
    for r in results:
        tools_used = r.get("tools_used", [])
        total_calls += len(tools_used)
        # Check if first tool's observation appears in answer (heuristic)
        answer = r.get("pred", "")
        trace = r.get("trace", [])
        for t in trace:
            obs = t.get("observation", "")
            action = t.get("action", "")
            if action != "final_answer" and _tool_used_in_answer(action, answer, obs):
                effective += 1

    tool_precision = effective / total_calls if total_calls > 0 else 0.0

    return {
        "em": round(em_sum / total, 4),
        "contains": round(contains_sum / total, 4),
        "avg_latency": round(avg_latency, 2),
        "avg_tokens": avg_tokens,
        "tool_precision": round(tool_precision, 4),
    }
