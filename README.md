# FastAPI + Ollama (Qwen 3.5 2B) Bridge

A lightweight, asynchronous FastAPI service and modern Web UI connecting directly to a local Ollama instance running the **`qwen3.5:2b`** model.

---

## 🚀 Features

- **Interactive Web UI**: A ChatGPT-style chat interface with real-time token streaming, markdown formatting, syntax-highlighted code blocks with 1-click copy, and prompt templates.
- **Real-Time Streaming**: Supports Server-Sent Events (SSE) streaming for fast token-by-token responses.
- **REST Endpoints**: Complete endpoints for chat completions (`/api/chat`), text generation (`/api/generate`), and model discovery (`/api/models`).
- **Interactive API Docs**: Built-in Swagger UI at `http://127.0.0.1:8000/docs`.
- **Zero Config UI**: UI is served directly at `http://127.0.0.1:8000/` or can be opened locally as `index.html`.

---

## 📋 Prerequisites

1. **Ollama**: Ensure Ollama is running on your machine.
2. **Model**: Pull the model (if not already downloaded):
   ```bash
   ollama pull qwen3.5:2b
   ```

---

## ⚡ Quick Start

### 1. Launch the Server

Run the startup batch script:
```cmd
start.bat
```
*Or manually:*
```cmd
.\.venv\Scripts\activate
python run.py
```

The server starts on `http://127.0.0.1:8000`.

### 2. Open the Web UI

Open your web browser and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

You can also directly double-click `index.html` in your file explorer.

---

## 🛠️ API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` or `/ui` | Opens the interactive Web Chat UI |
| `GET` | `/health` | Health check verifying Ollama connectivity |
| `GET` | `/api/models` | Lists all downloaded Ollama models |
| `POST` | `/api/chat` | Chat completion (supports both streaming and JSON response) |
| `POST` | `/api/generate` | Direct prompt completion |
| `GET` | `/docs` | Interactive Swagger API documentation |

### Example cURL Request (Chat Completion)

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5:2b",
    "messages": [
      {"role": "user", "content": "Explain agentic AI in two sentences."}
    ],
    "stream": false,
    "temperature": 0.7
  }'
```

---

## ⚙️ Configuration (`.env`)

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
DEFAULT_MODEL=qwen3.5:2b
HOST=127.0.0.1
PORT=8000
```
