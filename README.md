# Local Service AI

A FastAPI application and web chat UI powered by a local Ollama model. Ask about services and providers listed in the SQLite database.

## Features

- **SQLite-scoped AI chat**: Answers service questions from SQLite provider records only.
- **SQLite service discovery**: Analyzes service requests and returns matching providers from the SQLite directory.
- **Safety guidance**: Detects electrical hazards and provides a safety warning.
- **REST API**: App-scoped chat, generation, service analysis, and provider discovery.
- **Local web UI**: Served at `http://127.0.0.1:8000/`.

> **Booking limitation:** SQLite records contain provider directory details only, not prices or availability. The app lists matching providers but does not confirm bookings.

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

4. The provider directory uses SQLite. Set `PROVIDER_DATABASE_PATH` in `.env` to override the default `local_service_ai.sqlite3` database file.

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

The web app requests the browser's location when it opens and sends coordinates with service requests. Distance is calculated only for SQLite provider records that have coordinates; other records are shown with their stored area. Location access is one-time per page load; use the crosshair icon to refresh it. If access is denied or unavailable, the app uses fallback coordinates. Browser geolocation requires localhost or a secure HTTPS origin.

After location is received, the displayed place name is resolved locally from the offline GeoNames data bundled with `reverse-geocoder`; coordinates are not sent to an external geocoding service. This reports the nearest named city/town, not a street address. Model answers use only service categories and provider records from SQLite.

## Using the assistant

Ask only about services and providers present in the SQLite database. For example:

> Find a plumbing provider in Aluva.

Service categories and provider details come from SQLite. If no provider row matches the requested category, the app says so instead of suggesting a built-in demo provider. Prices and available appointment slots are not in the database, so booking requests only return matching directory records.

## API

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` or `/ui` | Serves the chat UI |
| `GET` | `/health` | Checks Ollama connectivity |
| `GET` | `/api/models` | Lists installed Ollama models |
| `POST` | `/api/chat` | Sends a chat completion request; supports streaming |
| `POST` | `/api/generate` | Sends a text-generation request |
| `POST` | `/api/service-ai/analyze` | Analyzes a service request and matches SQLite providers |
| `POST` | `/api/service-ai/follow-up` | Submits a service-analysis clarification |
| `POST` | `/api/service-ai/recommend` | Matches a service category to SQLite providers |
| `GET` | `/api/service-ai/categories` | Lists service categories present in SQLite |
| `GET` | `/api/service-ai/catalog` | Groups SQLite providers by service category |
| `GET` | `/api/service-ai/providers` | Lists SQLite providers; optionally filter with `?category=home_cleaning` |
| `GET` | `/api/location/resolve?latitude=9.94&longitude=76.26` | Resolves coordinates to a nearby place name offline |
| `GET` | `/api/service-ai/session/{session_id}` | Returns session details |
| `GET` | `/docs` | Opens Swagger API documentation |

Before a provider CSV has been imported, service and provider lookups return no results. They never fall back to built-in demo records.

### Import provider CSV data

The CSV must include `service_category`, `shop_name`, `contact_name`, `phone`, `address`, `area`, `latitude`, `longitude`, `source_url`, and `verification_status`. Import it with:

```cmd
python import_providers.py --csv "C:\path\to\providers.csv"
```

Imports are repeatable: records are upserted using the service category, shop name, and phone. Coordinates are optional but range-validated when present; provider names and areas are required. Pass `--database "C:\path\to\providers.sqlite3"` to override the configured/default SQLite file for one import.

### Chat request example

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5:2b",
    "messages": [
      {"role": "user", "content": "Which plumbing providers are listed?"}
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
