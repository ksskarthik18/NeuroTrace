# 🧠 NeuroTrace — Neural Debugger

> **Autonomous AI System for Bug Localization, Root Cause Analysis, and Patch Verification**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 What is NeuroTrace?

NeuroTrace is an AI-powered debugging framework that autonomously:

1. **Detects** buggy regions in Python source code
2. **Analyzes** runtime traces and error logs
3. **Reasons** about root causes using LLM chain-of-thought
4. **Generates** minimal candidate patches
5. **Validates** fixes automatically via test execution
6. **Reports** confidence-aware debugging explanations

### Example

**Input:**
```python
nums = [1, 2, 3]
print(nums[5])
```

**Output:**
```
Bug Type: IndexError
Root Cause: The list contains only 3 elements, but index 5 is accessed.
Suggested Fix: Check bounds before accessing the index.

Validated Patch:
  if len(nums) > 5:
      print(nums[5])

Confidence: 92%
```

---

## 🏗️ Architecture

```
User Code → Static Analyzer → Execution Sandbox → Runtime Trace Collector
    → LLM Root Cause Analyzer → Patch Generator → Patch Validator → Verified Fix
```

---

## 📁 Project Structure

```
NeuroTrace/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Environment settings
│   ├── models.py            # Pydantic schemas
│   ├── database.py          # SQLite via SQLAlchemy
│   ├── api/
│   │   └── routes.py        # REST API endpoints
│   ├── debugger/
│   │   ├── sandbox.py       # Code execution sandbox
│   │   ├── static_analyzer.py  # AST / pylint / mypy
│   │   └── trace_collector.py  # Runtime trace extraction
│   ├── llm/
│   │   ├── client.py        # Groq / OpenAI API wrapper
│   │   ├── prompts.py       # Prompt templates
│   │   └── root_cause.py    # Root cause analysis
│   ├── patcher/
│   │   └── generator.py     # Patch generation
│   └── validator/
│       └── runner.py        # Patch validation loop
├── frontend/                 # React dashboard (Phase 6)
├── datasets/                 # Benchmark bug samples
├── evaluation/
│   └── metrics.py           # Performance metrics
├── tests/                    # pytest test suite
├── docker/                   # Sandbox Dockerfile
├── requirements.txt
├── pyproject.toml
├── .env.example
└── .gitignore
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/your-username/NeuroTrace.git
cd NeuroTrace

# Create virtual environment
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the server
uvicorn backend.main:app --reload
```

### Verify

Open [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | App info |
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/debug` | Full debug pipeline |
| `POST` | `/api/v1/execute` | Execute code only |
| `POST` | `/api/v1/analyze` | Static analysis only |
| `POST` | `/api/v1/trace` | Runtime trace only |
| `POST` | `/api/v1/root-cause` | Root cause analysis |
| `POST` | `/api/v1/patch` | Generate patch |
| `POST` | `/api/v1/validate` | Validate patch |

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **LLM:** Groq (Llama 3), OpenAI (fallback)
- **Analysis:** Python AST, pylint, mypy
- **Execution:** subprocess (Docker stretch goal)
- **Testing:** pytest
- **Database:** SQLite (→ PostgreSQL for production)
- **Frontend:** React + Vite (Phase 6)

---

## 📊 Evaluation Metrics

| Metric | Description |
|--------|-------------|
| Localization Accuracy | % correct faulty line identified |
| Patch Success Rate | % patches that pass tests |
| Execution Success | % patches that run without error |
| Repair Accuracy | % semantically correct fixes |
| False Patch Rate | % wrong but plausible fixes |

---

## 🗓️ Development Roadmap

- [x] **v0.1.0** — Project scaffolding & API skeleton
- [ ] **v0.2.0** — Code execution sandbox
- [ ] **v0.3.0** — Static analysis engine
- [ ] **v0.4.0** — Runtime trace collector
- [ ] **v0.5.0** — LLM root cause analysis + patch generation
- [ ] **v0.6.0** — Automated patch validation loop
- [ ] **v0.7.0** — React frontend dashboard
- [ ] **v1.0.0** — Benchmark evaluation & documentation

---

## 📄 License

This project is licensed under the MIT License.