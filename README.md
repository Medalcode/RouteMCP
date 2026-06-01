# RouteMCP — AI Model Router MCP Server

Servidor MCP que clasifica tareas y enruta prompts al mejor modelo de IA disponible. Soporta Google Gemini, Groq y Cerebras con failover automático.

## How It Works / Cómo Funciona

1. **Classify** — Analiza el prompt usando IA (Groq `llama-3.1-8b`) con un *fallback* inteligente a palabras clave para detectar el tipo de tarea (code, math, reasoning, creative, vision, long_context, multilingual, general).
2. **Route** — Selecciona el mejor modelo según la tarea usando las prioridades configuradas en `config.json`.
3. **Fallback** — Si el mejor modelo falla (API error, timeout, rate limit 429 con Retry-After), prueba el siguiente en la lista.
4. **Ask** — Envía el prompt directamente a un modelo específico.
5. **Compare** — Envía el mismo prompt a múltiples modelos en paralelo (concurrencia) y compara resultados rápidamente.

### Routing Logic / Lógica de Enrutamiento (Vía `config.json`)

| Task Type | Preferred Models |
|---|---|
| code | gemini-2.5-pro → llama-3.3-70b → gemini-2.5-flash → cerebras-llama-3.3-70b |
| reasoning | gemini-2.5-pro → llama-3.3-70b → gemini-2.5-flash |
| math | gemini-2.5-pro → gemini-2.5-flash → llama-3.3-70b |
| creative | gemini-2.0-flash → gemini-3-flash-preview → mixtral-8x7b |
| general | gemini-2.0-flash → gemini-2.5-flash → llama-3.3-70b → gemini-3-flash-preview |
| vision | gemini-2.5-pro → gemini-2.0-flash → gemini-2.5-flash → gemini-3-flash-preview |
| long_context | gemini-2.5-pro → gemini-2.0-flash → gemini-2.5-flash → gemini-3-flash-preview |
| speed | llama-3.1-8b → cerebras-llama-3.3-70b → llama-3.3-70b → gemini-2.0-flash |
| multilingual | gemini-2.0-flash → mixtral-8x7b → gemini-2.5-flash |

## Features / Funcionalidades

| Tool / Herramienta | Description / Descripción |
|---|---|
| `ask` | Envía un prompt a un modelo específico |
| `models` | Lista modelos disponibles con capacidades, contexto y costo |
| `classify_task` | Clasifica un prompt y muestra los modelos recomendados |
| `route` | Enruta automáticamente al mejor modelo según la tarea |
| `compare` | Compara respuestas de múltiples modelos para un mismo prompt (Ejecución en paralelo) |

> **Nota sobre Configuración:** Toda la lógica de enrutamiento, lista de modelos y palabras clave se genera y lee desde un archivo `config.json` en la raíz del proyecto. ¡Puedes editarlo para personalizar tus modelos sin tocar el código fuente!

## Providers / Proveedores

| Provider | API Key | Models |
|---|---|---|
| **Google Gemini** | `GEMINI_API_KEY` | gemini-2.5-pro, gemini-2.0-flash, gemini-2.5-flash, gemini-3-flash-preview |
| **Groq** | `GROQ_API_KEY` | llama-3.3-70b, llama-3.1-8b, mixtral-8x7b |
| **Cerebras** | `CEREBRAS_API_KEY` | cerebras-llama-3.3-70b |

## Tech Stack

- **Python** — `>=3.11`
- **Framework**: `mcp` (FastMCP) via stdio JSON-RPC
- **HTTP**: `httpx` (async) con manejo de límites de tasa (`Retry-After`)
- **Classifier**: Híbrido (LLM basado en Groq `llama-3.1-8b` + Keyword-based fallback)
- **Configuration**: Externa vía `config.json`

## Quick Start

```bash
# Configurar API keys
export GEMINI_API_KEY="..."
export GROQ_API_KEY="..."
export CEREBRAS_API_KEY="..."

# Instalar
pip install mcp httpx

# Ejecutar servidor
python server.py
```

### Ejemplos

```python
# Listar modelos disponibles
result = await session.call_tool("models", {})

# Clasificar tarea
result = await session.call_tool("classify_task", {"prompt": "write a Python function"})

# Enrutar automáticamente
result = await session.call_tool("route", {"prompt": "explain quantum computing"})

# Preguntar a un modelo específico
result = await session.call_tool("ask", {"model": "gemini-2.0-flash", "prompt": "hello"})

# Comparar modelos
result = await session.call_tool("compare", {
    "prompt": "solve 2+2",
    "models": "gemini-2.0-flash,llama-3.3-70b"
})
```

## Project Structure

```
routemcp/
├── server.py                 # MCP server entry point (tools)
├── router/
│   ├── __init__.py
│   ├── engine.py             # RouterEngine: routing & fallback logic, async compare
│   ├── classifier.py         # Task classifier (LLM Hybrid + keyword scoring)
│   ├── models.py             # Model definitions & config.json loader
│   └── providers/
│       ├── __init__.py
│       ├── base.py           # AIProvider base class & ProviderError
│       ├── google_provider.py   # Google Gemini API
│       ├── groq_provider.py     # Groq API
│       └── cerebras_provider.py # Cerebras API
├── client.py                 # Test client CLI
└── pyproject.toml
```
