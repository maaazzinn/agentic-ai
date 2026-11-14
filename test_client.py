"""
Test client to verify FastAPI Ollama Bridge endpoints.
"""
import sys
import json
import httpx

BASE_URL = "http://127.0.0.1:8000"


def test_health():
    print("\n--- 1. Testing Health Endpoint (/health) ---")
    try:
        resp = httpx.get(f"{BASE_URL}/health", timeout=10.0)
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Failed to connect to FastAPI server: {e}")
        return False


def test_models():
    print("\n--- 2. Testing Models Endpoint (/api/models) ---")
    try:
        resp = httpx.get(f"{BASE_URL}/api/models", timeout=10.0)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        models = [m.get("name") for m in data.get("models", [])]
        print(f"Available Ollama Models: {models}")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False


def test_chat():
    print("\n--- 3. Testing Chat Endpoint (/api/chat) ---")
    payload = {
        "model": "qwen3.5:2b",
        "messages": [
            {"role": "system", "content": "You are a concise AI assistant. Answer in 1-2 sentences."},
            {"role": "user", "content": "What is the capital of France and what is it known for?"}
        ],
        "stream": False,
        "temperature": 0.5
    }
    try:
        print("Sending chat request to qwen3.5:2b...")
        resp = httpx.post(f"{BASE_URL}/api/chat", json=payload, timeout=60.0)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Assistant Response:\n{data.get('message', {}).get('content')}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Failed: {e}")
        return False


def test_chat_streaming():
    print("\n--- 4. Testing Chat Streaming Endpoint (/api/chat with stream=True) ---")
    payload = {
        "model": "qwen3.5:2b",
        "messages": [
            {"role": "user", "content": "Give me a 3-word slogan for AI."}
        ],
        "stream": True,
        "temperature": 0.7
    }
    try:
        print("Streaming response: ", end="", flush=True)
        with httpx.stream("POST", f"{BASE_URL}/api/chat", json=payload, timeout=60.0) as resp:
            for line in resp.iter_lines():
                if line.startswith("data: "):
                    raw_data = line[6:]
                    try:
                        chunk = json.loads(raw_data)
                        content = chunk.get("message", {}).get("content", "")
                        print(content, end="", flush=True)
                    except json.JSONDecodeError:
                        pass
        print("\nStreaming finished successfully!")
        return True
    except Exception as e:
        print(f"\nFailed: {e}")
        return False


def test_generate():
    print("\n--- 5. Testing Generate Endpoint (/api/generate) ---")
    payload = {
        "model": "qwen3.5:2b",
        "prompt": "Count from 1 to 5.",
        "stream": False
    }
    try:
        print("Sending generate request to qwen3.5:2b...")
        resp = httpx.post(f"{BASE_URL}/api/generate", json=payload, timeout=60.0)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Model Response:\n{data.get('response')}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Failed: {e}")
        return False


if __name__ == "__main__":
    print(f"Starting test suite against {BASE_URL}...")
    if not test_health():
        print("\nHealth check failed. Make sure FastAPI server and Ollama are running.")
        sys.exit(1)
    test_models()
    test_chat()
    test_chat_streaming()
    test_generate()
    print("\nAll tests completed!")
