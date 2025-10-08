# Azure OpenAI × Week-21 Challenge — Scaffold

This repo is a minimal scaffold:

- **Azure OpenAI** for reasoning, EDA explanations, and report generation.
- **Azure ML** for the classifier (customer satisfaction).
- **FastAPI app** orchestrates tool calls.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
