import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.vlm_tool import vlm_describe
from agent.react_agent import run_agent

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
QUESTIONS_FILE = os.path.join(DATA_DIR, "sample_questions.json")
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "results.json")


def main():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    questions = questions[:10]
    results = []

    for i, item in enumerate(questions):
        image_path = os.path.join(PROJECT_DIR, item["image_path"])
        question = item["question"]
        print(f"\n[{i+1}/10] Processing: {os.path.basename(image_path)}")
        print(f"  Question: {question[:60]}...")

        # Baseline: direct VLM
        try:
            baseline_answer = vlm_describe(image_path, question)
        except Exception as e:
            baseline_answer = f"Baseline error: {e}"
        print(f"  Baseline: {baseline_answer[:80]}...")

        # Agent
        try:
            agent_result = run_agent(image_path, question)
            agent_answer = agent_result["answer"]
            tools_used = agent_result["tools_used"]
        except Exception as e:
            agent_answer = f"Agent error: {e}"
            tools_used = []
        print(f"  Agent: {agent_answer[:80]}...")
        print(f"  Tools used: {tools_used}")

        results.append({
            "question": question,
            "image_path": item["image_path"],
            "expected_tools": item.get("expected_tools", []),
            "baseline_answer": baseline_answer,
            "agent_answer": agent_answer,
            "tools_used": tools_used,
        })

        if i < len(questions) - 1:
            time.sleep(1)

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
