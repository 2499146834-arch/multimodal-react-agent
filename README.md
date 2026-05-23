# Multimodal ReAct Agent

A multimodal ReAct (Reasoning + Acting) agent that autonomously selects and chains tools — **OCR** (EasyOCR), **Object Detection** (YOLOv8n), **Vision-Language Model** (Claude), and **Knowledge Search** (Claude) — to answer questions about images.

## Features

- **Autonomous tool selection** — Agent decides whether to OCR, detect objects, query VLM, or search knowledge at each step
- **ReAct loop** — Thought → Action → Observation cycle, max 4 steps
- **GPU acceleration** — YOLOv8n and EasyOCR run on CUDA (RTX 5060 Ti)
- **Ablation study** — Systematic comparison of Baseline / OCR Only / Detect Only / Full Agent on 100 TextVQA samples
- **Gradio web UI** — Upload images, ask questions, see step-by-step reasoning
- **Word reports** — Auto-generated experiment reports in English and Chinese

## Architecture

```
┌──────────────────────────────────────────┐
│            Gradio UI (app.py)            │
└──────────────────┬───────────────────────┘
                   │
┌──────────────────▼───────────────────────┐
│         ReAct Agent (agent/)             │
│  ┌─────────────────────────────────┐    │
│  │  Thought → Action → Observe     │    │
│  │         (max 4 loops)           │    │
│  └─────────────────────────────────┘    │
└──────┬────────┬────────┬────────────────┘
       │        │        │
  ┌────▼──┐ ┌──▼───┐ ┌─▼──────┐
  │  OCR   │ │Detect│ │  VLM   │  Search
  │EasyOCR │ │YOLOv8│ │Claude  │  Claude
  └────────┘ └──────┘ └────────┘
```

## Project Structure

```
multimodal_agent/
├── tools/                     Tool implementations
│   ├── ocr_tool.py            EasyOCR text extraction
│   ├── vlm_tool.py            Claude Vision API
│   ├── detection_tool.py      YOLOv8n object detection
│   └── search_tool.py         Claude knowledge search
├── agent/                     ReAct agent
│   ├── prompts.py             System prompt
│   └── react_agent.py         Agent loop & tool routing
├── eval/                      Evaluation & experiments
│   ├── run_eval.py            Experiment 1: baseline vs agent
│   ├── run_ablation.py        Experiment 2: ablation study
│   ├── download_vqa.py        TextVQA dataset downloader
│   ├── agent_variants.py      Restricted agent for ablation
│   ├── metrics.py             EM / Contains / Tool Precision
│   ├── plot_results.py        Experiment 1 charts
│   ├── plot_ablation.py       Experiment 2 charts (4 figures)
│   ├── generate_report.py     English report generator
│   ├── generate_word_report.py  Word report (EN + ZH)
│   ├── figures/               Generated charts
│   └── report.md              Ablation report (markdown)
├── data/                      Test data
│   ├── images/                10 hand-picked test images
│   ├── sample_questions.json  Experiment 1 questions
│   └── textvqa_200.json       200 TextVQA questions
├── app.py                     Gradio web UI
├── run_app.bat                Double-click launcher (Windows)
├── download_data.py           Test image downloader
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- CUDA-capable GPU (8GB+ VRAM)
- Claude API key

### Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/multimodal-react-agent.git
cd multimodal-react-agent

# Install dependencies
pip install easyocr ultralytics gradio opencv-python langchain torch transformers python-dotenv anthropic python-docx matplotlib pillow

# Configure API key
# Create .env file with:
#   ANTHROPIC_API_KEY=your_key_here
#   ANTHROPIC_BASE_URL=https://api.aipaibox.com
```

### Launch Web UI

```bash
python app.py
# or double-click run_app.bat on Windows
```

Open `http://127.0.0.1:7860` in your browser.

### Run Experiments

```bash
# Download TextVQA test data
python eval/download_vqa.py

# Experiment 1: 10-sample baseline vs agent
python eval/run_eval.py
python eval/plot_results.py

# Experiment 2: Ablation study (100 samples)
python eval/run_ablation.py
python eval/plot_ablation.py

# Generate reports
python eval/generate_word_report.py
```

## Experiments

### Experiment 1: Small-Scale Validation (10 samples)

Hand-picked images from Wikimedia Commons across OCR, detection, and search categories.

### Experiment 2: Ablation Study (100 TextVQA samples)

Four configurations systematically compared:

| Configuration | EM | Contains | Latency | Tokens |
|---|---|---|---|---|
| Baseline (VLM only) | 0.000 | 0.910 | 21.0s | ~600 |
| OCR Only | 0.000 | 0.760 | 51.2s | 3,295 |
| Detect Only | 0.010 | 0.710 | 46.9s | 3,818 |
| Full Agent | 0.000 | 0.740 | 59.1s | 3,434 |

**Key findings:**
1. VLM directly achieves highest Contains Match; agent approaches trade speed for structured answers
2. OCR is the most frequently invoked tool in TextVQA tasks
3. Token consumption varies 5-6x between baseline and agent configurations

## API Configuration

All API calls use the Anthropic SDK with model `claude-sonnet-4-6`. Configure via `.env`:

```
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_BASE_URL=https://api.aipaibox.com
```

## Tools

| Tool | Backend | GPU | Description |
|------|---------|-----|-------------|
| `ocr` | EasyOCR (ch_sim, en) | Yes | Extract text from images |
| `detect` | YOLOv8n | Yes | Object detection (conf >= 0.5) |
| `vlm` | Claude Vision API | No | Visual description & QA |
| `search` | Claude API | No | Knowledge retrieval |

## License

MIT
