import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RESULTS_FILE = os.path.join(os.path.dirname(__file__), "ablation_results.json")
FIGURES_DIR = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

EXPERIMENT_NAMES = ["baseline", "ocr_only", "detect_only", "full_agent"]
DISPLAY_NAMES = ["Baseline\n(VLM only)", "OCR Only\n(-detect,-search)",
                 "Detect Only\n(-ocr,-search)", "Full Agent"]


def main():
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)

    # === Chart 1: Accuracy Comparison ===
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(EXPERIMENT_NAMES))
    width = 0.35
    em_vals = []
    cm_vals = []
    for exp in EXPERIMENT_NAMES:
        entries = results.get(exp, [])
        n = len(entries) if entries else 1
        em_vals.append(sum(r["em"] for r in entries) / n)
        cm_vals.append(sum(r["contains"] for r in entries) / n)
    bars1 = ax.bar(x - width/2, em_vals, width, label="Exact Match", color="#4C78A8")
    bars2 = ax.bar(x + width/2, cm_vals, width, label="Contains Match", color="#F58518")
    ax.set_ylabel("Accuracy")
    ax.set_title("Accuracy Comparison Across Ablation Configurations")
    ax.set_xticks(x)
    ax.set_xticklabels(DISPLAY_NAMES)
    ax.legend(loc="lower right")
    ax.set_ylim(0, max(max(em_vals), max(cm_vals)) * 1.3)
    for bar, val in zip(bars1, em_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f"{val:.3f}", ha="center", va="bottom", fontsize=9)
    for bar, val in zip(bars2, cm_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f"{val:.3f}", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "accuracy_comparison.png"), dpi=150)
    plt.close()

    # === Chart 2: Latency Boxplot ===
    fig, ax = plt.subplots(figsize=(10, 6))
    latency_data = []
    for exp in EXPERIMENT_NAMES:
        entries = results.get(exp, [])
        lats = [r["latency"] for r in entries if r["latency"] > 0]
        latency_data.append(lats)
    bp = ax.boxplot(latency_data, labels=DISPLAY_NAMES, patch_artist=True)
    colors = ["#4C78A8", "#72B7B2", "#E45756", "#F58518"]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_ylabel("Latency (seconds)")
    ax.set_title("Response Latency Distribution by Configuration")
    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "latency_boxplot.png"), dpi=150)
    plt.close()

    # === Chart 3: Tool Usage Heatmap ===
    tool_names = ["ocr", "detect", "vlm", "search"]
    heatmap_data = np.zeros((len(EXPERIMENT_NAMES), len(tool_names)))
    for i, exp in enumerate(EXPERIMENT_NAMES):
        entries = results.get(exp, [])
        n = len(entries) if entries else 1
        tool_counts = {t: 0 for t in tool_names}
        for r in entries:
            for t in r.get("tools_used", []):
                if t in tool_counts:
                    tool_counts[t] += 1
        for j, t in enumerate(tool_names):
            heatmap_data[i, j] = tool_counts[t] / n

    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(heatmap_data, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(tool_names)))
    ax.set_xticklabels(tool_names)
    ax.set_yticks(range(len(EXPERIMENT_NAMES)))
    ax.set_yticklabels([d.replace("\n", " ") for d in DISPLAY_NAMES])
    ax.set_title("Tool Usage Frequency Heatmap")
    for i in range(len(EXPERIMENT_NAMES)):
        for j in range(len(tool_names)):
            text = ax.text(j, i, f"{heatmap_data[i, j]:.2f}",
                           ha="center", va="center", fontsize=10)
    fig.colorbar(im, ax=ax, label="Calls per question")
    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "tool_usage_heatmap.png"), dpi=150)
    plt.close()

    # === Chart 4: Token Efficiency ===
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, exp in enumerate(EXPERIMENT_NAMES):
        entries = results.get(exp, [])
        n = len(entries) if entries else 1
        avg_tokens = sum(r["tokens"] for r in entries) / n
        avg_em = sum(r["em"] for r in entries) / n
        avg_lat = sum(r["latency"] for r in entries) / n
        ax.scatter(avg_tokens, avg_em, s=max(avg_lat * 50, 80),
                   color=colors[i], label=DISPLAY_NAMES[i].replace("\n", " "),
                   edgecolors="black", alpha=0.8, zorder=5)
    ax.set_xlabel("Average Token Consumption")
    ax.set_ylabel("Exact Match Accuracy")
    ax.set_title("Token Efficiency: Accuracy vs Cost")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "token_efficiency.png"), dpi=150)
    plt.close()

    print(f"4 charts saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
