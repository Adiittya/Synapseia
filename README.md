<div align="center">

```
███████╗██╗   ██╗███╗   ██╗ █████╗ ██████╗ ███████╗███████╗██╗ █████╗ 
██╔════╝╚██╗ ██╔╝████╗  ██║██╔══██╗██╔══██╗██╔════╝██╔════╝██║██╔══██╗
███████╗ ╚████╔╝ ██╔██╗ ██║███████║██████╔╝███████╗█████╗  ██║███████║
╚════██║  ╚██╔╝  ██║╚██╗██║██╔══██║██╔═══╝ ╚════██║██╔══╝  ██║██╔══██║
███████║   ██║   ██║ ╚████║██║  ██║██║     ███████║███████╗██║██║  ██║
╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚══════╝╚══════╝╚═╝╚═╝  ╚═╝
```

**A local-first multi-agent AI system. Powered by Ollama. Running entirely on your machine.**

[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/ollama-local%20LLMs-black?style=flat-square)](https://ollama.ai)
[![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![Privacy](https://img.shields.io/badge/privacy-100%25%20local-green?style=flat-square)](#-privacy-first-ai)

</div>

---

> **Synapseia** explores what local, modular, and collaborative AI can become when intelligence is distributed across specialized agents — not centralized in a single model. No API keys. No subscriptions. No cloud. Just intelligence, on your terms.

---

## 🎥 Demo

![Synapseia Demo](https://raw.githubusercontent.com/Adiittya/Synapseia/main/.streamlit/intro.gif)

The demo showcases:
- Multi-agent orchestration routing a complex query through specialized agents
- Financial analysis with automated chart generation
- Web research with source-aware, noise-filtered responses
- GitHub repository intelligence and code tracing
- Long-term memory and user personalization — all stored locally

---

## ✨ Core Agents

Synapseia is built around a modular set of specialized agents. Each one is independently capable — and exponentially more powerful in combination.

| Agent | Role |
|-------|------|
| 🌐 **Web Agent** | Contextual web research, noise filtering, source-aware responses |
| 📈 **Stock Agent** | Financial data retrieval, trend analysis, automated visual plots |
| 🧠 **Memory Agent** | Local memory storage for personalization and long-term continuity |
| 💻 **Code Agent** | GitHub repo understanding, structure mapping, function tracing |
| ⚡ **Raw Agent** | Lightweight direct responses with zero orchestration overhead |

---

## 🏗️ Architecture
![Architecture](https://raw.githubusercontent.com/Adiittya/Synapseia/main/.streamlit/image.png)

The orchestration layer manages:
- **Agent routing** — intelligently selects and chains the right agents per query
- **Context handling** — injects relevant memory and conversation history
- **Validation loops** — verifies output correctness before delivery
- **Structured outputs** — formats responses consistently across agents
- **Human-in-the-loop** — surfaces ambiguity for user clarification when needed

---

## 🔒 Privacy-First AI

Synapseia is built with a zero-trust approach to external services.

```
✅  Fully offline execution
✅  No API keys required
✅  No subscriptions
✅  No cloud dependency
✅  No telemetry
✅  Complete data ownership
```

> **Your data never leaves your machine.** Every LLM call, every embedding, every memory write — local.

---

## 🛠️ Tech Stack

**LLMs & AI**
- Ollama runtime — Llama 3.2
- Embedding Models — Nomic-Embed-Text, all-MiniLM-L6-v2, BGE-Small-En

**Backend & Databases**
- Python, FastAPI
- ChromaDB (vector store)

---

## ⚡ Installation

### Prerequisites

- [Ollama](https://ollama.ai) installed and running
- Python 3.10+
- Docker (optional but recommended)

### Quickstart

```bash
# 1. Clone the repo
git clone https://github.com/Adiittya/Synapseia
cd synapseia

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Ollama (if not already running)
ollama serve

# 4. Pull a model (e.g., Llama 3.2)
ollama pull llama3.2

# 5. Launch Synapseia
python app.py
```

## 🌌 Vision

Synapseia is a proof-of-concept and ongoing exploration of what happens when AI is:

- **Local** — running on your hardware, not someone else's
- **Modular** — specialized agents that do one thing exceptionally well
- **Collaborative** — agents that coordinate, not just coexist
- **Private** — no external calls, no data leakage, no corporate dependency

The goal isn't to replicate a cloud AI product. It's to demonstrate that a **personal AI system** — one that knows you, remembers you, and works for you — can exist entirely on commodity hardware.

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with curiosity. Runs without permission.**

*A personal AI system. Running entirely on your machine.*

</div>
