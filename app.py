import os
import sys
import time
import gradio as gr

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from agent.react_agent import run_agent

TOOL_ICONS = {
    "ocr": "OCR",
    "detect": "DET",
    "vlm": "VLM",
    "search": "SRC",
}

CSS = """
.gradio-container { max-width: 1200px !important; margin: auto !important; }
.header { text-align: center; padding: 20px 0; border-bottom: 2px solid #e0e0e0; margin-bottom: 20px; }
.header h1 { margin: 0; font-size: 2em; }
.header p { color: #666; margin: 5px 0 0 0; }
.example-chip {
    display: inline-block; padding: 6px 14px; margin: 4px; border-radius: 20px;
    background: #f0f4ff; border: 1px solid #d0d8f0; cursor: pointer; font-size: 13px;
    transition: all 0.2s;
}
.example-chip:hover { background: #dde4ff; border-color: #8899cc; }
.step-card {
    border: 1px solid #e8e8e8; border-radius: 8px; padding: 12px; margin: 8px 0;
    background: #fafafa;
}
.step-card .step-label {
    font-weight: bold; color: #333; margin-bottom: 4px;
}
.step-card .step-obs {
    color: #555; font-size: 13px; max-height: 100px; overflow-y: auto;
    white-space: pre-wrap; word-break: break-word;
}
.status-bar {
    display: flex; gap: 16px; padding: 10px 16px; border-radius: 8px;
    background: #f5f5f5; flex-wrap: wrap;
}
.status-item { font-size: 13px; }
.status-item span { font-weight: bold; color: #333; }
.answer-box { padding: 16px; border-radius: 8px; background: #fff; border: 1px solid #e0e0e0; min-height: 120px; }
footer { visibility: hidden; }
"""

def process(image, question):
    if image is None:
        yield "", _empty_trace(), _empty_status()
        return

    if not question or not question.strip():
        question = "Describe this image in detail."

    image_path = image if isinstance(image, str) else image.name
    start_time = time.time()
    result = run_agent(image_path, question)
    elapsed = time.time() - start_time

    answer = result.get("answer", "Error: no answer produced")
    tools_used = result.get("tools_used", [])
    trace = result.get("trace", [])

    trace_html = _build_trace_html(trace)
    status_html = _build_status_html(tools_used, elapsed, len(trace))

    yield answer, trace_html, status_html


def _build_trace_html(trace):
    if not trace:
        return "<div style='color:#999;padding:20px;text-align:center;'>No steps recorded</div>"

    lines = []
    for i, step in enumerate(trace, 1):
        action = step.get("action", "?")
        observation = step.get("observation", "")
        icon = TOOL_ICONS.get(action, "?")
        if action == "final_answer":
            lines.append(f"""
            <div class="step-card" style="background:#e8f5e9;border-color:#a5d6a7;">
                <div class="step-label">Step {i} | FINAL ANSWER</div>
                <div class="step-obs">{_escape(observation[:300])}</div>
            </div>""")
        elif action == "parse_error":
            lines.append(f"""
            <div class="step-card" style="background:#fff3e0;border-color:#ffcc80;">
                <div class="step-label">Step {i} | Parse Error</div>
                <div class="step-obs">{_escape(observation[:200])}</div>
            </div>""")
        else:
            lines.append(f"""
            <div class="step-card">
                <div class="step-label">Step {i} | [{icon}] {action}</div>
                <div class="step-obs">{_escape(observation[:200])}</div>
            </div>""")

    return "\n".join(lines)


def _build_status_html(tools_used, elapsed, steps):
    tools_str = ", ".join(tools_used) if tools_used else "none"
    return f"""
    <div class="status-bar">
        <div class="status-item">Tools: <span>{tools_str}</span></div>
        <div class="status-item">Steps: <span>{steps}</span></div>
        <div class="status-item">Latency: <span>{elapsed:.1f}s</span></div>
    </div>"""


def _empty_trace():
    return "<div style='color:#999;padding:20px;text-align:center;'>Upload an image and submit to see the thinking process</div>"


def _empty_status():
    return """<div class="status-bar">
        <div class="status-item">Tools: <span>-</span></div>
        <div class="status-item">Steps: <span>-</span></div>
        <div class="status-item">Latency: <span>-</span></div>
    </div>"""


def _escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


with gr.Blocks(title="Multimodal ReAct Agent", css=CSS, theme=gr.themes.Soft()) as demo:
    gr.HTML("""
    <div class="header">
        <h1>Multimodal ReAct Agent</h1>
        <p>OCR + Object Detection + VLM + Knowledge Search &mdash; Autonomous reasoning loop</p>
    </div>""")

    with gr.Row(equal_height=True):
        with gr.Column(scale=2):
            image_input = gr.Image(type="filepath", label="Upload Image", height=360)

            question_input = gr.Textbox(
                label="Your Question",
                placeholder="e.g., What text is on this sign? What objects are in this room? What landmark is in this photo?",
                lines=2,
                show_label=True,
            )

            with gr.Row():
                submit_btn = gr.Button("Analyze", variant="primary", size="lg", scale=2)
                clear_btn = gr.Button("Clear", size="lg", scale=1)

        with gr.Column(scale=3):
            gr.Markdown("### Final Answer")
            answer_output = gr.HTML(value="<div class='answer-box' style='color:#999;'>Upload an image and click <b>Analyze</b> to get started</div>")

            gr.Markdown("### Thinking Process")
            trace_output = gr.HTML(value=_empty_trace())

            status_output = gr.HTML(value=_empty_status())

    # Example question chips
    gr.Markdown("### Quick Questions")
    with gr.Row():
        ex1 = gr.Button("What text is written here?", size="sm")
        ex2 = gr.Button("What objects are in this scene?", size="sm")
        ex3 = gr.Button("Describe this image in detail.", size="sm")
        ex4 = gr.Button("What landmark is this?", size="sm")
        ex5 = gr.Button("What animal or object is this?", size="sm")

    ex1.click(fn=lambda: "What text is written in this image?", inputs=[], outputs=[question_input])
    ex2.click(fn=lambda: "What objects can you detect in this scene?", inputs=[], outputs=[question_input])
    ex3.click(fn=lambda: "Describe this image in detail.", inputs=[], outputs=[question_input])
    ex4.click(fn=lambda: "What landmark is this? Tell me about it.", inputs=[], outputs=[question_input])
    ex5.click(fn=lambda: "What animal or object is this?", inputs=[], outputs=[question_input])

    submit_btn.click(
        fn=process,
        inputs=[image_input, question_input],
        outputs=[answer_output, trace_output, status_output],
    )

    clear_btn.click(
        fn=lambda: (None, "", "<div class='answer-box' style='color:#999;'>Upload an image and click <b>Analyze</b> to get started</div>", _empty_trace(), _empty_status()),
        inputs=[],
        outputs=[image_input, question_input, answer_output, trace_output, status_output],
    )


if __name__ == "__main__":
    try:
        print("Starting Multimodal ReAct Agent...")
        print("Open http://127.0.0.1:7860 in your browser")
        demo.launch(server_name="0.0.0.0", server_port=7860, inbrowser=True)
    except KeyboardInterrupt:
        print("Server stopped.")
    except Exception as e:
        print(f"Error: {e}")
        try:
            input("Press Enter to exit...")
        except EOFError:
            pass
