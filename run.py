"""
Entrypoint to run the FastAPI Ollama bridge server.
"""
import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    is_production = os.getenv("APP_ENV", "development").strip().lower() == "production"
    print(f"==================================================")
    print(f" FastAPI Ollama Service (Qwen 3.5 2B)")
    print(f" Server URL: http://{host}:{port}")
    if not is_production:
        print(f" Swagger Docs: http://{host}:{port}/docs")
    print(f"==================================================")
    uvicorn.run("app.main:app", host=host, port=port, reload=not is_production)
