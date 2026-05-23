import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eval.agent_variants import run_agent_restricted
from eval.metrics import exact_match, contains_match

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(PROJECT_DIR, "data", "textvqa_200.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "ablation_results.json")
MAX_ITEMS = 100
RETRY_MAX = 2

EXPERIMENTS = {
    "baseline":       {"type": "baseline",    "disabled": None},
    "ocr_only":       {"type": "agent",       "disabled": ["detect", "search"]},
    "detect_only":    {"type": "agent",       "disabled": ["ocr", "search"]},
    "full_agent":     {"type": "agent",       "disabled": []},
}


def run_baseline(image_path, question):
    import os, base64
    from dotenv import load_dotenv
    import anthropic
    load_dotenv(r"D:\Multimodal Project\.env", override=True)

    for attempt in range(RETRY_MAX):
        try:
            start = time.time()
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            ext = os.path.splitext(image_path)[1].lower()
            mt = "image/png" if ext == ".png" else "image/jpeg"
            client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                base_url=os.getenv("ANTHROPIC_BASE_URL")
            )
            resp = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=1024,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": mt, "data": img_data}},
                    {"type": "text", "text": question}
                ]}]
            )
            answer = next((b.text for b in resp.content if getattr(b, 'type', None) == 'text'), "")
            latency = round(time.time() - start, 2)
            tokens = 0
            if hasattr(resp, 'usage'):
                tokens = getattr(resp.usage, 'input_tokens', 0) + getattr(resp.usage, 'output_tokens', 0)
            return {
                "answer": answer, "trace": [], "tools_used": [],
                "latency": latency, "tokens": tokens,
            }
        except Exception:
            if attempt < RETRY_MAX - 1:
                time.sleep(2)
    return {"answer": "", "trace": [], "tools_used": [], "latency": 0, "tokens": 0}


def run_agent_exp(image_path, question, disabled):
    for attempt in range(RETRY_MAX):
        try:
            result = run_agent_restricted(image_path, question, disabled_tools=disabled)
            return result
        except Exception:
            if attempt < RETRY_MAX - 1:
                time.sleep(2)
    return {
        "answer": "",
        "trace": [],
        "tools_used": [],
        "latency": 0,
        "tokens": 0,
    }


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data[:MAX_ITEMS]
    total = len(items)
    print(f"Running ablation on {total} items ({len(EXPERIMENTS)} experiments each)")

    all_results = {exp_name: [] for exp_name in EXPERIMENTS}

    for idx, item in enumerate(items):
        image_path = os.path.join(PROJECT_DIR, item["image_path"])
        question = item["question"]
        answers = item.get("answers", [])

        if not os.path.exists(image_path):
            continue

        for exp_name, config in EXPERIMENTS.items():
            if config["type"] == "baseline":
                result = run_baseline(image_path, question)
            else:
                disabled = set(config["disabled"]) if config["disabled"] else set()
                result = run_agent_exp(image_path, question, disabled)

            pred = result.get("answer", "")
            em = exact_match(pred, answers)
            cm = contains_match(pred, answers)

            entry = {
                "question": question,
                "image_path": item["image_path"],
                "pred": pred,
                "answers": answers,
                "em": em,
                "contains": cm,
                "latency": result["latency"],
                "tokens": result["tokens"],
                "tools_used": result["tools_used"],
            }
            all_results[exp_name].append(entry)

        if (idx + 1) % 10 == 0:
            stats = {}
            for exp_name in EXPERIMENTS:
                items_done = len(all_results[exp_name])
                if items_done > 0:
                    em_avg = sum(r["em"] for r in all_results[exp_name]) / items_done
                    stats[exp_name] = f"{em_avg:.2f}"
                else:
                    stats[exp_name] = "N/A"
            parts = " ".join([f"{k}:{v}" for k, v in stats.items()])
            print(f"[{idx+1}/{total}] {parts}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # Print final summary
    print(f"\nResults saved to: {OUTPUT_FILE}")
    for exp_name in EXPERIMENTS:
        items_done = len(all_results[exp_name])
        if items_done > 0:
            em_avg = sum(r["em"] for r in all_results[exp_name]) / items_done
            cm_avg = sum(r["contains"] for r in all_results[exp_name]) / items_done
            lat_avg = sum(r["latency"] for r in all_results[exp_name]) / items_done
            tok_avg = sum(r["tokens"] for r in all_results[exp_name]) / items_done
            print(f"  {exp_name}: EM={em_avg:.3f}, Contains={cm_avg:.3f}, "
                  f"Latency={lat_avg:.1f}s, Tokens={tok_avg:.0f}")


if __name__ == "__main__":
    main()
