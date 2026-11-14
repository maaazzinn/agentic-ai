import os
import json
import logging
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from pydantic import BaseModel, Field
import httpx

# Local Service AI Services
from services.analyzer import (
    analyze_problem_with_qwen,
    ProblemAnalysis,
    SUPPORTED_CATEGORIES,
    is_local_service_request,
)
from services.mcp_catalog import (
    mcp_search_catalog,
    mcp_find_providers,
    mcp_get_pricing_estimate,
    SERVICES_CATALOGUE,
    SERVICE_PROVIDERS,
)
from services.recommendation import generate_recommendations
from services.session_manager import (
    get_or_create_session,
    get_session,
    SessionState,
)
from services.agent_booking import execute_agent_booking

# Load environment variables
load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen3.5:2b")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
FORCE_GPU = os.getenv("FORCE_GPU", "true").lower() in ("true", "1", "yes")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fastapi_ollama")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event to verify Ollama availability on startup."""
    logger.info("Initializing Local Service AI & Ollama Bridge...")
    logger.info(f"Ollama Target URL: {OLLAMA_BASE_URL}")
    logger.info(f"Configured Default Model: {DEFAULT_MODEL}")
    
    # Check if Ollama is accessible
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                models = [m.get("name") for m in resp.json().get("models", [])]
                logger.info(f"Connected to Ollama! Available models: {models}")
                if DEFAULT_MODEL in models or any(m.startswith(DEFAULT_MODEL) for m in models):
                    logger.info(f"Target model '{DEFAULT_MODEL}' is ready!")
                else:
                    logger.warning(
                        f"Target model '{DEFAULT_MODEL}' not found in Ollama models list. "
                        f"Make sure to pull it using: ollama pull {DEFAULT_MODEL}"
                    )
            else:
                logger.warning(f"Ollama responded with status {resp.status_code}")
    except Exception as e:
        logger.warning(
            f"Could not connect to Ollama on startup ({e}). "
            f"Please ensure Ollama is running at {OLLAMA_BASE_URL}"
        )
    yield
    logger.info("Local Service AI shutting down.")


app = FastAPI(
    title="Local Service AI (Qwen 3.5 2B + MCP)",
    description=(
        "Next-generation local service discovery platform powered by local "
        f"**{DEFAULT_MODEL}** and MCP tools. Understands natural language problem descriptions, "
        "processes images, handles safety emergencies, and matches verified local service providers."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for external/frontend consumers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# Pydantic Schemas - Chat & Generation
# =====================================================================
class Message(BaseModel):
    role: str = Field(..., description="Role of the sender: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message text content")


class ChatRequest(BaseModel):
    messages: List[Message] = Field(
        ...,
        description="Conversation history",
        example=[
            {"role": "system", "content": "You are a concise, helpful AI assistant."},
            {"role": "user", "content": "What is agentic AI?"},
        ],
    )
    model: Optional[str] = Field(
        default=DEFAULT_MODEL,
        description="Ollama model tag to query",
        example=DEFAULT_MODEL,
    )
    stream: Optional[bool] = Field(
        default=False,
        description="Whether to stream the response token-by-token",
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature",
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional Ollama runtime options",
    )


class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for the model")
    system: Optional[str] = Field(default=None, description="Optional system instruction")
    model: Optional[str] = Field(default=DEFAULT_MODEL, description="Ollama model tag")
    stream: Optional[bool] = Field(default=False, description="Streaming mode")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    options: Optional[Dict[str, Any]] = Field(default=None)


# =====================================================================
# Pydantic Schemas - Local Service AI Modules
# =====================================================================
class ProblemInputRequest(BaseModel):
    problem_description: str = Field(..., description="Natural language description of the customer issue")
    image_base64: Optional[str] = Field(default=None, description="Optional base64 encoded photo of appliance/problem")
    session_id: Optional[str] = Field(default=None, description="Optional session ID to track continuous turn")
    latitude: Optional[float] = Field(default=12.9716, description="User GPS latitude (default: Bangalore)")
    longitude: Optional[float] = Field(default=77.5946, description="User GPS longitude (default: Bangalore)")
    city: Optional[str] = Field(default="Bangalore (Central)", description="User city or neighborhood")
    # Conversation history for multi-turn context (list of {role, content} dicts)
    conversation_history: Optional[List[Dict[str, Any]]] = Field(default=None)


class FollowUpRequest(BaseModel):
    session_id: str = Field(..., description="Active session ID")
    clarification: str = Field(..., description="Customer's answer to the follow-up question")
    property_size: Optional[str] = Field(default=None, description="Optional property size (e.g. 1BHK, 2BHK)")


class DirectRecommendRequest(BaseModel):
    category: str = Field(..., description="Service category")
    issue_type: Optional[str] = Field(default="general_repair", description="Specific issue type")
    latitude: Optional[float] = Field(default=12.9716)
    longitude: Optional[float] = Field(default=77.5946)
    emergency: Optional[bool] = Field(default=False)


# =====================================================================
# Status & Helper Functions
# =====================================================================
async def get_gpu_status() -> Dict[str, Any]:
    """Inspects running models in Ollama to verify GPU offloading and VRAM allocation."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/ps")
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("models", [])
                gpu_models = []
                for m in models:
                    size = m.get("size", 0)
                    size_vram = m.get("size_vram", 0)
                    pct = (size_vram / size * 100) if size > 0 else 0
                    gpu_models.append({
                        "name": m.get("name"),
                        "size_vram_mb": round(size_vram / (1024 * 1024), 1),
                        "size_total_mb": round(size / (1024 * 1024), 1),
                        "vram_percentage": f"{pct:.1f}%",
                        "is_gpu": pct > 0,
                        "runner": m.get("runner", "llamacpp"),
                        "details": m.get("details", {}),
                    })
                is_active_gpu = any(gm["is_gpu"] for gm in gpu_models)
                return {
                    "gpu_enforced": FORCE_GPU,
                    "active_on_gpu": is_active_gpu,
                    "running_models": gpu_models,
                    "gpu_summary": f"{gpu_models[0]['vram_percentage']} GPU" if gpu_models else "Idle (GPU Ready)",
                }
    except Exception as exc:
        return {
            "gpu_enforced": FORCE_GPU,
            "active_on_gpu": False,
            "error": str(exc),
        }
    return {
        "gpu_enforced": FORCE_GPU,
        "active_on_gpu": False,
        "running_models": [],
        "gpu_summary": "Idle (GPU Ready)",
    }


async def check_ollama_status() -> Dict[str, Any]:
    """Helper to check connectivity to Ollama."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                models = [m.get("name") for m in resp.json().get("models", [])]
                has_default = DEFAULT_MODEL in models or any(m.startswith(DEFAULT_MODEL) for m in models)
                gpu_info = await get_gpu_status()
                return {
                    "online": True,
                    "default_model_installed": has_default,
                    "available_models": models,
                    "gpu": gpu_info,
                }
    except Exception as exc:
        return {
            "online": False,
            "error": str(exc),
            "hint": f"Ensure Ollama is running at {OLLAMA_BASE_URL}",
        }
    return {"online": False, "error": "Unexpected Ollama response"}


# =====================================================================
# UI & Core Health Endpoints
# =====================================================================
@app.get("/", summary="Local Service AI Web UI", tags=["UI"], response_class=FileResponse)
@app.get("/ui", summary="Local Service AI Web UI", tags=["UI"], response_class=FileResponse)
async def serve_ui():
    """Serves the interactive Local Service AI Web UI."""
    ui_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(ui_path):
        return FileResponse(ui_path)
    return JSONResponse({"message": "UI not found, please check index.html"}, status_code=404)


@app.get("/health", summary="Health Check", tags=["Health"])
async def health_check():
    status_info = await check_ollama_status()
    if not status_info.get("online"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "message": f"Ollama is unreachable at {OLLAMA_BASE_URL}",
                "error": status_info.get("error"),
            },
        )
    return {
        "status": "healthy",
        "app": "Local Service AI",
        "ollama": status_info,
    }


@app.get("/api/gpu", summary="GPU Acceleration Status", tags=["GPU"])
async def gpu_status():
    return await get_gpu_status()


@app.get("/api/models", summary="List Ollama Models", tags=["Models"])
async def list_models():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Ollama returned status {resp.status_code}: {resp.text}",
                )
            return resp.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot connect to Ollama at {OLLAMA_BASE_URL}.",
        )


# =====================================================================
# Local Service AI - Application Endpoints
# =====================================================================
@app.post("/api/service-ai/analyze", summary="Analyze Customer Problem with Qwen", tags=["Local Service AI"])
async def analyze_problem(req: ProblemInputRequest):
    """
    Step 1 & 2 in Customer Journey:
    Customer inputs natural-language problem + optional photo.
    Qwen analyzes the problem, categorizes it, identifies urgency & safety risks,
    and returns recommendations (or follow-up questions if needed).
    """
    session = get_or_create_session(req.session_id)
    session.initial_query = req.problem_description
    session.has_image = bool(req.image_base64)
    if req.latitude and req.longitude:
        session.location = {"lat": req.latitude, "lon": req.longitude}
    if req.city:
        session.city_name = req.city

    if not is_local_service_request(req.problem_description, bool(req.image_base64)):
        messages = [{
            "role": "system",
            "content": (
                "You are a helpful, knowledgeable AI assistant. Answer the user's actual "
                "question directly and accurately. Do not rely on canned examples, invent "
                "facts, or claim to have performed actions or contacted service providers."
            ),
        }]
        if req.conversation_history:
            for turn in req.conversation_history[-12:]:
                role = turn.get("role")
                content = turn.get("content")
                if role in ("user", "assistant") and isinstance(content, str) and content.strip():
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": req.problem_description})

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": DEFAULT_MODEL,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": 0.7},
                    },
                )
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Ollama returned status {resp.status_code}: {resp.text}",
                    )
                answer = resp.json().get("message", {}).get("content", "").strip()
                if not answer:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Ollama returned an empty answer.",
                    )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Cannot connect to Ollama at {OLLAMA_BASE_URL}: {exc}",
            ) from exc

        return {
            "session_id": session.session_id,
            "state": session.state,
            "mode": "chat",
            "answer": answer,
        }

    # Invoke Qwen local model with structured analysis
    analysis = await analyze_problem_with_qwen(
        user_input=req.problem_description,
        image_base64=req.image_base64,
        conversation_history=req.conversation_history,
        ollama_base_url=OLLAMA_BASE_URL,
        model_name=DEFAULT_MODEL,
        timeout=60.0,
    )
    session.analysis = analysis

    # ── AGENT MODE: auto-book if intent == book ──────────────────────
    if analysis.intent == "book" and not analysis.requires_followup:
        agent_result = execute_agent_booking(
            analysis=analysis,
            user_lat=session.location["lat"],
            user_lon=session.location["lon"],
        )
        session.state = SessionState.RECOMMENDED
        return {
            "session_id": session.session_id,
            "state": session.state,
            "mode": "agent",
            "analysis": analysis.model_dump(),
            "agent_result": agent_result,
        }

    # Generate initial MCP recommendations
    recommendations = generate_recommendations(
        analysis=analysis,
        user_lat=session.location["lat"],
        user_lon=session.location["lon"],
    )
    session.recommendations = recommendations

    if analysis.requires_followup:
        session.state = SessionState.AWAITING_FOLLOWUP
    else:
        session.state = SessionState.RECOMMENDED

    return {
        "session_id": session.session_id,
        "state": session.state,
        "analysis": analysis.model_dump(),
        "recommendations": recommendations,
        "location": session.location,
        "city_name": session.city_name,
    }


@app.post("/api/service-ai/follow-up", summary="Submit Follow-Up Clarification", tags=["Local Service AI"])
async def submit_follow_up(req: FollowUpRequest):
    """
    Step 4 & 5 in Customer Journey:
    Customer answers follow-up clarification question asked by Qwen.
    Recommendation engine updates provider ranking and pricing accordingly.
    """
    session = get_session(req.session_id)
    if not session or not session.analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {req.session_id} not found or expired.",
        )

    session.follow_up_answer = req.clarification

    # Re-analyze with full conversation context so Qwen knows what was said before
    history = [
        {"role": "user", "content": session.initial_query},
        {"role": "assistant", "content": session.analysis.follow_up_question or "Could you clarify?"},
    ]
    refined_analysis = await analyze_problem_with_qwen(
        user_input=req.clarification,
        conversation_history=history,
        ollama_base_url=OLLAMA_BASE_URL,
        model_name=DEFAULT_MODEL,
        timeout=60.0,
    )
    # Carry over original category/intent if the clarification doesn't change them
    if refined_analysis.category == "other" and session.analysis.category != "other":
        refined_analysis.category = session.analysis.category
        refined_analysis.issue_type = session.analysis.issue_type
    if refined_analysis.intent == "discover":
        refined_analysis.intent = session.analysis.intent
    if not refined_analysis.time_preference:
        refined_analysis.time_preference = session.analysis.time_preference
    refined_analysis.booking_priority = refined_analysis.booking_priority or session.analysis.booking_priority
    session.analysis = refined_analysis

    # Agent mode after follow-up
    if refined_analysis.intent == "book" and not refined_analysis.requires_followup:
        agent_result = execute_agent_booking(
            analysis=refined_analysis,
            user_lat=session.location["lat"],
            user_lon=session.location["lon"],
        )
        session.state = SessionState.RECOMMENDED
        return {
            "session_id": session.session_id,
            "state": session.state,
            "mode": "agent",
            "analysis": refined_analysis.model_dump(),
            "agent_result": agent_result,
            "clarification_received": req.clarification,
        }

    # Discover mode — regenerate recommendations
    recommendations = generate_recommendations(
        analysis=refined_analysis,
        user_lat=session.location["lat"],
        user_lon=session.location["lon"],
        user_clarification=req.clarification,
        property_size=req.property_size,
    )
    session.recommendations = recommendations
    session.state = SessionState.RECOMMENDED

    return {
        "session_id": session.session_id,
        "state": session.state,
        "mode": "discover",
        "analysis": session.analysis.model_dump(),
        "recommendations": recommendations,
        "clarification_received": req.clarification,
    }


@app.post("/api/service-ai/recommend", summary="Direct MCP Tool Discovery", tags=["Local Service AI"])
async def direct_recommend(req: DirectRecommendRequest):
    """
    MCP-based tool endpoint to directly query catalog & rank nearby providers.
    """
    dummy_analysis = ProblemAnalysis(
        problem_summary=f"Direct query for {req.category}",
        category=req.category,
        issue_type=req.issue_type or "general",
        confidence=1.0,
        safety_warning="DANGER: High voltage hazard. Do not touch!" if req.emergency else None,
    )
    return generate_recommendations(
        analysis=dummy_analysis,
        user_lat=req.latitude or 12.9716,
        user_lon=req.longitude or 77.5946,
    )


@app.get("/api/service-ai/categories", summary="Supported Service Categories", tags=["Local Service AI"])
async def get_categories():
    """Returns the list of supported service categories and metadata."""
    category_meta = [
        {"id": "plumbing", "name": "Plumbing", "icon": "🚰", "examples": "Tap leak, blocked drain, pipe burst"},
        {"id": "electrical", "name": "Electrical", "icon": "⚡", "examples": "Burnt socket, sparking switch, tripped MCB"},
        {"id": "ac_repair", "name": "AC Repair", "icon": "❄️", "examples": "Not cooling, gas refill, deep foam jet service"},
        {"id": "appliance_repair", "name": "Appliance Repair", "icon": "🧺", "examples": "Washing machine noise, fridge cooling"},
        {"id": "home_cleaning", "name": "Home Cleaning", "icon": "🧹", "examples": "2BHK deep clean, bathroom & kitchen sanitize"},
        {"id": "car_wash", "name": "Car Wash", "icon": "🚗", "examples": "Doorstep foam wash & interior vacuuming"},
        {"id": "painting", "name": "Painting", "icon": "🎨", "examples": "Wall repainting, waterproofing"},
        {"id": "carpentry", "name": "Carpentry", "icon": "🪚", "examples": "Door hinges, furniture assembly"},
        {"id": "pest_control", "name": "Pest Control", "icon": "🐜", "examples": "Cockroach & termite management"},
    ]
    return {"categories": category_meta}


@app.get("/api/service-ai/catalog", summary="Full Service Catalogue", tags=["Local Service AI"])
async def get_catalog(category: Optional[str] = None):
    """Returns services from the MCP catalogue."""
    if category:
        return [s for s in SERVICES_CATALOGUE if s["category"].lower() == category.lower()]
    return SERVICES_CATALOGUE


@app.get("/api/service-ai/providers", summary="Provider Directory", tags=["Local Service AI"])
async def get_providers(category: Optional[str] = None):
    """Returns verified local providers."""
    if category:
        return [p for p in SERVICE_PROVIDERS if p["category"].lower() == category.lower()]
    return SERVICE_PROVIDERS


@app.get("/api/service-ai/session/{session_id}", summary="Get Session Details", tags=["Local Service AI"])
async def get_session_info(session_id: str):
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    return sess.to_dict()


@app.post("/api/service-ai/evaluate", summary="Run Evaluation Benchmark Suite", tags=["Evaluation"])
async def run_evaluation_benchmark():
    """Triggers the automated Qwen evaluation suite across all 5 capabilities and scenarios."""
    from evaluate_qwen import run_evaluation
    report = await run_evaluation()
    return report


# =====================================================================
# Chat & Generate Endpoints (Standard Bridge preserved)
# =====================================================================
@app.post("/api/chat", summary="Chat Completion with Qwen", tags=["Inference"])
async def chat(request: ChatRequest):
    model_name = request.model or DEFAULT_MODEL
    runtime_options = dict(request.options) if request.options else {}
    if FORCE_GPU and "num_gpu" not in runtime_options:
        runtime_options["num_gpu"] = 99
    if request.temperature is not None:
        runtime_options["temperature"] = request.temperature

    ollama_payload = {
        "model": model_name,
        "messages": [msg.model_dump() for msg in request.messages],
        "stream": request.stream,
        "options": runtime_options,
    }

    if request.stream:
        async def stream_generator():
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    async with client.stream(
                        "POST",
                        f"{OLLAMA_BASE_URL}/api/chat",
                        json=ollama_payload,
                    ) as resp:
                        if resp.status_code != 200:
                            err_content = await resp.aread()
                            yield f"data: {json.dumps({'error': err_content.decode()})}\n\n"
                            return

                        async for line in resp.aiter_lines():
                            if line:
                                yield f"data: {line}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=ollama_payload)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=f"Ollama error: {resp.text}")
            data = resp.json()
            return {
                "model": data.get("model", model_name),
                "created_at": data.get("created_at"),
                "message": data.get("message", {}),
                "done": data.get("done", True),
                "total_duration": data.get("total_duration"),
                "eval_count": data.get("eval_count"),
            }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/generate", summary="Text Completion with Qwen", tags=["Inference"])
async def generate(request: GenerateRequest):
    model_name = request.model or DEFAULT_MODEL
    runtime_options = dict(request.options) if request.options else {}
    if FORCE_GPU and "num_gpu" not in runtime_options:
        runtime_options["num_gpu"] = 99
    if request.temperature is not None:
        runtime_options["temperature"] = request.temperature

    ollama_payload = {
        "model": model_name,
        "prompt": request.prompt,
        "stream": request.stream,
        "options": runtime_options,
    }
    if request.system:
        ollama_payload["system"] = request.system

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=ollama_payload)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=f"Ollama error: {resp.text}")
            data = resp.json()
            return {
                "model": data.get("model", model_name),
                "created_at": data.get("created_at"),
                "response": data.get("response", ""),
                "done": data.get("done", True),
            }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    print(f"Starting Local Service AI on http://{HOST}:{PORT}")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
