# NeuroTrace

**Autonomous AI System for Bug Localization, Root Cause Analysis, and Patch Verification**

NeuroTrace is an AI-powered debugging framework that automatically detects bugs in Python code, identifies their root cause using LLM reasoning, generates minimal patches, and validates fixes through an iterative repair loop.

---

## Features

- **Code Execution Sandbox** — Safely runs Python code in isolated subprocesses with timeout enforcement
- **Static Analysis Engine** — Combines AST parsing, pylint, and mypy for comprehensive code analysis
- **Runtime Trace Collector** — Captures exception details, variable state at crash point, and call stack
- **LLM Root Cause Analyzer** — Chain-of-thought reasoning using Groq/OpenAI to identify *why* bugs occur
- **Patch Generator** — Produces minimal code fixes with unified diff output
- **Automated Validation Loop** — Executes patched code, runs tests, and retries with LLM feedback if patches fail
- **Confidence Scoring** — Weighted formula considering execution success, test pass rate, patch minimality, and attempt count
- **React Dashboard** — Premium dark-themed UI with pipeline visualization, diff viewer, and confidence gauge
- **Benchmark Suite** — 32 curated Python bugs across 10 categories for evaluation

## Architecture

```
User submits buggy code + optional tests
    │
    ▼
┌─────────────────────────────────────────────┐
│              FastAPI Gateway                │
├─────────────┬───────────────────────────────┤
│  Sandbox    │  Static Analysis (AST/pylint) │
│  Execution  │  Runtime Trace Collector      │
├─────────────┴───────────────────────────────┤
│        LLM Root Cause Analyzer (Groq)       │
│        Patch Generator (LLM)                │
├─────────────────────────────────────────────┤
│        Patch Validator (re-execute + test)   │
│            ↻ retry loop (up to 3x)          │
├─────────────────────────────────────────────┤
│        Session Logger (SQLite)              │
│        Evaluation Metrics                   │
└─────────────────────────────────────────────┘
    │
    ▼
React Dashboard (Vite)
```

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI (async, auto-docs) |
| LLM | Groq API (Llama 3 70B) / OpenAI |
| Static Analysis | `ast`, `pylint`, `mypy` |
| Execution | `subprocess` with timeout |
| Validation | Automated test execution |
| Database | SQLite (async via aiosqlite) |
| Frontend | React + Vite |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/ksskarthik18/NeuroTrace.git
cd NeuroTrace

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Run the server
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000` with docs at `/docs`.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

### Running Tests

```bash
python -m pytest tests/ -v
```

### Running Benchmarks

```bash
# Run all 32 bugs
python -m evaluation.benchmark_runner

# Run first 5 bugs only
python -m evaluation.benchmark_runner --max 5
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/debug` | Full 6-stage debugging pipeline |
| `POST` | `/api/v1/execute` | Execute code in sandbox |
| `POST` | `/api/v1/analyze` | Static analysis only |
| `POST` | `/api/v1/trace` | Runtime trace collection |
| `POST` | `/api/v1/root-cause` | LLM root cause analysis |
| `POST` | `/api/v1/patch` | LLM patch generation |
| `POST` | `/api/v1/validate` | Full pipeline + validation |
| `GET` | `/api/v1/sessions` | List debug sessions |
| `GET` | `/api/v1/sessions/{id}` | Get session details |
| `GET` | `/api/v1/metrics` | Evaluation metrics |
| `GET` | `/api/v1/health` | Health check |

## Bug Categories (Benchmark Dataset)

| Category | Count | Examples |
|---|---|---|
| IndexError | 5 | List out of bounds, empty list pop |
| TypeError | 5 | String + int, wrong arg count |
| LogicError | 5 | Off-by-one, wrong operator |
| AttributeError | 4 | NoneType access, misspelled method |
| KeyError | 3 | Missing dict key, case mismatch |
| ValueError | 2 | Invalid int(), item not in list |
| ZeroDivisionError | 2 | Division by zero, modulo zero |
| NameError | 2 | Undefined variable, typo |
| ImportError | 1 | Wrong module import |
| RuntimeError | 1 | Infinite recursion |
| EdgeCase | 2 | Empty string, uninitialized var |

## Project Structure

```
NeuroTrace/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Environment settings
│   ├── models.py               # Pydantic data models
│   ├── database.py             # SQLAlchemy async setup
│   ├── api/routes.py           # REST endpoints (11 routes)
│   ├── debugger/
│   │   ├── sandbox.py          # Subprocess code execution
│   │   ├── static_analyzer.py  # AST + pylint + mypy
│   │   └── trace_collector.py  # Runtime trace injection
│   ├── llm/
│   │   ├── client.py           # Groq/OpenAI API wrapper
│   │   ├── prompts.py          # Chain-of-thought prompts
│   │   └── root_cause.py       # Root cause analysis
│   ├── patcher/
│   │   └── generator.py        # Patch generation + diff
│   └── validator/
│       └── runner.py           # Iterative validation loop
├── frontend/                   # React + Vite dashboard
├── evaluation/
│   ├── metrics.py              # Metric computation
│   └── benchmark_runner.py     # Batch evaluation script
├── datasets/
│   └── bugs.json               # 32 curated Python bugs
├── tests/                      # pytest test suite (65+ tests)
├── requirements.txt
└── pyproject.toml
```

## Confidence Scoring

The validation confidence is calculated using a weighted formula:

```
confidence = 0.35 × execution_success
           + 0.35 × test_pass_rate
           + 0.15 × patch_minimality
           + 0.15 × attempt_penalty
```

- **Execution success** (35%): Does the patched code run without errors?
- **Test pass rate** (35%): What percentage of provided tests pass?
- **Patch minimality** (15%): Smaller diffs score higher
- **Attempt penalty** (15%): First-attempt fixes score higher than retries

## License

MIT