import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import Counter

RESULTS_FILE = os.path.join(os.path.dirname(__file__), "results.json")
EVAL_DIR = os.path.dirname(__file__)


def main():
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)

    # Chart 1: Tool usage frequency
    all_tools = []
    for r in results:
        all_tools.extend(r.get("tools_used", []))
    tool_counts = Counter(all_tools)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    if tool_counts:
        tools = list(tool_counts.keys())
        counts = [tool_counts[t] for t in tools]
        bars = ax1.bar(tools, counts, color=["#4C78A8", "#F58518", "#E45756", "#72B7B2"])
        ax1.set_title("Tool Usage Frequency", fontsize=14)
        ax1.set_ylabel("Count")
        for bar, count in zip(bars, counts):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                     str(count), ha="center", va="bottom")
    else:
        ax1.text(0.5, 0.5, "No tool usage data", ha="center", va="center",
                 transform=ax1.transAxes, fontsize=12)
        ax1.set_title("Tool Usage Frequency", fontsize=14)

    # Chart 2: Answer length comparison
    baseline_lens = [len(r.get("baseline_answer", "")) for r in results]
    agent_lens = [len(r.get("agent_answer", "")) for r in results]
    x = range(len(results))
    width = 0.35
    bars1 = ax2.bar([i - width/2 for i in x], baseline_lens, width,
                    label="Baseline (VLM only)", color="#4C78A8")
    bars2 = ax2.bar([i + width/2 for i in x], agent_lens, width,
                    label="ReAct Agent", color="#F58518")
    ax2.set_title("Answer Length: Baseline vs Agent", fontsize=14)
    ax2.set_xlabel("Question Index")
    ax2.set_ylabel("Answer Length (chars)")
    ax2.set_xticks(x)
    ax2.legend()

    plt.tight_layout()

    fig1_path = os.path.join(EVAL_DIR, "tool_usage.png")
    fig.savefig(fig1_path, dpi=150, bbox_inches="tight")

    # Also save answer_length separately
    fig2, ax = plt.subplots(figsize=(10, 5))
    bars1 = ax.bar([i - width/2 for i in x], baseline_lens, width,
                   label="Baseline (VLM only)", color="#4C78A8")
    bars2 = ax.bar([i + width/2 for i in x], agent_lens, width,
                   label="ReAct Agent", color="#F58518")
    ax.set_title("Answer Length: Baseline vs Agent", fontsize=14)
    ax.set_xlabel("Question Index")
    ax.set_ylabel("Answer Length (chars)")
    ax.set_xticks(x)
    ax.legend()
    fig2_path = os.path.join(EVAL_DIR, "answer_length.png")
    fig2.savefig(fig2_path, dpi=150, bbox_inches="tight")
    plt.close("all")

    print(f"Charts saved: {fig1_path}, {fig2_path}")


if __name__ == "__main__":
    main()
