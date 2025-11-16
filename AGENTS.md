# RouteMCP — Agent Guide

## Commands
```bash
source .venv/bin/activate
python client.py models                    # list available models
python client.py classify "write code"     # test classifier
python client.py route "hello"             # auto-route to best model
python client.py ask gemini-2.0-flash "hi" # direct model query
```

## Critical Quirks

- **No `requirements.txt`** — `.venv` is the source of truth. Activate before running.
- **API keys required** as environment variables:
  - `GEMINI_API_KEY` — Google Gemini (all Gemini models)
  - `GROQ_API_KEY` — Groq (Llama 3.3, Mixtral, Llama 3.1)
  - `CEREBRAS_API_KEY` — Cerebras (Llama 3.3 70B)
- **Without API keys**, `models()` returns "No models available" and `route()`/`ask()` fail. The server starts but is non-functional.
- **Classifier is keyword-based** (multilingual EN/ES). It scores prompts against keyword lists for: code, math, reasoning, creative, vision, long_context, multilingual. Falls back to "general" if no keywords match.
- **Routing fallback chain**: if the best model fails (API error, timeout), it tries the next in `TASK_ROUTING` priority list. If all fail, raises `ProviderError`.
- **Groq model IDs** are internally mapped (e.g., `llama-3.3-70b` → `llama-3.3-70b-versatile`). Use the short IDs (`llama-3.3-70b`, `llama-3.1-8b`, `mixtral-8x7b`), not the full API model names.
- **Cerebras** only exposes one model (`llama3.3-70b`) — the `model` parameter is ignored for Cerebras calls.
