# Local Service AI

A FastAPI application and web chat UI powered by a local Ollama model. Ask general questions, describe a home-service problem, or request a service booking in natural language.

## Features

- **General AI chat**: Answers open-ended questions using the local model and recent conversation context.
- **Service discovery**: Analyzes service issues, recommends catalog services and nearby providers, and asks follow-up questions when needed.
- **Booking agent demo**: Understands requests such as “Book house cleaning at 2pm, cheapest,” checks available slots, and ranks by estimated total price, speed, or rating.
- **Safety guidance**: Detects electrical hazards and provides a safety warning.
- **REST API**: Chat, generation, service analysis, provider discovery, and pricing endpoints.
- **Local web UI**: Served at `http://127.0.0.1:8000/`.

> **Booking limitation:** Service providers and availability come from a local demo catalog. The booking agent prepares a demo booking summary; it does not contact a provider or create a real-world reservation.

## Requirements

1. Install [Ollama](https://ollama.com/) and make sure it is running.
2. Download the configured model:

   ```cmd
   ollama pull qwen3.5:2b
   ```

3. Install the Python dependencies:

   ```cmd
   python -m pip install -r requirements.txt
   ```

## Run

Start the server using:

```cmd
start.bat
```

Or run it manually:

```cmd
python run.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser. The interactive chat requires the server and Ollama to be running.

## Using the assistant

Type a question directly to get an AI-generated answer. To discover or book a local service, include the service and any preferences you have, such as a time or price priority. For example:

> Book house cleaning at 2pm, cheapest option.

The assistant checks the local catalog for a matching provider and time. If the requested slot is unavailable, it reports available alternatives rather than claiming the booking succeeded. For a demo booking, the result shows an estimated price and clearly indicates that no provider was contacted.

## API

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` or `/ui` | Serves the chat UI |
| `GET` | `/health` | Checks Ollama connectivity |
| `GET` | `/api/models` | Lists installed Ollama models |
| `POST` | `/api/chat` | Sends a chat completion request; supports streaming |
| `POST` | `/api/generate` | Sends a text-generation request |
| `POST` | `/api/service-ai/analyze` | Answers general questions or analyzes a service/booking request |
| `POST` | `/api/service-ai/follow-up` | Submits a service-analysis clarification |
| `POST` | `/api/service-ai/recommend` | Gets service and provider recommendations |
| `GET` | `/api/service-ai/categories` | Lists supported service categories |
| `GET` | `/api/service-ai/catalog` | Lists catalog services; optionally filter with `?category=home_cleaning` |
| `GET` | `/api/service-ai/providers` | Lists providers; optionally filter with `?category=home_cleaning` |
| `GET` | `/api/service-ai/session/{session_id}` | Returns session details |
| `GET` | `/docs` | Opens Swagger API documentation |

### Chat request example

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

## Configuration

Set these values in a `.env` file to override the defaults:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
DEFAULT_MODEL=qwen3.5:2b
HOST=127.0.0.1
PORT=8000
```

## Tests

Run the focused routing and booking tests with:

```cmd
python -m unittest -v test_agentic_behavior
```

The end-to-end API checks in `test_service_ai.py` require the app server to be running.
