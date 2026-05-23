import json
import os

RESULTS_FILE = os.path.join(os.path.dirname(__file__), "ablation_results.json")
REPORT_FILE = os.path.join(os.path.dirname(__file__), "report.md")

EXPERIMENT_NAMES = ["baseline", "ocr_only", "detect_only", "full_agent"]
EXP_LABELS = {
    "baseline": "Baseline (VLM only)",
    "ocr_only": "OCR Only",
    "detect_only": "Detect Only",
    "full_agent": "Full Agent",
}


def _avg(lst):
    return sum(lst) / len(lst) if lst else 0


def _extract_findings(stats):
    findings = []
    ems = {k: v["em"] for k, v in stats.items()}
    lats = {k: v["avg_latency"] for k, v in stats.items()}
    toks = {k: v["avg_tokens"] for k, v in stats.items()}

    best_em = max(ems, key=ems.get)
    worst_em = min(ems, key=ems.get)
    findings.append(
        f"**{EXP_LABELS[best_em]}** achieved the highest Exact Match ({ems[best_em]:.1%}), "
        f"while **{EXP_LABELS[worst_em]}** scored lowest ({ems[worst_em]:.1%}). "
        f"This shows that {'tool-augmented reasoning improves accuracy' if best_em != 'baseline' else 'direct VLM is sufficient for this task'}."
    )

    fastest = min(lats, key=lats.get)
    slowest = max(lats, key=lats.get)
    findings.append(
        f"**{EXP_LABELS[fastest]}** was fastest ({lats[fastest]:.1f}s avg), "
        f"**{EXP_LABELS[slowest]}** slowest ({lats[slowest]:.1f}s avg). "
        f"Agent-based approaches add latency but {'provide richer answers' if ems.get('full_agent', 0) > ems.get('baseline', 0) else 'trade speed for accuracy'}."
    )

    cheapest = min(toks, key=toks.get)
    dearest = max(toks, key=toks.get)
    findings.append(
        f"**{EXP_LABELS[cheapest]}** used fewest tokens ({toks[cheapest]:.0f}), "
        f"**{EXP_LABELS[dearest]}** used most ({toks[dearest]:.0f}). "
        f"Token efficiency varies {toks[dearest]/max(toks[cheapest],1):.1f}x across configurations."
    )

    return findings


def main():
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)

    stats = {}
    for exp in EXPERIMENT_NAMES:
        entries = results.get(exp, [])
        n = len(entries)
        stats[exp] = {
            "n": n,
            "em": _avg([r["em"] for r in entries]),
            "contains": _avg([r["contains"] for r in entries]),
            "avg_latency": _avg([r["latency"] for r in entries]),
            "avg_tokens": _avg([r["tokens"] for r in entries]),
        }

    findings = _extract_findings(stats)

    lines = []
    lines.append("# Ablation Experiment Report")
    lines.append("")
    lines.append("## Experiment Setup")
    lines.append("")
    lines.append(f"- **Dataset**: TextVQA validation set, {stats['baseline']['n']} sampled questions")
    lines.append("- **Max agent steps**: 4")
    lines.append("- **Model**: claude-sonnet-4-6")
    lines.append("")
    lines.append("### Configurations")
    lines.append("")
    lines.append("| Name | Description |")
    lines.append("|------|-------------|")
    lines.append("| Baseline (VLM only) | Direct VLM call without any tools |")
    lines.append("| OCR Only | Agent with OCR + VLM only (detect/search disabled) |")
    lines.append("| Detect Only | Agent with detection + VLM only (ocr/search disabled) |")
    lines.append("| Full Agent | Full ReAct agent with all tools available |")
    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append("| Configuration | N | EM Accuracy | Contains Accuracy | Avg Latency (s) | Avg Tokens |")
    lines.append("|---------------|----|-------------|-------------------|-----------------|------------|")
    for exp in EXPERIMENT_NAMES:
        s = stats[exp]
        lines.append(f"| {EXP_LABELS[exp]} | {s['n']} | {s['em']:.3f} | {s['contains']:.3f} | {s['avg_latency']:.1f} | {s['avg_tokens']:.0f} |")
    lines.append("")
    lines.append("## Key Findings")
    lines.append("")
    for i, finding in enumerate(findings, 1):
        lines.append(f"{i}. {finding}")
        lines.append("")
    lines.append("## Charts")
    lines.append("")
    lines.append("![Accuracy Comparison](figures/accuracy_comparison.png)")
    lines.append("")
    lines.append("![Latency Distribution](figures/latency_boxplot.png)")
    lines.append("")
    lines.append("![Tool Usage Heatmap](figures/tool_usage_heatmap.png)")
    lines.append("")
    lines.append("![Token Efficiency](figures/token_efficiency.png)")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Report saved to: {REPORT_FILE}")


if __name__ == "__main__":
    main()
